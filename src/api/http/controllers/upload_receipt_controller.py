from decimal import Decimal
from typing import Any

from fastapi import UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.shared.errors.base_exception import BadRequestError
from src.bootstraps.use_cases_bootstrap import get_extract_receipt_info_use_case


class UploadReceiptController:
    def __init__(self) -> None:
        self.extractor_use_case = get_extract_receipt_info_use_case()

    async def handle(self, files: list[UploadFile]) -> JSONResponse:
        try:

            result = await self.extractor_use_case.execute(files=files)

            receipts = [r.to_dict() for r in result]
            payload: dict[str, Any] = {
                "status": 201,
                "result": receipts,
            }
            safe_payload = jsonable_encoder(payload, custom_encoder={Decimal: str})

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=safe_payload,
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
