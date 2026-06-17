import puremagic
from fastapi import UploadFile, status, BackgroundTasks
from fastapi.responses import JSONResponse

from src.shared.errors.base_exception import BadRequestError
from src.bootstraps.use_cases_bootstrap import get_submit_receipt_use_case


class UploadReceiptController:
    def __init__(self) -> None:
        pass

    async def handle(
        self,
        files: list[UploadFile],
        groups: list[str] | None,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse:
        try:

            grouped_images = await self._group_and_validate(files, groups)

            use_case = get_submit_receipt_use_case(background_tasks=background_tasks)

            temp_user_id = "ac9890c6-194b-4b7e-9aa0-2caae7db6c17"

            await use_case.execute(user_id=temp_user_id, grouped_images=grouped_images)

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "status": 202,
                    "message": "Los tickets se están procesando",
                },
            )
        except BadRequestError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "title": "BAD REQUEST",
                    "status": 400,
                    "message": str(e),
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "title": "Internal Server Error",
                    "status": 500,
                    "message": str(e),
                },
            )

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
                raise BadRequestError("Solo se permiten imágenes JPG o PNG")

            return real_mime
        except puremagic.PureError:
            raise BadRequestError("Archivo no reconocido")
