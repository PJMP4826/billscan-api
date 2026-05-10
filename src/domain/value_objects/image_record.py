from typing import Any
from dataclasses import dataclass

@dataclass
class ImageRecord():
    image_bytes: bytes
    mime_type: Any
