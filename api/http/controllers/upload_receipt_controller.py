import json
import puremagic
from fastapi import UploadFile, status, BackgroundTasks
from fastapi.responses import JSONResponse

from src.domain.enums.invoice_use import InvoiceUse
from src.domain.enums.tax_regime import TaxRegime
from src.domain.errors.file_upload_error import (
    InvalidFileTypeError,
    UnrecognizedFileError,
)
from src.domain.value_objects.user_id import UserId
from src.bootstraps.use_cases_bootstrap import get_submit_receipt_use_case


class UploadReceiptController:
    def __init__(self) -> None:
        pass

    async def handle(
        self,
        user_id: UserId,
        files: list[UploadFile],
        groups_raw: str | None,
        background_tasks: BackgroundTasks,
        auto_billing: bool = False,
        uso_cfdi: InvoiceUse | None = None,
        regimen: TaxRegime | None = None,
    ) -> JSONResponse:

        groups = self._deserialize_group(groups_raw=groups_raw)
        grouped_images = await self._group_and_validate(files, groups)

        use_case = get_submit_receipt_use_case(background_tasks=background_tasks)

        await use_case.execute(
            user_id=user_id,
            grouped_images=grouped_images,
            auto_billing=auto_billing,
            uso_cfdi=uso_cfdi,
            regimen=regimen,
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": 202,
                "message": "Los tickets se están procesando",
            },
        )

    def _deserialize_group(self, groups_raw: str | None) -> list[str] | None:
        groups: list[str] | None = None
        if groups_raw:
            try:
                raw_list: list[str] = json.loads(
                    groups_raw
                )  # Convierte '["1", "2"]' -> ["1", "2"]

                if not isinstance(raw_list, list):  # type: ignore
                    raise ValueError("groups no es un array serializable")

                groups = [str(item) for item in raw_list]
            except (json.JSONDecodeError, ValueError):
                # Si el frontend envió un texto plano sin formato JSON (ej. "grupo1,grupo2")
                groups = [
                    item.strip() for item in groups_raw.split(",") if item.strip()
                ]
        return groups

    async def _group_and_validate(
        self, files: list[UploadFile], groups: list[str] | None
    ) -> dict[str, list[dict[str, bytes | str]]]:
        if not groups or len(groups) != len(files):
            # Fallback: si no llega 'groups[]' (o viene mal formado), cada
            # archivo se trata como su propio ticket. Mantiene compatibilidad
            # con clientes viejos que todavía no agrupan.
            groups = [str(i) for i in range(len(files))]

        grouped_files_content: dict[str, list[dict[str, bytes | str]]] = {}
        for file, group_key in zip(files, groups):
            mime_type = await self._validate(file)
            content = await file.read()

            # Group files by group_key, storing mime_type and file content
            if group_key not in grouped_files_content:
                grouped_files_content[group_key] = []
            grouped_files_content[group_key].append(
                {"mime": mime_type, "file": content}
            )

        return grouped_files_content

    async def _validate(self, file: UploadFile) -> str:
        head = await file.read(2048)
        await file.seek(0)

        try:
            real_mime = str(puremagic.from_string(head, mime=True))  # type: ignore

            if real_mime not in ["image/jpeg", "image/png", "image/jpg"]:
                raise InvalidFileTypeError("Solo se permiten imágenes JPG o PNG")

            return real_mime
        except puremagic.PureError as exc:
            raise UnrecognizedFileError("Archivo no reconocido") from exc
