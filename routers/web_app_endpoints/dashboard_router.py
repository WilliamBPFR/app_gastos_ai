from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from db.db import get_db
from db.db_models import UserFinancialTransactions, UserEmailProcessingLogs, UserCategories
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi_deps import get_current_user_id

router = APIRouter(prefix="/dashboard", tags=["app/dashboard"])

@router.get("/data")
def get_dashboard_data(current_user_id: int = Depends(get_current_user_id), 
                       db: Session = Depends(get_db),
                       fechadesde: Optional[str] = Query(None, description="Fecha de inicio en formato YYYY-MM-DD (Default desde hace un mes)"),
                       fechahasta: Optional[str] = Query(None, description="Fecha de fin en formato YYYY-MM-DD (Default hoy)")
):
    try:
        fechadesde_dt = datetime.strptime(fechadesde, "%Y-%m-%d") if fechadesde else datetime.now() - timedelta(days=30)
        fechahasta_dt = datetime.strptime(fechahasta, "%Y-%m-%d") if fechahasta else datetime.now()
        diferencia_dias = (fechahasta_dt - fechadesde_dt).days
        fechadesde_periodo_anterior = fechadesde_dt - timedelta(days=diferencia_dias)
        fechahasta_periodo_anterior = fechahasta_dt - timedelta(days=diferencia_dias)
        
    
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
        
        # Agregaciones de transacciones para el periodo anterior: suma y conteo por tipo (una sola consulta)
        income_sum_anterior, expense_sum_anterior = db.query(
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'income', UserFinancialTransactions.final_amount), else_=0)), 0),
            func.coalesce(func.sum(case((UserFinancialTransactions.tipo_transaccion == 'expense', UserFinancialTransactions.final_amount), else_=0)), 0),
        ).filter(
            UserFinancialTransactions.user_id == current_user_id,
            UserFinancialTransactions.fecha_transaccion >= fechadesde_periodo_anterior,
            UserFinancialTransactions.fecha_transaccion <= fechahasta_periodo_anterior
        ).one()

        porcentaje_cambio_ingresos = ((income_sum - income_sum_anterior) / income_sum_anterior * 100) if income_sum_anterior != 0 else None
        porcentaje_cambio_egresos = ((expense_sum - expense_sum_anterior) / expense_sum_anterior * 100) if expense_sum_anterior != 0 else None
        # Buscar los correos electronicos analizados en el rango de fechas para el usuario actual
        total_correos_analizados = db.query(
            func.coalesce(func.sum(UserEmailProcessingLogs.cantidad_correos_obtenidos), 0)).filter(
            UserEmailProcessingLogs.user_id == current_user_id,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento >= fechadesde_dt,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento <= fechahasta_dt).scalar()
        
        total_transacciones_registradas = int(income_count + expense_count)

        # Calcular la cantidad de gastos por categoria 
        gastos_por_categoria = db.query(
            UserFinancialTransactions.category_id,
            UserCategories.category_name,
            func.coalesce(func.sum(UserFinancialTransactions.final_amount), 0),
            UserCategories.color
        ).join(
            UserCategories,
            UserFinancialTransactions.category_id == UserCategories.category_id
        ).filter(
            UserFinancialTransactions.user_id == current_user_id,
            UserFinancialTransactions.tipo_transaccion == 'expense',
            UserFinancialTransactions.fecha_transaccion >= fechadesde_dt,
            UserFinancialTransactions.fecha_transaccion <= fechahasta_dt
        ).group_by(
            UserFinancialTransactions.category_id,
            UserCategories.category_name,
            UserCategories.color
        ).order_by(
            func.sum(UserFinancialTransactions.final_amount).desc()
        ).all()

        # Obtener los analisis de correo realizados por dia en el rango de fechas para el usuario actual
        analisis_por_dia_rows = db.query(
            func.date(UserEmailProcessingLogs.fecha_terminacion_procesamiento).label('fecha'),
            func.coalesce(func.sum(UserEmailProcessingLogs.cantidad_correos_obtenidos), 0).label('correos_analizados'),
            func.coalesce(func.sum(UserEmailProcessingLogs.cantidad_correos_validos), 0).label('correos_transaccion')
        ).filter(
            UserEmailProcessingLogs.user_id == current_user_id,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento >= fechadesde_dt,
            UserEmailProcessingLogs.fecha_terminacion_procesamiento <= fechahasta_dt
        ).group_by(
            func.date(UserEmailProcessingLogs.fecha_terminacion_procesamiento)
        ).order_by(
            func.date(UserEmailProcessingLogs.fecha_terminacion_procesamiento)
        ).all()

        analisis_por_dia_map = {
            fila.fecha: {
                "correos_analizados": int(fila.correos_analizados),
                "correos_transaccion": int(fila.correos_transaccion),
            }
            for fila in analisis_por_dia_rows
        }

        fecha_inicio = fechadesde_dt.date()
        fecha_fin = fechahasta_dt.date()
        total_dias = (fecha_fin - fecha_inicio).days + 1

        analisis_por_dia = [
            {
                "fecha": (fecha_inicio + timedelta(days=indice)).isoformat(),
                "correos_analizados": analisis_por_dia_map.get(fecha_inicio + timedelta(days=indice), {}).get("correos_analizados", 0),
                "correos_transaccion": analisis_por_dia_map.get(fecha_inicio + timedelta(days=indice), {}).get("correos_transaccion", 0),
            }
            for indice in range(total_dias)
        ]

        dashboard_data = {
            "message": f"Dashboard data for user_id {current_user_id}",
            "total_ingresos": float(income_sum),
            "porcentaje_cambio_ingresos": porcentaje_cambio_ingresos,
            "total_ingresos_count": int(income_count),
            "total_egresos": float(expense_sum),
            "porcentaje_cambio_egresos": porcentaje_cambio_egresos,
            "total_egresos_count": int(expense_count),
            "total_transacciones_registradas": total_transacciones_registradas,
            "total_correos_analizados": int(total_correos_analizados),
            "gastos_por_categoria": [
                {
                    "category_id": category_id,
                    "category_name": category_name,
                    "total_gastos": float(total_gastos),
                    "color": color
                }                
                for category_id, category_name, total_gastos, color in gastos_por_categoria
            ],
            "analisis_por_dia": analisis_por_dia
        }
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
