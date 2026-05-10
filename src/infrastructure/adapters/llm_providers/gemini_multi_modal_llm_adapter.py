from src.domain.ports.llm_provider_port import MultiModalLLMProviderPort
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms.llm import LLM


class GeminiMultiModalAdapter(MultiModalLLMProviderPort):
    def __init__(self, llm_model_name: str, api_key: str) -> None:
        self._llm = GoogleGenAI(model=llm_model_name, api_key=api_key)

    @property
    def get_multi_modal_llm_model(self) -> LLM:
        return self._llm
