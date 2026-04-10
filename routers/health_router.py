from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.2.0", "Descripcion": "Retorno del body Plain y HTML - V1.2.0"}