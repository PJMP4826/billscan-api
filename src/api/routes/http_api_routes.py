from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form

from src.api.http.controllers.upload_receipt_controller import UploadReceiptController
from src.api.http.controllers.create_fiscal_info_controller import (
    CreateFiscalInfoController,
)
from src.api.http.requests.fiscal_info_request import CreateFiscalInfoRequest

router = APIRouter(prefix="/api")

receipt_controller = UploadReceiptController()
fiscal_info_controller = CreateFiscalInfoController()


@router.post("/receipts")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] | None = File(default=None, alias="files[]"),
    groups: str | None = Form(default=None, alias="groups[]"),
    auto_billing: bool = Form(default=False),
):

    if not files:
        raise HTTPException(status_code=400, detail="Debes enviar al menos un archivo")

    return await receipt_controller.handle(
        files, groups, background_tasks, auto_billing
    )


@router.post("/fiscal-info")
async def create_fiscal_info(payload: CreateFiscalInfoRequest):
    """Registra la información fiscal y el régimen fiscal del usuario."""
    return await fiscal_info_controller.handle(request_data=payload)
