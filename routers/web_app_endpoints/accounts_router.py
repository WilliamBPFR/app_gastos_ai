from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from db.db import get_db
from db.db_models import UserAccounts, AccountTypes
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_
from fastapi_deps import get_current_user_id
from schemas.account_schemas import AccountGetAllResponseModel, AccountBase, AccountTypeBase
from typing import Optional

router = APIRouter(prefix="/accounts", tags=["app/accounts"])

@router.get("/get-all", response_model=AccountGetAllResponseModel)
def get_accounts(
    current_user_id: int = 3, 
    db: Session = Depends(get_db),
    page_number: int = Query(1, ge=1, description="Número de página (mínimo 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página (entre 1 y 100)"),
    account_name: Optional[str] = Query(None, description="Filtrar por nombre de categoría (búsqueda parcial)"),
    status: Optional[bool] = Query(None, description="Filtrar por estado (activo o inactivo)")
):
    try:
        # Verificar cuantos registros hay para el usuario con el filtro aplicado
        print(f"Obteniendo cuentas para el usuario {current_user_id} con filtros - Nombre: {account_name}, Estado: {status}")
        query = select(UserAccounts).options(joinedload(UserAccounts.account_type)).where(UserAccounts.user_id == current_user_id)
        if account_name:
            query = query.where(
                or_(
                    UserAccounts.account_name.ilike(f"%{account_name}%"),
                    UserAccounts.account_description.ilike(f"%{account_name}%")
                )
            )
        if status is not None:
            query = query.where(UserAccounts.active == status)
        
        # Contar registros totales
        count_query = select(func.count()).select_from(UserAccounts).where(UserAccounts.user_id == current_user_id)
        if account_name:
            count_query = count_query.where(
                or_(
                    UserAccounts.account_name.ilike(f"%{account_name}%"),
                    UserAccounts.account_description.ilike(f"%{account_name}%")
                )
            )
        if status is not None:
            count_query = count_query.where(UserAccounts.active == status)
        total_accounts = db.scalar(count_query)
        
        # Obtener las categorías con paginación
        accounts = db.execute(query.order_by(UserAccounts.creation_date.desc()).offset((page_number - 1) * page_size).limit(page_size)).scalars().all()
        return AccountGetAllResponseModel(
            total_accounts=total_accounts,
            pagination_use=page_size,
            accounts=[
                AccountBase(
                    account_id=account.account_id,
                    account_name=account.account_name,
                    account_description=account.account_description,
                    creation_date=account.creation_date,
                    active=account.active,
                    account_type=AccountTypeBase(
                        account_type_id=account.account_type.account_type_id,
                        account_type_name=account.account_type.account_type_name,
                    ),
                )
                for account in accounts
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/deactivate/{account_id}")
def deactivate_account(
    account_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        account = db.execute(select(UserAccounts).where(UserAccounts.account_id == account_id, UserAccounts.user_id == current_user_id)).scalars().first()
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        account.active = False
        db.commit()
        return {"message": "Cuenta desactivada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/activate/{account_id}")
def activate_account(
    account_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        account = db.execute(select(UserAccounts).where(UserAccounts.account_id == account_id, UserAccounts.user_id == current_user_id)).scalars().first()
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        account.active = True
        db.commit()
        return {"message": "Cuenta activada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
def create_account(
    account: AccountBase, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        new_account = UserAccounts(
            user_id=current_user_id,
            account_name=account.account_name,
            account_description=account.account_description,
            active=account.active,
            account_type_id=account.account_type.account_type_id
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return {"message": "Cuenta creada exitosamente", "account_id": new_account.account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{account_id}")
def update_account(
    account_id: int,
    account: AccountBase, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        existing_account = db.execute(select(UserAccounts).where(UserAccounts.account_id == account_id, UserAccounts.user_id == current_user_id)).scalars().first()
        if not existing_account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")
        
        existing_account.account_name = account.account_name
        existing_account.account_description = account.account_description
        existing_account.active = account.active
        existing_account.account_type_id = account.account_type.account_type_id
        
        db.commit()
        return {"message": "Cuenta actualizada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accountstypes/get-all", response_model=list[AccountTypeBase])
def get_account_types(
    current_user_id: int = 3, 
    db: Session = Depends(get_db)
):
    try:
        account_types = db.execute(select(AccountTypes)).scalars().all()
        return [
            AccountTypeBase(account_type_id=atype.account_type_id, account_type_name=atype.account_type_name)
            for atype in account_types
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
