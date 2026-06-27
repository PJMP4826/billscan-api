from typing import Literal

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Form,
    Query,
)

from src.api.http.controllers.upload_receipt_controller import UploadReceiptController
from src.api.http.controllers.create_fiscal_info_controller import (
    CreateFiscalInfoController,
)
from src.api.http.controllers.get_deductible_expenses_summary_controller import (
    GetDeductibleExpensesSummaryController,
)
from src.api.http.controllers.get_issued_cfdi_summary_controller import (
    GetIssuedCFDISummaryController,
)
from src.api.http.controllers.get_recent_activity_controller import (
    GetRecentActivityController,
)
from src.api.http.controllers.get_receipt_detail_controller import (
    GetReceiptDetailController,
)
from src.api.http.controllers.get_fiscal_info_controller import (
    GetUserFiscalInfoController,
)
from src.api.http.requests.fiscal_info_request import CreateFiscalInfoRequest
from src.api.http.requests.get_recent_activity_request import GetRecentActivityRequest
from src.api.http.requests.get_receipt_detail_request import GetReceiptDetailRequest

router = APIRouter(prefix="/api")

receipt_controller = UploadReceiptController()
fiscal_info_controller = CreateFiscalInfoController()
deductible_expenses_controller = GetDeductibleExpensesSummaryController()
issued_cfdi_controller = GetIssuedCFDISummaryController()
recent_activity_controller = GetRecentActivityController()
receipt_detail_controller = GetReceiptDetailController()
get_fiscal_info_controller = GetUserFiscalInfoController()


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


@router.get("/receipts/{receipt_uuid}")
async def get_receipt_detail(
    receipt_uuid: str,
    detail_level: Literal["base", "full"] = Query(default="base"),
):
    """Returns the detail (base or full) of a receipt including items, taxes and payments."""
    return await receipt_detail_controller.handle(
        request=GetReceiptDetailRequest(
            receipt_uuid=receipt_uuid, detail_level=detail_level
        )
    )


@router.post("/fiscal-info")
async def create_fiscal_info(payload: CreateFiscalInfoRequest):
    """Registers the fiscal info and tax regime of the user."""
    return await fiscal_info_controller.handle(request_data=payload)

@router.get("/fiscal-info")
async def get_fiscal_info():
    return await get_fiscal_info_controller.handle()


@router.get("/reporting/deductible-expenses")
async def get_deductible_expenses_summary():
    """Returns total amount and count of billable pending receipts."""
    return await deductible_expenses_controller.handle()


@router.get("/reporting/issued-cfdis")
async def get_issued_cfdi_summary():
    """Returns total amount and count of issued CFDIs."""
    return await issued_cfdi_controller.handle()


@router.get("/reporting/recent-activity")
async def get_recent_activity(
    receipt_uuid: str | None = Query(default=None),
    status_filter: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Returns recent activity ordered by date DESC, with optional filters."""
    return await recent_activity_controller.handle(
        request_data=GetRecentActivityRequest(
            receipt_uuid=receipt_uuid,
            status_filter=status_filter,
            limit=limit,
        )
    )
