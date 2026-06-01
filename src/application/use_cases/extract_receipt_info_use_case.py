import puremagic
from fastapi import UploadFile

from src.domain.entities.receipt import Receipt
from src.shared.errors.base_exception import BadRequestError
from src.domain.ports.receipt_extractor import ReceiptExtractorPort
from src.infrastructure.agents.ticket_extractor_agent.prompts.ticket_extractor_prompts import (
    TICKET_EXTRACTOR_AGENT,
)


class ExtractReceiptInfoUseCase:
    def __init__(self, extractor: ReceiptExtractorPort) -> None:
        self.extractor = extractor

    async def execute(self, files: list[UploadFile]) -> list[Receipt]:
        content_bytes: list[bytes] = []

        receipts: list[Receipt] = []

        for file in files:
            await self._validate_and_process(file=file)
            content_bytes.append(await file.read())

        if content_bytes:
            result = await self.extractor.extract(
                images_bytes=content_bytes, prompt_template_str=TICKET_EXTRACTOR_AGENT
            )
            receipts.extend(result)

        return receipts

    async def _validate_and_process(self, file: UploadFile):
        # 1. Leer los primeros bytes para identificar el archivo real
        head = await file.read(2048)
        await file.seek(0)  # Resetear puntero para no romper lecturas posteriores

        # 2. Detectar el MIME type real basándose en el contenido, no en el nombre
        try:
            real_mime = str(puremagic.from_string(head, mime=True))  # type: ignore
        except puremagic.PureError:
            raise BadRequestError("Archivo no reconocido")

        # 3. Validar contra tus formatos permitidos
        if real_mime not in ["image/jpeg", "image/png", "image/jpg"]:
            raise BadRequestError("Solo se permiten imágenes JPG o PNG")
