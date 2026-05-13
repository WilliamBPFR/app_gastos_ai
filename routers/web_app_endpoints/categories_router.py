from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends
from db.db import get_db
from db.db_models import UserCategories
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi_deps import get_current_user_id
from schemas.category_schemas import CategoryBase, CategoryGetAllResponseModel, CategoryCreateModel
from typing import Optional

router = APIRouter(prefix="/categories", tags=["app/categories"])

@router.get("/get-all", response_model=CategoryGetAllResponseModel)
def get_categories(
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db),
    page_number: int = Query(1, ge=1, description="Número de página (mínimo 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página (entre 1 y 100)"),
    category_name: Optional[str] = Query(None, description="Filtrar por nombre de categoría (búsqueda parcial)"),
):
    try:
        # Verificar cuantos registros hay para el usuario con el filtro aplicado
        query = select(UserCategories).where(UserCategories.user_id == current_user_id)
        if category_name:
            query = query.where(UserCategories.category_name.ilike(f"%{category_name}%"))
        
        # Contar registros totales
        count_query = select(func.count()).select_from(UserCategories).where(UserCategories.user_id == current_user_id)
        if category_name:
            count_query = count_query.where(UserCategories.category_name.ilike(f"%{category_name}%"))
        total_categories = db.scalar(count_query)
        
        # Obtener las categorías con paginación
        categories = db.execute(query.order_by(UserCategories.creation_date.desc()).offset((page_number - 1) * page_size).limit(page_size)).scalars().all()
        return CategoryGetAllResponseModel(
            total_categories=total_categories,
            pagination_use=page_size,
            categories=[CategoryBase(**category.__dict__) for category in categories]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
def create_category(
    category: CategoryCreateModel, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        new_category = UserCategories(
            user_id=current_user_id,
            category_name=category.category_name,
            category_description=category.category_description,
            color=category.color,
            active=category.active
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return {"message": "Categoría creada exitosamente", "category_id": new_category.category_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/deactivate/{category_id}")
def deactivate_category(
    category_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        select_query = select(UserCategories).where(UserCategories.category_id == category_id, UserCategories.user_id == current_user_id)
        category = db.execute(select_query).scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        category.active = False
        db.commit()
        return {"message": f"Categoría {'activada' if category.active else 'desactivada'} exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/activate/{category_id}")
def activate_category(
    category_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        select_query = select(UserCategories).where(UserCategories.category_id == category_id, UserCategories.user_id == current_user_id)
        category = db.execute(select_query).scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        category.active = True
        db.commit()
        return {"message": f"Categoría {'activada' if category.active else 'desactivada'} exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{category_id}")
def delete_category(
    category_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        select_query = select(UserCategories).where(UserCategories.category_id == category_id, UserCategories.user_id == current_user_id)
        category = db.execute(select_query).scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        db.delete(category)
        db.commit()
        return {"message": "Categoría eliminada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/update/{category_id}")
def update_category(
    category_id: int, 
    category_update: CategoryCreateModel, 
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    try:
        select_query = select(UserCategories).where(UserCategories.category_id == category_id, UserCategories.user_id == current_user_id)
        category = db.execute(select_query).scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
        category.category_name = category_update.category_name
        category.category_description = category_update.category_description
        category.color = category_update.color
        category.active = category_update.active
        
        db.commit()
        return {"message": "Categoría actualizada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))