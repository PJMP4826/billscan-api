from enum import Enum


class PersonType(str, Enum):
    FISICA = "FISICA"
    MORAL = "MORAL"

    @classmethod
    def from_rfc(cls, rfc: str) -> "PersonType":
        """RFC de 12 caracteres = moral, 13 = física."""
        normalized = rfc.strip()
        if len(normalized) == 12:
            return cls.MORAL
        if len(normalized) == 13:
            return cls.FISICA
        raise ValueError(
            f"RFC con longitud inválida ({len(normalized)}): {rfc!r}"
        )
