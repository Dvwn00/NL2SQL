# Path: src/nl2sql/hf_engine.py
# This module defines the HuggingFace-based engine for generating SQL queries from natural language questions.
import os
from huggingface_hub import InferenceClient
from langchain_core.language_models.llms import LLM
from typing import Any, List, Optional

# Default Model
# DEFAULT_MODEL_ID = "defog/llama-3-sqlcoder-8b:featherless-ai"
DEFAULT_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct:featherless-ai"

# Custom LangChain wrapper for HuggingFace Inference API
class HFChatWrapper(LLM):
    """
    Custom LLM wrapper for HuggingFace Inference API to maintain compatibility with LangChain's LLM interface.
    """
    client: Any
    model_id: str

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        completion = self.client.chat.completions.create(
            model = self.model_id,
            messages = [
                {"role": "user", "content": prompt}
            ],
            temperature = 0.0,
            max_tokens = 512
        )
        return completion.choices[0].message.content
    
    @property
    def _llm_type(self) -> str:
        return "huggingface_inference_client"
    
# Initialize the HuggingFace endpoint using the InferenceClient
def get_llm(model_id: str = DEFAULT_MODEL_ID):
    """
    Initializes the HuggingFace InferenceClient and returns an LLM instance for generating SQL queries.
    """
    # Load HuggingFace API token from environment variable
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HuggingFace API token not found!")
    
    print(f"Initializing HuggingFace InferenceClient with model: {model_id}")

    # Initialize the HuggingFace InferenceClient
    client = InferenceClient(api_key=hf_token)
    llm = HFChatWrapper(client=client, model_id=model_id)

    return llm