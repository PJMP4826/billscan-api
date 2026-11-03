from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("UserId vacío")