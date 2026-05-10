from abc import ABC
from typing import TypeVar

T = TypeVar("T")


class MultiModalLLMProviderPort(ABC):
    @property
    def get_multi_modal_llm_model(self) -> object:
        raise NotImplementedError
