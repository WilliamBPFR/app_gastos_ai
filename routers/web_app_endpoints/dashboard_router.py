from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from db.db import get_db
from db.db_models import UserFinancialTransactions, UserEmailProcessingLogs
from datetime import datetime, timedelta
from typing import Optional

from fastapi_deps import get_current_user_id

router = APIRouter(prefix="/dashboard", tags=["app/dashboard"])

@router.get("/data")
def get_dashboard_data(current_user_id: int = 3, 
                       db: Session = Depends(get_db),
                       fechadesde: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD (Default desde hace un mes)"),
                       fechahasta: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD (Default hoy)")
):
    try:
        fechadesde_dt = datetime.strptime(fechadesde, "%Y-%m-%d") if fechadesde else datetime.now() - timedelta(days=30)
        fechahasta_dt = datetime.strptime(fechahasta, "%Y-%m-%d") if fechahasta else datetime.now()
        # Agregaciones de transacciones: suma y conteo por tipo (una sola consulta)
        income_sum, expense_sum, income_count, expense_count = db.query(
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'income', UserFinancialTransactions.final_amount), else_=0)), 0),
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'expense', UserFinancialTransactions.final_amount), else_=0)), 0),
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'income', 1), else_=0)), 0),
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'expense', 1), else_=0)), 0),
        ).filter(
            UserFinancialTransactions.user_id == current_user_id,
            UserFinancialTransactions.fecha_transaccion >= fechadesde_dt,
            UserFinancialTransactions.fecha_transaccion <= fechahasta_dt
        ).one()
        
        # Buscar los correos electronicos analizados en el rango de fechas para el usuario actual
        total_correos_analizados = db.query(
            func.coalesce(func.sum(UserEmailProcessingLogs.cantidad_correos_obtenidos), 0)).filter(
            UserEmailProcessingLogs.user_id == current_user_id,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento >= fechadesde_dt,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento <= fechahasta_dt).scalar()
        
        
        total_transacciones_registradas = int(income_count + expense_count)

        dashboard_data = {
            "message": f"Dashboard data for user_id {current_user_id}",
            "total_ingresos": float(income_sum),
            "total_ingresos_count": int(income_count),
            "total_egresos": float(expense_sum),
            "total_egresos_count": int(expense_count),
            "total_transacciones_registradas": total_transacciones_registradas,
            "total_correos_analizados": int(total_correos_analizados)
        }
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
