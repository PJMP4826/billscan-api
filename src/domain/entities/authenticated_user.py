from dataclasses import dataclass

from src.domain.value_objects.user_id import UserId


@dataclass(eq=False)
class AuthenticatedUser:
    """Entidad que representa al usuario autenticado de una petición.

    Es una entidad y no un value object porque tiene **identidad propia**
    (`user_id`, el `sub` que emite Clerk): dos instancias con el mismo
    `user_id` son el mismo usuario aunque sus atributos cambien (por ejemplo,
    el `email` al actualizarlo en Clerk). La igualdad y el hash se definen
    únicamente por la identidad.
    """

    user_id: UserId
    email: str

    def __post_init__(self) -> None:
        if not self.email or not self.email.strip():
            raise ValueError("El email del usuario autenticado no puede estar vacío")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AuthenticatedUser):
            return NotImplemented
        return self.user_id == other.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)
