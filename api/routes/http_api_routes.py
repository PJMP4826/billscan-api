from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Form,
    Query,
)
from pydantic import EmailStr

from api.http.requests.fiscal_info_request import CreateFiscalInfoRequest
from src.domain.enums.invoice_use import InvoiceUse

router = APIRouter(prefix="/api")


@router.post("/receipts")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] | None = File(default=None, alias="files[]"),
    groups: str | None = Form(default=None, alias="groups[]"),
    auto_billing: bool = Form(default=False),
):
    from api.http.controllers.upload_receipt_controller import UploadReceiptController

    if not files:
        raise HTTPException(status_code=400, detail="Debes enviar al menos un archivo")

    receipt_controller = UploadReceiptController()
    return await receipt_controller.handle(
        files, groups, background_tasks, auto_billing
    )


@router.get("/receipts")
async def get_receipt_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Returns a paginated list of receipts with merchant, total, and billing status."""
    from api.http.controllers.get_receipt_list_controller import (
        GetReceiptListController,
    )

    receipt_list_controller = GetReceiptListController()
    return await receipt_list_controller.handle(page, page_size)


@router.get("/cfdis")
async def get_cfdi_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
):
    """Returns a paginated list of the CFDIs issued for the user."""
    from api.http.controllers.get_cfdi_list_controller import (
        GetCfdiListController,
    )

    cfdi_list_controller = GetCfdiListController()
    return await cfdi_list_controller.handle(page, page_size)


@router.get("/cfdis/{receipt_uuid}")
async def get_cfdi_detail(receipt_uuid: str):
    """Returns the full CFDI content (snake_case) plus presigned XML/PDF urls."""
    from api.http.controllers.get_cfdi_detail_controller import (
        GetCfdiDetailController,
    )
    from api.http.requests.get_cfdi_detail_request import GetCfdiDetailRequest

    cfdi_detail_controller = GetCfdiDetailController()
    return await cfdi_detail_controller.handle(
        request=GetCfdiDetailRequest(receipt_uuid=receipt_uuid)
    )


@router.get("/receipts/{receipt_uuid}")
async def get_receipt_detail(receipt_uuid: str):
    """Returns the full Receipt aggregate as JSON, including a presigned image url."""
    from api.http.controllers.get_receipt_detail_controller import (
        GetReceiptDetailController,
    )
    from api.http.requests.get_receipt_detail_request import GetReceiptDetailRequest

    receipt_detail_controller = GetReceiptDetailController()
    return await receipt_detail_controller.handle(
        request=GetReceiptDetailRequest(receipt_uuid=receipt_uuid)
    )


@router.post("/fiscal-info")
async def create_fiscal_info(payload: CreateFiscalInfoRequest):
    """Registers the fiscal info and tax regime of the user."""
    from api.http.controllers.create_fiscal_info_controller import (
        CreateFiscalInfoController,
    )

    fiscal_info_controller = CreateFiscalInfoController()
    return await fiscal_info_controller.handle(request_data=payload)


@router.post("/fiscal-info/csf")
async def create_fiscal_info_from_csf(
    file: UploadFile = File(..., alias="file"),
    email: EmailStr = Form(..., description="Email de contacto fiscal"),
    use_cfdi_code_default: InvoiceUse = Form(
        ..., description="Código de uso de CFDI por defecto (ej. 'G03')"
    ),
):
    """Registers the fiscal info extracted from a CSF (PDF, JPG or PNG)."""
    from api.http.controllers.create_fiscal_info_from_csf_controller import (
        CreateFiscalInfoFromCsfController,
    )
    from api.http.requests.fiscal_info_from_csf_request import (
        CreateFiscalInfoFromCsfRequest,
    )

    fiscal_info_controller = CreateFiscalInfoFromCsfController()
    return await fiscal_info_controller.handle(
        file=file,
        request_data=CreateFiscalInfoFromCsfRequest(
            email=email,
            use_cfdi_code_default=use_cfdi_code_default,
        ),
    )


@router.get("/fiscal-info")
async def get_fiscal_info():
    from api.http.controllers.get_fiscal_info_controller import (
        GetUserFiscalInfoController,
    )

    get_fiscal_info_controller = GetUserFiscalInfoController()
    return await get_fiscal_info_controller.handle()


@router.get("/reporting/receipts/count")
async def get_receipt_count_summary():
    """Returns total, billable, and non-billable receipt counts."""
    from api.http.controllers.get_receipt_count_summary_controller import (
        GetReceiptCountSummaryController,
    )

    receipt_count_controller = GetReceiptCountSummaryController()
    return await receipt_count_controller.handle()


@router.get("/reporting/completed-billing")
async def get_completed_billing_summary(
    period: str = Query(default="month", description="month, year, 3years, 5years"),
):
    """Returns total amount and count of completed billings for the given period."""
    from api.http.controllers.get_completed_billing_summary_controller import (
        GetCompletedBillingSummaryController,
    )

    completed_billing_controller = GetCompletedBillingSummaryController()
    return await completed_billing_controller.handle(period)


@router.get("/reporting/recent-activity")
async def get_recent_activity(
    receipt_uuid: str | None = Query(default=None),
    status_filter: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
):
    """Returns recent activity ordered by date DESC, with optional filters."""
    from api.http.controllers.get_recent_activity_controller import (
        GetRecentActivityController,
    )
    from api.http.requests.get_recent_activity_request import (
        GetRecentActivityRequest,
    )

    recent_activity_controller = GetRecentActivityController()
    return await recent_activity_controller.handle(
        request_data=GetRecentActivityRequest(
            receipt_uuid=receipt_uuid,
            status_filter=status_filter,
            limit=limit,
        )
    )
