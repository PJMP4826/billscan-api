from dataclasses import dataclass


@dataclass
class UploadedImage:
    """Record — resultado de una operación save() en ImageRepository."""

    key: str
    url: str
    mime_type: str
