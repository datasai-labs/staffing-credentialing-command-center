from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthcheckResponse(BaseModel):
    status: Literal["ok"] = "ok"


class DatabricksHealthResponse(BaseModel):
    configured: bool
    can_connect: bool
    message: Optional[str] = None

    server_hostname_set: bool
    http_path_set: bool
    access_token_set: bool

    catalog: str
    schema_gold: str

    use_mock_data: bool


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=500)


class ErrorResponse(BaseModel):
    message: str
    request_id: Optional[str] = None


class SortSpec(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


def parse_date(value: str) -> date:
    # YYYY-MM-DD
    return date.fromisoformat(value)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)

