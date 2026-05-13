from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

class TransactionBase(BaseModel):
    id: int
    user_id: int
    fecha_transaccion: date
    original_amount: Decimal
    final_amount: Decimal
    tipo_transaccion: str
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    descripcion_transaccion: Optional[str] = None
    transaction_source: Optional[str] = None
    created_at: Optional[datetime] = None

class TransactionGetAllResponseModel(BaseModel):
    total_transactions: int
    pagination_use: int
    transactions: List[TransactionBase]
