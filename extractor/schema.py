from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Party(BaseModel):
    name: str
    address: str | None = None
    tax_id: str | None = None


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    tax_rate: float | None = None
    amount: float


class ExtractedDocument(BaseModel):
    document_type: Literal["invoice", "receipt"]

    document_id: str | None = None

    vendor: Party

    customer: Party | None = None

    invoice_date: date | None = None

    due_date: date | None = None

    currency: str

    line_items: list[LineItem] = Field(default_factory=list)

    subtotal: float | None = None

    tax_amount: float | None = None

    discount: float | None = None

    total: float

    payment_status: str | None = None