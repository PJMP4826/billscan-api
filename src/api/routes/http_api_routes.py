from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form

from src.api.http.controllers.upload_receipt_controller import UploadReceiptController
from src.api.http.controllers.create_fiscal_info_controller import (
    CreateFiscalInfoController,
)
from src.api.http.requests.fiscal_info_request import CreateFiscalInfoRequest

router = APIRouter(prefix="/api")

file_controller = UploadReceiptController()
fiscal_info_controller = (
    CreateFiscalInfoController()
)


@router.post("/uploads/files")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    return await file_controller.handle(
        [file], groups=None, background_tasks=background_tasks
    )


@router.post("/uploads/multiples/files")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] | None = File(default=None),
    files_brackets: list[UploadFile] | None = File(default=None, alias="files[]"),
    groups: list[str] | None = Form(default=None, alias="groups[]"),
):
    all_files = (files or []) + (files_brackets or [])

    if not all_files:
        raise HTTPException(status_code=400, detail="Debes enviar al menos un archivo")

    return await file_controller.handle(all_files, groups, background_tasks)


@router.post("/fiscal-info")
async def create_fiscal_info(payload: CreateFiscalInfoRequest):
    """Registra la información fiscal y el régimen fiscal del usuario."""
    return await fiscal_info_controller.handle(request_data=payload)
