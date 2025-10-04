import torch
from transformers import AutoTokenizer, AutoModel
from PIL import Image
from torchvision import transforms
import timm

class EmbeddingService:
    """
    Handles text and image embeddings for RAG.
    Uses local Hugging Face models (no external API).
    """

    def __init__(self, device: str = None):
        # Pick device automatically (GPU if available)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load text embedding model
        self.text_tokenizer = AutoTokenizer.from_pretrained("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
        self.text_model = AutoModel.from_pretrained("nomic-ai/nomic-embed-text-v1", trust_remote_code=True).to(self.device)

        # Load image embedding model (CLIP / SigLIP backbone via timm)
        self.image_model = timm.create_model("vit_base_patch16_clip_224", pretrained=True)
        self.image_model.eval().to(self.device)

        # Standard preprocessing for CLIP
        self.image_preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.48145466, 0.4578275, 0.40821073),
                                 std=(0.26862954, 0.26130258, 0.27577711)),
        ])

    def embed_text(self, text: str):
        """
        Generate embedding for a text string.
        """
        inputs = self.text_tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.text_model(**inputs)
            # Mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.cpu().numpy()[0]

    def embed_image(self, image_path: str):
        """
        Generate embedding for an image.
        """
        img = Image.open(image_path).convert("RGB")
        img_tensor = self.image_preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.image_model(img_tensor)
        return features.cpu().numpy()[0]


# --- Example usage ---
if __name__ == "__main__":
    embedder = EmbeddingService()

    # Text example
    text_vec = embedder.embed_text("Retrieval-Augmented Generation is powerful for question answering.")
    print("Text embedding vector shape:", text_vec.shape)

    # Image example
    # Make sure you have an image file locally for testing
    try:
        img_vec = embedder.embed_image("sample_image.jpg")
        print("Image embedding vector shape:", img_vec.shape)
    except FileNotFoundError:
        print("No sample_image.jpg found, skipping image test.")
