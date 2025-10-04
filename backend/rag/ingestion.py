import os
import re
from typing import List, Optional, Dict, Any, Tuple

from rag.weaviate_client import WeaviateClientWrapper
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
from tqdm import tqdm  # optional, useful for CLI progress

load_dotenv()


class DocumentIngestor:
    """
    Ingest files into a Weaviate collection.

    Usage:
      ingestor = DocumentIngestor(data_dir="uploads")
      res = ingestor.ingest(collection_name="finance_101", file_paths=["/tmp/lecture1.pdf"])
      # res contains inserted_text_chunks and combined_text for LLM use

    The class is collection-agnostic; collection_name is passed to `ingest`.
    """

    SUPPORTED_TEXT_EXT = {".txt", ".md", ".pdf"}
    SUPPORTED_IMAGE_EXT = {".png", ".jpg", ".jpeg"}
    SUPPORTED_AUDIO_EXT = {".mp3", ".wav", ".flac"}

    def __init__(self, data_dir: str = "data", weaviate_client: Optional[WeaviateClientWrapper] = None):
        self.data_dir = data_dir
        self.weaviate_client = weaviate_client or WeaviateClientWrapper()

    # def _slugify_collection(self, name: str) -> str:
    #     s = (name or "").strip()
    #     # replace non-alnum with _
    #     s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    #     if not s:
    #         s = "Collection"
    #     # enforce max length
    #     s = s[:63]
    #     # must start with uppercase
    #     if not s[0].isalpha() or not s[0].isupper():
    #         s = "C" + s
    #     return s


    def _slugify_collection(self, name: str) -> str:
        # Remove non-alphanumeric characters
        cleaned = re.sub(r'[^0-9a-zA-Z]+', ' ', name)
        # Split into words and capitalize
        parts = cleaned.strip().split()
        if not parts:
            raise ValueError("Collection name cannot be empty after slugify")
        # Join into PascalCase
        pascal = ''.join(p.capitalize() for p in parts)
        return pascal

    def _gather_files(self, file_paths: Optional[List[str]]) -> List[str]:
        if file_paths:
            if isinstance(file_paths, str):
                file_paths = [file_paths]
            return [p for p in file_paths if os.path.exists(p)]
        # fallback: scan data_dir
        if not os.path.exists(self.data_dir):
            return []
        all_files = [os.path.join(self.data_dir, f) for f in os.listdir(self.data_dir)]
        return [p for p in all_files if os.path.isfile(p)]

    async def ingest(
        self,
        collection_name: str,
        file_paths: Optional[List[str]] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 20,
    ) -> Dict[str, Any]:
        """
        Ingest the supplied files into Weaviate under `collection_name`.
        Returns a dict:
          {
            "collection": <collection_name>,
            "inserted_text_chunks": [ ... ],
            "inserted_media": [ ... ],
            "combined_text": "..."   # concatenated for LLM use (first N chunks)
          }
        """
        if not collection_name:
            raise ValueError("collection_name is required")

        slug_name = self._slugify_collection(collection_name)
        if not self.weaviate_client.client:
            raise RuntimeError("Weaviate client not available")

        # ensure collection/schema exists
        self.weaviate_client.create_collection_if_not_exists(slug_name)

        files = self._gather_files(file_paths)
        if not files:
            return {"collection": slug_name, "inserted_text_chunks": [], "inserted_media": [], "combined_text": ""}

        text_files = []
        media_files = []
        for p in files:
            ext = os.path.splitext(p)[1].lower()
            if ext in self.SUPPORTED_TEXT_EXT:
                text_files.append(p)
            elif ext in self.SUPPORTED_IMAGE_EXT or ext in self.SUPPORTED_AUDIO_EXT:
                media_files.append(p)

        inserted_chunks = []
        # TEXT ingestion
        if text_files:
            try:
                reader = SimpleDirectoryReader(input_files=text_files)
                documents = reader.load_data()
            except Exception as e:
                # fallback: try to read files naively
                documents = []
                for p in text_files:
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                            documents.append(type("Doc", (), {"text": fh.read(), "metadata": {"file_path": p}})())
                    except Exception:
                        continue

            pipeline = IngestionPipeline(transformations=[SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)])
            try:
                nodes = pipeline.run(documents=documents)
            except Exception as e:
                # if pipeline.run fails, fall back to naive splitting
                nodes = []
                for doc in documents:
                    text = getattr(doc, "text", "") or ""
                    nodes.append(type("Node", (), {"text": text, "metadata": {"file_path": getattr(doc, "file_path", "unknown")}})())

            for node in tqdm(nodes, desc="Text chunks", disable=False):
                text = (node.text or "").strip()
                source = (node.metadata or {}).get("file_path", "unknown")
                if not text:
                    continue
                try:
                    self.weaviate_client.insert_text(slug_name, text, source)
                    inserted_chunks.append({"text": text, "source": source})
                except Exception as e:
                    # log and continue
                    print(f"Failed to insert text chunk: {e}")

        # MEDIA ingestion
        inserted_media = []
        for m in tqdm(media_files, desc="Media files", disable=False):
            ext = os.path.splitext(m)[1].lower()
            try:
                if ext in self.SUPPORTED_IMAGE_EXT:
                    self.weaviate_client.insert_image(slug_name, m, m)
                elif ext in self.SUPPORTED_AUDIO_EXT:
                    self.weaviate_client.insert_audio(slug_name, m, m)
                inserted_media.append(m)
            except Exception as e:
                print(f"Failed to insert media {m}: {e}")

        # combine first N chunks for LLM context (don't send everything)
        combined_text = "\n\n".join([c["text"] for c in inserted_chunks[:20]])

        return {
            "collection": slug_name,
            "inserted_text_chunks": inserted_chunks,
            "inserted_media": inserted_media,
            "combined_text": combined_text,
        }


# Example
if __name__ == "__main__":
    ing = DocumentIngestor(data_dir="uploads")
    print(ing.ingest(collection_name="Finance 101"))
