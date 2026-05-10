from abc import ABC, abstractmethod
from src.domain.entities.receipt import Receipt


class ReceiptExtractorPort(ABC):
    @abstractmethod
    def extract_from_url(self, image_url: str) -> Receipt:
        raise NotImplementedError
