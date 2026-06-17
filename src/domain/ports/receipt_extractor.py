from abc import ABC, abstractmethod
from src.domain.entities.receipt import Receipt


class ReceiptExtractorPort(ABC):
    @abstractmethod
    async def extract(
        self, grouped_images_bytes: list[list[bytes]], prompt_template_str: str
    ) -> list[Receipt]:
        raise NotImplementedError
