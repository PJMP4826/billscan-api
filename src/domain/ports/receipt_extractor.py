from abc import ABC, abstractmethod
from src.domain.entities.receipt import Receipt


class ReceiptExtractorPort(ABC):
    @abstractmethod
    async def extract(
        self, image_pages: list[bytes], prompt_template_str: str
    ) -> Receipt:
        raise NotImplementedError
