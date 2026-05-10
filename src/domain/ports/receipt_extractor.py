from abc import ABC, abstractmethod
from src.domain.entities.receipt import Receipt


class ReceiptExtractorPort(ABC):
    @abstractmethod
    async def extract_from_url(self, images_url: list[str], prompt_template_str: str) -> list[Receipt]:
        raise NotImplementedError
