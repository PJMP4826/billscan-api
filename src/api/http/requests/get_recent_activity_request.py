from pydantic import BaseModel, Field


class GetRecentActivityRequest(BaseModel):
    receipt_uuid: str | None = Field(default=None)
    status_filter: str | None = Field(default=None)
    limit: int = Field(default=10, ge=1, le=100)