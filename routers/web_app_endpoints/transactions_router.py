from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi_deps import get_current_user_id
from db.db_models import UserFinancialTransactions
from db.db import get_db
from schemas.transaction_schemas import TransactionBase, TransactionGetAllResponseModel
from typing import Optional

router = APIRouter(prefix="/transaction", tags=["app/transactions"])

@router.get("/getAllTransactions", response_model=TransactionGetAllResponseModel)
def get_all_transactions(
    current_user_id: int = 3, 
    db: Session = Depends(get_db),
    page_number: int = Query(1, ge=1, description="Número de página (mínimo 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página (entre 1 y 100)"),
    amount_or_source: Optional[str] = Query(None, description="Filtrar por monto o fuente (búsqueda parcial)"),
    type: Optional[str] = Query(None, description="Filtrar por tipo de transacción (income o expense)"),
    account_id: Optional[int] = Query(None, description="Filtrar por cuenta ID"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría ID"),
    source: Optional[str] = Query(None, description="Filtrar por fuente (búsqueda parcial)")
):
    try:
        is_amount = int(amount_or_source) if amount_or_source and amount_or_source.isdigit() else None
        # Verificar cuantos registros hay para el usuario con el filtro aplicado
        query = select(UserFinancialTransactions).where(UserFinancialTransactions.user_id == current_user_id)
        count_query = select(func.count()).select_from(UserFinancialTransactions).where(UserFinancialTransactions.user_id == current_user_id)

        if amount_or_source:
            if is_amount is not None:
                query = query.where(UserFinancialTransactions.final_amount == is_amount)
                count_query = count_query.where(UserFinancialTransactions.final_amount == is_amount)
            query = query.where(
                (UserFinancialTransactions.transaction_source.ilike(f"%{amount_or_source}%"))
            )
            count_query = count_query.where(
                (UserFinancialTransactions.transaction_source.ilike(f"%{amount_or_source}%"))
            )

        if type:
            query = query.where(UserFinancialTransactions.tipo_transaccion == type)
            count_query = count_query.where(UserFinancialTransactions.tipo_transaccion == type)
        if account_id:
            query = query.where(UserFinancialTransactions.account_id == account_id)
            count_query = count_query.where(UserFinancialTransactions.account_id == account_id)
        if category_id:
            query = query.where(UserFinancialTransactions.category_id == category_id)
            count_query = count_query.where(UserFinancialTransactions.category_id == category_id)
        if source:
            query = query.where(UserFinancialTransactions.transaction_source == source)
            count_query = count_query.where(UserFinancialTransactions.transaction_source == source)
        
        # Contar registros totales
        total_transactions = db.scalar(count_query)
        
        # Obtener las transacciones con paginación
        transactions = db.execute(query.order_by(UserFinancialTransactions.created_at.desc()).offset((page_number - 1) * page_size).limit(page_size)).scalars().all()
        return TransactionGetAllResponseModel(
            total_transactions=total_transactions,
            pagination_use=page_size,
            transactions=[TransactionBase(**transaction.__dict__) for transaction in transactions]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))