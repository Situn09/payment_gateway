from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WebhookPayload(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str

class TransactionOut(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
