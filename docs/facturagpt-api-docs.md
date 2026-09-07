# FacturaGPT Partner API — Documentation

> **Base URL:** `https://api.facturagpt.com.mx`  
> All examples use the production environment.

FacturaGPT converts receipt images into valid Mexican electronic invoices (CFDI) — the XML + PDF files required by Mexico's tax authority (SAT). You send a receipt photo; FacturaGPT automates the entire invoicing workflow in the background.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Response Format](#3-response-format)
4. [Endpoints](#4-endpoints)
   - [POST /api/v1/get_factura](#post-apiv1get_factura)
   - [GET /api/v1/get_factura_status/{session_id}](#get-apiv1get_factura_statussession_id)
   - [GET /api/v1/get_factura_files/{session_id}](#get-apiv1get_factura_filessession_id)
   - [GET /api/v1/files/{session_id}/{file_type}](#get-apiv1filessession_idfile_type)
5. [Webhooks](#5-webhooks)
6. [Status Codes & Error Handling](#6-status-codes--error-handling)
7. [Best Practices](#7-best-practices)
8. [Quick Start Samples](#8-quick-start-samples)
9. [Reference Tables](#9-reference-tables)

---

## 1. Quick Start

### Step 1 — Create an API Key

1. Open the **Partner Dashboard**.
2. Go to the **API keys** tab.
3. Click **Create key**, copy it, and store it securely.

Your key format: `fgpt_live_xxxxxxxxxxxxxxxxxxxx`

> ⚠️ **Keys are shown only once at creation.** Store them in a secrets manager — never in source code.

---

### Step 2 — Submit Your First Invoice Request

Call `POST /api/v1/get_factura` with a ticket image and either billing information or a previously saved `customer_id`.

**Required fields:**

| Field | Required | Description |
|---|---|---|
| `external_id` | Yes | Your own unique ID for this expense (idempotency key) |
| `ticket_image` | Yes | Receipt photo, base64-encoded |
| `customer_id` | One of these | Previously saved partner customer |
| `user_info` | One of these | Billing details (name, RFC, email, postal code, tax regime) |
| `csf_pdf` | One of these | SAT fiscal registration PDF (CSF), base64-encoded |

> ⚠️ Send **either** `customer_id` **or** raw fiscal data (`user_info` / `csf_pdf`). **Never both.**

**Request broken into two mental blocks:**

**Block 1 — Ticket Info** *(travels with every request)*

| Field | Purpose |
|---|---|
| `ticket_image` | Receipt image to process |
| `external_id` | Your unique expense ID for idempotency and reconciliation |
| `payment_method` | SAT payment code (e.g., `28`) |
| `uso_cfdi` | SAT invoice-use code (e.g., `G03`) |

**Block 2 — User Info** *(identifies who receives the invoice)*

| Field | Purpose |
|---|---|
| `csf_pdf` | Upload the SAT CSF PDF if you already have it |
| `user_info` | Send billing details manually when you don't have the CSF |
| `save_customer` | Set `true` to save the billing profile and reuse it later |

> **Key Mexican fiscal terms:**  
> - **RFC** — Mexican tax ID assigned by SAT  
> - **Régimen fiscal** — Tax classification code (e.g., `612` for individual entrepreneurs)  
> - **Código postal (cp)** — The postal code registered with SAT (may differ from business address)

---

### Step 3 — Receive the Result via Webhook

FacturaGPT processes invoices **asynchronously**. The POST request returns immediately with `status: "processing"`. The invoice is generated in the background.

> ⚠️ **Webhooks are required.** Configure a webhook URL in the Dashboard (Webhooks tab) or per-request via the `webhook_url` field **before** submitting any invoice request.

**Invoice states:**

| State | Type | Meaning |
|---|---|---|
| `processing` | Non-terminal | Request accepted, automation running |
| `completed` | Terminal | Invoice generated successfully. **Chargeable.** |
| `failed` | Terminal | Processing failed. **Not chargeable.** |

> Processing can last from a few seconds to a few minutes depending on merchant portal availability.

---

## 2. Authentication

All requests require a Bearer API key in the `Authorization` header:

```http
Authorization: Bearer fgpt_live_your_api_key_here
Content-Type: application/json
```

Manage keys from the **API keys** tab in the Partner Dashboard. Keys can be revoked at any time.

---

## 3. Response Format

All API responses use a consistent envelope:

**Success:**
```json
{
  "ok": true,
  "data": { },
  "error": null,
  "meta": {
    "version": "2026-03",
    "session_id": "id_abc123",
    "timestamp": "2026-03-06T12:00:00Z"
  }
}
```

**Failure:**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Your account does not have sufficient credits.",
    "details": {
      "balance_mxn": 0,
      "required_mxn": 4.64
    }
  },
  "meta": {
    "version": "2026-03",
    "timestamp": "2026-03-06T12:00:00Z"
  }
}
```

**Key identifiers:**

| Identifier | Source | Use |
|---|---|---|
| `external_id` | You provide it | Your idempotency key — links FacturaGPT sessions back to your records |
| `session_id` | FacturaGPT assigns it | FacturaGPT's workflow ID — use it for status polling and file retrieval |

> Always store **both** `external_id` and `session_id` in your database after a successful submission.

---

## 4. Endpoints

### POST /api/v1/get_factura

Submit a receipt image to start invoice generation.

**Request body:**
```json
{
  "external_id": "expense_12345",
  "ticket_image": "<base64-encoded image>",
  "save_customer": true,
  "uso_cfdi": "G03",
  "payment_method": "28",
  "user_info": {
    "razon_social": "ACME SA DE CV",
    "rfc": "XAXX010101000",
    "email": "finance@acme.com",
    "regimen": "601",
    "cp": "11560",
    "address": "Optional full address"
  },
  "webhook_url": "https://your-server.com/webhooks/facturagpt",
  "test_mode": false
}
```

**Field rules:**

| Field | Notes |
|---|---|
| `external_id` | **Required.** Acts as idempotency key scoped to your partner account. |
| `ticket_image` | **Required.** Base64-encoded receipt image. |
| `save_customer` | Optional. When `true`, stores the user profile and returns a `customer_id`. |
| `uso_cfdi` | Optional. Defaults to `G03`. |
| `payment_method` | Optional. Uses OCR-detected value when available, otherwise `99`. |
| `user_info` / `csf_pdf` | Send one — not both. |
| `webhook_url` | Optional per-request override. Use Dashboard config for production. |
| `test_mode: true` | Runs full automation but **does not charge** your balance. |

> **Idempotency:** Sending the same `external_id` with the **same payload** returns the original session (200). Sending the same `external_id` with a **different payload** returns `409 EXTERNAL_ID_CONFLICT`.

---

**Success Response — 202 Accepted**

The request was accepted. OCR ran immediately. Invoice automation continues in the background.

```json
{
  "ok": true,
  "data": {
    "session_id": "id_abc123",
    "external_id": "expense_12345",
    "status": "processing",
    "ocr_result": {
      "merchant_name": "Starbucks",
      "merchant_rfc": "SCA9312224NA",
      "amount": "125.50",
      "net_amount": "108.19",
      "tax_amount": "17.31",
      "tax_rate": "0.16",
      "currency": "MXN",
      "date": "2026-03-06",
      "payment_method": "card",
      "ticket_readable": true
    }
  },
  "error": null,
  "meta": {
    "version": "2026-03",
    "session_id": "id_abc123",
    "timestamp": "2026-03-06T12:00:00Z"
  }
}
```

**Idempotent Replay — 200 OK**

```json
{
  "ok": true,
  "data": {
    "session_id": "id_abc123",
    "external_id": "expense_12345",
    "status": "processing",
    "ocr_result": {}
  },
  "error": null,
  "meta": {
    "version": "2026-03",
    "session_id": "id_abc123",
    "timestamp": "2026-03-06T12:01:00Z"
  }
}
```

---

### GET /api/v1/get_factura_status/{session_id}

Check the current status of a specific invoice session.

Use this to confirm a result, reconcile records, or cross-check a webhook event. This is a **supplementary** check — not a replacement for webhooks.

**Response — 200 OK:**
```json
{
  "ok": true,
  "data": {
    "session_id": "id_abc123",
    "status": "completed",
    "ocr": {
      "ticket": {
        "merchant_name": "Starbucks",
        "merchant_rfc": "SCA9312224NA",
        "total": 125.5,
        "date": "2026-03-06"
      }
    }
  },
  "error": null,
  "meta": {
    "version": "2026-03",
    "session_id": "id_abc123",
    "timestamp": "2026-03-06T12:02:00Z"
  }
}
```

---

### GET /api/v1/get_factura_files/{session_id}

Retrieve the generated invoice files (XML + PDF) once the session is `completed`.

> ⚠️ Returns `404 FILES_NOT_AVAILABLE` while the session is still processing. Always wait for `completed` status.

**Files not ready — 404:**
```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "FILES_NOT_AVAILABLE",
    "message": "Files are not available yet for this session.",
    "details": {
      "session_id": "id_abc123",
      "status": "processing",
      "hint": "Wait for completed status before requesting files."
    }
  },
  "meta": {
    "version": "2026-03",
    "session_id": "id_abc123",
    "timestamp": "2026-03-06T12:00:30Z"
  }
}
```

---

### GET /api/v1/files/{session_id}/{file_type}

Download an invoice file directly.

| Parameter | Values |
|---|---|
| `file_type` | `xml` or `pdf` |

This is a **white-label download proxy** — returns a short-lived signed redirect URL. Raw storage hostnames are never exposed to your clients.

---

## 5. Webhooks

Webhooks are the **recommended** (and required) way to receive invoice results.

### Setup

- Configure your webhook URL in the **Partner Dashboard → Webhooks tab**.
- You can send a test event to confirm delivery.
- For one-off overrides, include `webhook_url` directly in the request body.

> ⚠️ A webhook must be configured **before** calling `POST /api/v1/get_factura`. Missing webhook returns `400 WEBHOOK_REQUIRED`.

---

### Event Types

| Event | When it fires |
|---|---|
| `factura.completed` | Invoice generated and files ready |
| `factura.failed` | Processing failed after all retries |
| `batch.completed` | All items in a batch flow finished |

---

### factura.completed Payload

```json
{
  "event": "factura.completed",
  "version": "2026-03",
  "idempotency_key": "factura.completed:id_abc123:1741132800",
  "session_id": "id_abc123",
  "external_id": "expense_12345",
  "status": "completed",
  "completed_at": "2026-03-06T12:01:23Z",
  "processing_time_seconds": 34,
  "files": {
    "xml_url": "https://api.facturagpt.com.mx/api/v1/files/id_abc123/xml",
    "pdf_url": "https://api.facturagpt.com.mx/api/v1/files/id_abc123/pdf"
  },
  "cfdi_summary": {
    "folio_fiscal": "uuid-here",
    "emisor_rfc": "AAA010101AAA",
    "receptor_rfc": "XAXX010101000",
    "amount": "125.50",
    "net_amount": "108.19",
    "tax_amount": "17.31",
    "currency": "MXN",
    "fecha_timbrado": "2026-03-06T12:01:20Z"
  }
}
```

---

When a merchant generates the invoice but sends it directly by email, factura.completed is still terminal and chargeable, but the webhook has no files object:

```json
{
  "event": "factura.completed",
  "version": "2026-03",
  "idempotency_key": "factura.completed:id_abc123:1741132800",
  "session_id": "id_abc123",
  "external_id": "expense_12345",
  "status": "completed",
  "completed_at": "2026-03-06T12:01:23Z",
  "delivery": {
    "method": "merchant_email",
    "files_available": false,
    "email_recipient": "customer@example.com",
    "message": "La factura fue generada por el comercio y enviada directamente por email."
  }
}
```

### factura.failed Payload

```json
{
  "event": "factura.failed",
  "version": "2026-03",
  "idempotency_key": "factura.failed:id_abc123:1741132900",
  "session_id": "id_abc123",
  "external_id": "expense_12345",
  "status": "failed",
  "reason_code": "PORTAL_UNAVAILABLE",
  "reason_message": "The merchant portal was inaccessible after multiple attempts."
}
```

---

### Handling Webhooks Reliably

> FacturaGPT uses **at-least-once delivery**. Design your handler to be idempotent.

**The correct pattern:**

1. Receive the webhook request.
2. **Reply `200 OK` immediately** — just an acknowledgement.
3. Do the actual work (save to DB, send notifications, etc.) **in the background** after responding.

**Other reliability rules:**

- **De-duplicate events.** Use `idempotency_key` to detect and skip events you've already processed.
- **Store before processing.** Save the raw payload to your DB first. If downstream logic fails, you can replay from what you saved.
- **Expect retries.** The same event may arrive more than once. Your handler must be safe to run twice with the same data.

---

### Webhook Signature Verification

Every delivery includes a signature. **Verify it** to confirm the request genuinely came from FacturaGPT.

**Where to find your signing secret:**  
Partner Dashboard → Webhooks tab → click the eye icon → copy `whsec_...`

> Keep it private. If it's ever exposed, use **Rotate secret** and update your server immediately.

**Headers sent with every delivery:**

| Header | Purpose |
|---|---|
| `x-facturagpt-id` | Unique ID for this delivery attempt |
| `x-facturagpt-timestamp` | Unix timestamp of when the event was sent |
| `x-facturagpt-signature` | HMAC-SHA256 signature (`v1=...`) |

**Node.js verification:**
```js
import crypto from "node:crypto";

const secret = process.env.FGPT_WEBHOOK_SECRET; // whsec_...
const rawKey = Buffer.from(secret.replace("whsec_", ""), "base64");

function verifyWebhook(req) {
  const id        = req.headers["x-facturagpt-id"];
  const timestamp = req.headers["x-facturagpt-timestamp"];
  const signature = req.headers["x-facturagpt-signature"];

  const body = JSON.stringify(req.body);
  const msg  = Buffer.from(`${timestamp}.${body}`);
  const expected = "v1=" + crypto.createHmac("sha256", rawKey).update(msg).digest("hex");

  if (expected !== signature) throw new Error("Invalid webhook signature");
  return JSON.parse(body);
}
```

**Python verification:**
```python
import hmac, hashlib, base64, os, json

secret = os.environ["FGPT_WEBHOOK_SECRET"]  # whsec_...
raw_key = base64.b64decode(secret.replace("whsec_", "") + "==")

def verify_webhook(request):
    timestamp = request.headers.get("x-facturagpt-timestamp")
    signature = request.headers.get("x-facturagpt-signature")
    body = request.data.decode("utf-8")

    msg = f"{timestamp}.{body}".encode()
    expected = "v1=" + hmac.new(raw_key, msg, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature or ""):
        raise ValueError("Invalid webhook signature")

    return json.loads(body)
```

---

## 6. Status Codes & Error Handling

### HTTP Status Codes

| Code | When it happens |
|---|---|
| `202` | Request accepted, invoice processing started |
| `200` | Successful read, poll, or idempotent replay |
| `400` | Invalid payload, missing required field, or webhook not configured |
| `401` | API key missing, invalid, or revoked |
| `402` | Account has insufficient balance |
| `403` | Account suspended |
| `404` | Session not found, or files not ready yet |
| `409` | Same `external_id` sent with a different payload |
| `422` | Ticket image unreadable, RFC not found in SAT registry |
| `429` | Rate limit exceeded |
| `503` | Merchant portal or automation temporarily unavailable |

---

### Error Codes

| Code | HTTP | What to do |
|---|---|---|
| `INVALID_API_KEY` | 401 | Check your key is correct and active |
| `EXPIRED_API_KEY` | 401 | Key was revoked — create a new one in the Dashboard |
| `INVALID_REQUEST` | 400 | A required field is missing or malformed |
| `WEBHOOK_REQUIRED` | 400 | Set a webhook URL in the Dashboard or in the request body |
| `INSUFFICIENT_BALANCE` | 402 | Top up your balance in the Dashboard |
| `ACCOUNT_SUSPENDED` | 403 | Contact support |
| `SESSION_NOT_FOUND` | 404 | The `session_id` does not exist or belongs to another account |
| `EXTERNAL_ID_CONFLICT` | 409 | Same `external_id` with different data — use a new `external_id` |
| `INVALID_IMAGE_FORMAT` | 400 | Image is corrupt or in an unsupported format |
| `UNREADABLE_TICKET` | 422 | OCR could not extract data from the ticket image |
| `RFC_NOT_FOUND` | 422 | The RFC provided is not registered in the SAT registry |
| `PORTAL_UNAVAILABLE` | 503 | The merchant's SAT portal was unreachable — retry later |
| `AUTOMATION_UNAVAILABLE` | 503 | Temporary internal processing outage — retry later |
| `RATE_LIMIT_EXCEEDED` | 429 | Slow down requests and retry with backoff |
| `FILES_NOT_AVAILABLE` | 404 | Invoice files are not ready yet — wait for `completed` status |

---

## 7. Best Practices

- **Image quality matters.** Use images ≥ 1200×800 px. Good lighting, no glare, cropped to ticket edges.
- **Use a stable `external_id`.** Generate it from your source system (e.g., an expense record ID) to prevent accidental duplicates on retry.
- **Webhooks are required.** Use `GET .../get_factura_status/{session_id}` only to reconcile, not as the primary delivery mechanism.
- **Store both identifiers.** Save `session_id` (FacturaGPT's ID) and `external_id` (your ID) in the same DB record.
- **Treat processing as async.** Never assume a fixed resolution time. Design for delayed completion.

---

## 8. Quick Start Samples

### Node.js

```js
import fs from "node:fs";
import axios from "axios";

const ticketImage = fs.readFileSync("./receipt.jpg").toString("base64");

const response = await axios.post(
  "https://api.facturagpt.com.mx/api/v1/get_factura",
  {
    external_id: "expense_12345",
    ticket_image: ticketImage,
    user_info: {
      razon_social: "ACME SA DE CV",
      rfc: "XAXX010101000",
      email: "finance@acme.com",
      regimen: "601",
      cp: "11560"
    }
  },
  {
    headers: {
      Authorization: "Bearer fgpt_live_your_api_key_here",
      "Content-Type": "application/json"
    }
  }
);

const { session_id, status } = response.data.data;
console.log(`Session: ${session_id} — Status: ${status}`);
// status will be "processing" — wait for the webhook event.
```

### Python

```python
import base64, requests

with open("./receipt.jpg", "rb") as f:
    ticket_image = base64.b64encode(f.read()).decode("utf-8")

resp = requests.post(
    "https://api.facturagpt.com.mx/api/v1/get_factura",
    headers={
        "Authorization": "Bearer fgpt_live_your_api_key_here",
        "Content-Type": "application/json",
    },
    json={
        "external_id": "expense_12345",
        "ticket_image": ticket_image,
        "user_info": {
            "razon_social": "ACME SA DE CV",
            "rfc": "XAXX010101000",
            "email": "finance@acme.com",
            "regimen": "601",
            "cp": "11560"
        }
    },
    timeout=30
)

data = resp.json().get("data", {})
print(f"Session: {data.get('session_id')} — Status: {data.get('status')}")
# status will be "processing" — wait for the webhook event.
```

### Status Check (optional reconciliation)

```js
const result = await axios.get(
  `https://api.facturagpt.com.mx/api/v1/get_factura_status/${session_id}`,
  { headers: { Authorization: "Bearer fgpt_live_your_api_key_here" } }
);

console.log(result.data.data.status);
// "processing" | "completed" | "failed"
```

---

## 9. Reference Tables

### Request Fields with SAT Catalogs

| Field | Where to send it | Default behavior |
|---|---|---|
| `uso_cfdi` | Top-level request field | Defaults to `G03` |
| `payment_method` | Top-level request field | Uses OCR result when available, otherwise `99` |

---

### Payment Methods — SAT c_FormaPago

| Code | Description | Notes |
|---|---|---|
| `01` | Efectivo | Cash |
| `02` | Cheque nominativo | Nominative check |
| `03` | Transferencia electrónica de fondos | Wire / SPEI |
| `04` | Tarjeta de crédito | Credit card |
| `05` | Monedero electrónico | Electronic wallet |
| `06` | Dinero electrónico | Electronic money |
| `08` | Vales de despensa | Food vouchers |
| `12` | Dación en pago | Giving in payment |
| `13` | Pago por subrogación | Subrogation |
| `14` | Pago por consignación | Consignment |
| `15` | Condonación | Debt forgiveness |
| `17` | Compensación | Compensation |
| `23` | Novación | Novation |
| `24` | Confusión | Confusion |
| `25` | Remisión de deuda | Debt remission |
| `26` | Prescripción o caducidad | Prescription / expiration |
| `27` | A satisfacción del acreedor | Creditor satisfaction |
| `28` | Tarjeta de débito | Debit card |
| `29` | Tarjeta de servicios | Service card |
| `30` | Aplicación de anticipos | Advance application |
| `31` | Intermediario pagos | Intermediary payments |
| `99` | Por definir | **Default when not detected by OCR** |

---

### uso_cfdi Catalog — SAT c_UsoCFDI

> Recommended default for general business expenses: **`G03`**

| Code | Description |
|---|---|
| `G01` | Adquisición de mercancías |
| `G02` | Devoluciones, descuentos o bonificaciones |
| `G03` | Gastos en general |
| `I01` | Construcciones |
| `I02` | Mobiliario y equipo de oficina por inversiones |
| `I03` | Equipo de transporte |
| `I04` | Equipo de cómputo y accesorios |
| `I05` | Dados, troqueles, moldes, matrices y herramental |
| `I06` | Comunicaciones telefónicas |
| `I07` | Comunicaciones satelitales |
| `I08` | Otra maquinaria y equipo |
| `D01` | Honorarios médicos, dentales y gastos hospitalarios |
| `D02` | Gastos médicos por incapacidad o discapacidad |
| `D03` | Gastos funerales |
| `D04` | Donativos |
| `D05` | Intereses reales efectivamente pagados por créditos hipotecarios |
| `D06` | Aportaciones voluntarias al SAR |
| `D07` | Primas por seguros de gastos médicos |
| `D08` | Gastos de transportación escolar obligatoria |
| `D09` | Depósitos en cuentas para el ahorro / planes de pensiones |
| `D10` | Pagos por servicios educativos (colegiaturas) |
| `P01` | Por definir |
| `S01` | Sin efectos fiscales |
| `CP01` | Pagos |
| `CN01` | Nómina |
