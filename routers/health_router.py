from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.3.0", "Descripcion": "Agregado soporte para body Plain y HTML. Agregado guardado de segundos de ejecucion en base de datos - V1.3.0"}