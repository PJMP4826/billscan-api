from fastapi import APIRouter, UploadFile, File, HTTPException

from src.api.http.controllers.upload_receipt_controller import UploadReceiptController


router = APIRouter(prefix="/api")

file_controller = UploadReceiptController()


@router.post("/uploads/files")
async def upload_file(file: UploadFile = File(...)):
    return await file_controller.handle([file])


@router.post("/uploads/multiples/files")
async def upload_files(
    files: list[UploadFile] | None = File(default=None),
    files_brackets: list[UploadFile] | None = File(default=None, alias="files[]"),
):
    all_files = (files or []) + (files_brackets or [])

    if not all_files:
        raise HTTPException(status_code=400, detail="Debes enviar al menos un archivo")

    return await file_controller.handle(all_files)
