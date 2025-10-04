import os
import time
import shlex
import subprocess
import requests
import json
import re
from typing import List, Optional, Dict, Any


def _extract_json(text: str) -> Optional[str]:
    """
    Try to extract a top-level JSON object or array from the model output.
    IMPROVED VERSION that handles markdown and finds complete objects.
    """
    if not text:
        return None
    
    # First, clean markdown code blocks
    cleaned_text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    cleaned_text = re.sub(r'\s*```\s*$', '', cleaned_text, flags=re.MULTILINE)
    cleaned_text = cleaned_text.strip()
    
    # Strategy 1: Try to parse the entire cleaned text
    try:
        json.loads(cleaned_text)
        return cleaned_text
    except Exception:
        pass
    
    # Strategy 2: Find complete JSON objects using brace counting
    brace_count = 0
    start_index = -1
    
    for i, char in enumerate(cleaned_text):
        if char == '{':
            if brace_count == 0:
                start_index = i  # Start of outermost object
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_index != -1:
                # Found complete object
                candidate = cleaned_text[start_index:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    # Continue searching
                    start_index = -1
    
    # Strategy 3: Original fallback logic
    arr_start = cleaned_text.find('[')
    arr_end = cleaned_text.rfind(']')
    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        candidate = cleaned_text[arr_start:arr_end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    obj_start = cleaned_text.find('{')
    obj_end = cleaned_text.rfind('}')
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        candidate = cleaned_text[obj_start:obj_end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    return None


class GemmaClient:
    def __init__(
        self,
        api_url: Optional[str] = None,
        port: int = None,
        completion_path: str = None,
        model_path: Optional[str] = None,
        start_cmd_template: Optional[str] = None,
        auto_start: bool = False,
        ping_path: str = "/",
        start_timeout: int = 30,
    ):
        # Config from env or parameters
        env_api = os.environ.get("GEMMA_API_URL")
        env_port = os.environ.get("GEMMA_API_PORT")
        env_comp = os.environ.get("GEMMA_COMPLETION_PATH")
        env_model = os.environ.get("GEMMA_MODEL_PATH")
        env_start = os.environ.get("GEMMA_START_CMD")
        env_auto = os.environ.get("GEMMA_AUTO_START")

        self.port = int(port or env_port or 8081)
        self.base_url = api_url or env_api or f"http://llm:{self.port}"
        self.completion_path = completion_path or env_comp or "/completion"
        self.completion_url = self.base_url.rstrip("/") + self.completion_path
        self.model_path = model_path or env_model or "backend/models/gemma-3n-E2B-it-UD-Q8_K_XL.gguf"
        self.start_cmd_template = start_cmd_template or env_start
        self.ping_path = ping_path
        self.start_timeout = start_timeout

        self._proc: Optional[subprocess.Popen] = None
        self.session = requests.Session()

        # defer async setup
        self._auto_start_requested = auto_start or (env_auto and env_auto.lower() in ("1", "true", "yes"))

        print(f"GemmaClient configured: base_url={self.base_url}, model='{self.model_path}'")

    async def init(self):
        """Perform async setup (ping or auto-start)."""
        if self._auto_start_requested:
            try:
                if not await self._ping_server():
                    started = await self.start_server(timeout=self.start_timeout)
                else:
                    started = True
            except Exception:
                started = False

            if not started:
                print("GemmaClient: auto-start requested but server is not reachable and start failed.")
        return self

    # ---------------------------
    # Server lifecycle / pinging
    # ---------------------------
    async def _ping_server(self, timeout: float = 2.0) -> bool:
        """Return True if the server responds to GET on / or /completion."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # try root
                r = await client.get(self.base_url.rstrip("/") + "/", timeout=timeout)
                if r.status_code in (200, 400, 404):  # accept common responses
                    return True
                # try completion
                r = await client.post(
                    self.completion_url,
                    json={"prompt": "ping", "n_predict": 1},
                    timeout=timeout
                )
                return r.status_code == 200
        except Exception:
            return False

    async def start_server(self, timeout: int = 30) -> bool:
        """
        Try to spawn a local server using the configured start_cmd_template.
        The start command MUST include placeholders {model} and {port} if they are used here.
        Example template:
          "/usr/local/bin/llama-server --model {model} --host 0.0.0.0 --port {port}"
        Returns True if server becomes ready within timeout seconds.
        """
        if not self.start_cmd_template:
            raise RuntimeError("No start_cmd_template provided. Set GEMMA_START_CMD or pass start_cmd_template.")

        if self._proc and self._proc.poll() is None:
            print("Server already running under process PID", self._proc.pid)
            return True

        cmd = self.start_cmd_template.format(model=self.model_path, port=self.port)
        args = shlex.split(cmd)

        try:
            # start detached process
            self._proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError as e:
            raise RuntimeError(f"Failed to start LLM server process: {e}")

        deadline = time.time() + timeout
        while time.time() < deadline:
            if await self._ping_server():
                print("LLM server is reachable.")
                return True
            time.sleep(0.5)

        # If we reach here, server didn't start in time. Capture stderr for debugging.
        try:
            if self._proc:
                out, err = self._proc.communicate(timeout=1)
                print("LLM server stderr:", err.decode(errors="ignore") if err else "<none>")
        except Exception:
            pass

        return False

    def stop_server(self):
        """Terminate the spawned server process if any."""
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            finally:
                self._proc = None
            return True
        return False

    # ---------------------------
    # Low-level generate wrapper
    # ---------------------------
    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512, stream: bool = False) -> str:
        """
        Send a generation request to the LLM server and return the generated text.
        This method tries to be tolerant to a few server response shapes:
          - {"content": "..."}
          - {"choices": [{"text": "..."}]}
          - {"result": "..."}
        """
        # Ensure server reachable
        if not await self._ping_server():
            raise RuntimeError("LLM server not reachable at " + self.base_url)

        payload = {
            "prompt": prompt,
            "temperature": float(temperature),
            "n_predict": int(max_tokens),
            "stream": bool(stream),
        }

        try:
            r = self.session.post(self.completion_url, json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Error calling LLM server: {e}")
        except ValueError:
            # non-json response
            return r.text

        # flexible parsing
        if isinstance(data, dict):
            if "content" in data:
                return data["content"]
            if "result" in data:
                # some servers use "result"
                return data["result"]
            if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                first = data["choices"][0]
                if isinstance(first, dict) and "text" in first:
                    return first["text"]
                # openai-like: choices[0].message.content
                if isinstance(first, dict) and "message" in first and isinstance(first["message"], dict):
                    if "content" in first["message"]:
                        return first["message"]["content"]
        # fallback: stringify
        try:
            return json.dumps(data)
        except Exception:
            return str(data)

    # ---------------------------
    # Higher-level helpers
    # ---------------------------
    async def generate_rag_response(self, query: str, context: List[str], max_tokens: int = 512) -> str:
        """
        Build a RAG-style prompt using `context` and ask the model to answer `query`.
        The function will instruct the LLM not to hallucinate and to only use the provided context.
        """
        context_str = "\n\n".join([f"---\n{c}\n---" for c in context])
        prompt = (
            "You are an expert study assistant. Use ONLY the provided context to answer the question. "
            "If the answer is not in the context, say you don't know and suggest how to find the answer.\n\n"
            f"CONTEXT:\n{context_str}\n\nQUESTION:\n{query}\n\nAnswer concisely with references to the pieces of context (if helpful)."
        )
        return await self.generate(prompt, temperature=0.0, max_tokens=max_tokens)

    async def generate_summary(self, text: str, summary_tokens: int = 200) -> str:
        """
        Ask the model to produce a concise summary and a short list of key points.
        """
        prompt = (
            "Summarize the following text into a short, clear summary, "
            "followed by 5 bullet-point key takeaways. Keep it factual.\n\n"
            f"TEXT:\n{text}\n\nSummary:\n"
        )
        return await self.generate(prompt, temperature=0.0, max_tokens=summary_tokens)

    async def choose_question_types(self, context: str, top_k: int = 3) -> List[str]:
        """
        Ask the LLM which question types fit best for this context.
        Returns a simple list of suggested types, e.g. ["mcq", "coding", "short_answer"].
        """
        prompt = (
            "You are designing practice questions for students. Given the following context, "
            "suggest the top question types that would best test understanding. Choose from: "
            "mcq, short_answer, coding, fill_in_the_blank, true_false. Return a JSON array of types.\n\n"
            f"Context:\n{context}\n\nReturn only a JSON array like [\"mcq\",\"short_answer\"]"
        )
        raw = await self.llm.generate(prompt, temperature=0.0, max_tokens=150)
        # try to parse JSON first
        js = _extract_json(raw)
        if js:
            try:
                return json.loads(js)
            except Exception:
                pass
        # fallback: parse lines and words
        candidates = re.findall(r"(mcq|short_answer|coding|fill_in_the_blank|true_false)", raw, flags=re.IGNORECASE)
        return [c.lower() for c in candidates][:top_k] if candidates else ["mcq"]

    async def generate_questions(
        self,
        context: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        allowed_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Ask model to generate a list of questions in strict JSON format.
        Each question will be an object like:
        {
          "type": "mcq" | "short_answer" | "coding" | "fill_in_the_blank" | "true_false",
          "question": "...",
          "options": ["A","B","C"]  # present only for mcq/true_false
          "answer": "..."           # canonical answer
          "explanation": "..."      # optional brief explanation
        }
        """
        if allowed_types is None:
            allowed_types = ["mcq", "short_answer", "coding", "fill_in_the_blank", "true_false"]

        allowed_str = ",".join(allowed_types)
        prompt = (
            "You are an exam-generator. Using the context below, generate exactly "
            f"{num_questions} questions appropriate for difficulty level '{difficulty}'. "
            f"Allowed types: {allowed_str}. Return a JSON array of question objects.\n\n"
            f"Context:\n{context}\n\nReturn only JSON (no commentary)."
        )

        raw = await self.llm.generate(prompt, temperature=0.2, max_tokens=1500)
        js = _extract_json(raw)
        if not js:
            # try to coax the model into JSON (retry with stricter instruction)
            retry_prompt = (
                "IMPORTANT: The previous output was not valid JSON. Please return only valid JSON array of question objects, nothing else.\n\n"
                f"Context:\n{context}\n\nNumber of questions: {num_questions}\n"
            )
            raw = await self.llm.generate(prompt, temperature=0.0, max_tokens=1500)
            js = _extract_json(raw)

        if not js:
            # last resort: return empty list and log raw output
            print("generate_questions: couldn't parse JSON. Raw output:\n", raw)
            return []

        try:
            return json.loads(js)
        except Exception as e:
            print("Failed to json.loads extracted JSON from model:", e)
            return []

    async def grade_written_answer(self, question: str, reference_answer: str, student_answer: str) -> Dict[str, Any]:
        """
        Ask the model to grade a student's written answer using the reference.
        Returns a dict with {score: float (0-100), feedback: str, rubrics: optional}
        """
        prompt = (
            "You are an objective grader. Grade the student's answer against the reference answer "
            "on a scale 0-100. Provide a numeric score and a short feedback paragraph explaining strengths and weaknesses.\n\n"
            f"QUESTION:\n{question}\n\nREFERENCE ANSWER:\n{reference_answer}\n\nSTUDENT ANSWER:\n{student_answer}\n\n"
            "Return JSON like: {\"score\": 85, \"feedback\": \"...\"}"
        )

        raw = await self.llm.generate(prompt, temperature=0.0, max_tokens=300)
        js = _extract_json(raw)
        if not js:
            # try to parse numbers and text heuristically
            # fallback: return a default structure
            print("grade_written_answer: non-JSON model output:", raw[:400])
            return {"score": None, "feedback": raw}

        try:
            return json.loads(js)
        except Exception as e:
            print("grade_written_answer JSON parse error:", e)
            return {"score": None, "feedback": raw}

    # ---------------------------
    # Utilities
    # ---------------------------
    async def create_quiz_from_context(self, context: str, num_questions: int = 10, difficulty: str = "medium") -> List[Dict[str, Any]]:
        """
        Convenience wrapper to create a quiz (questions + answers) from context.
        """
        # Ask the model for types first (prefer variety)
        types = self.choose_question_types(context, top_k=3)
        return await self.generate_questions(context=context, num_questions=num_questions, difficulty=difficulty, allowed_types=types)

