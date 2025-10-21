from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL_URL = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v0.6-GGUF/resolve/main/TinyLlama-1.1B-Chat-v0.6.Q2_K.gguf?download=true"
DEFAULT_MODEL_PATH = Path("models") / "tinyllama-q2k.gguf"


class TinyLLM:
    def __init__(self):
        self.model = None
        self._ensure_model()
        if self.model_path.exists():
            try:
                from llama_cpp import Llama  # type: ignore

                self.model = Llama(model_path=str(self.model_path), n_ctx=2048, logits_all=False)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("llama_cpp unavailable or failed to load: %s", exc)
                self.model = None

    @property
    def model_path(self) -> Path:
        return DEFAULT_MODEL_PATH

    def _ensure_model(self) -> None:
        if self.model_path.exists():
            return
        if os.getenv("DOWNLOAD_TINY_LLM", "0") != "1":
            LOGGER.info("Tiny LLM model not found and auto-download disabled; using rule-based text.")
            return
        try:
            import requests

            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            LOGGER.info("Downloading tiny LLM model to %s", self.model_path)
            resp = requests.get(DEFAULT_MODEL_URL, timeout=120)
            resp.raise_for_status()
            self.model_path.write_bytes(resp.content)
        except Exception as exc:
            LOGGER.warning("Failed to download tiny LLM model: %s", exc)

    def generate(self, prompt: str) -> Optional[str]:
        if not self.model:
            return None
        try:
            completion = self.model.create_completion(prompt=prompt, max_tokens=256, temperature=0.7)
            text = completion["choices"][0]["text"].strip()
            return text
        except Exception as exc:
            LOGGER.warning("Tiny LLM generation failed: %s", exc)
            return None


def run_prompt(prompt: str) -> Optional[str]:
    llm = TinyLLM()
    return llm.generate(prompt)
