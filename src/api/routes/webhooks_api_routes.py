import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter()


@router.post("/webhooks/facturagpt")
async def webhooks_facturagpt(request: Request):
    body = await request.body()
    body_text = body.decode("utf-8", errors="replace")

    try:
        payload = json.loads(body_text)
        print("FacturaGPT body:\n", json.dumps(payload, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("FacturaGPT body:", body_text)

    return JSONResponse(
        status_code=200,
        content={
            "mes": "pong"
        }
    )


