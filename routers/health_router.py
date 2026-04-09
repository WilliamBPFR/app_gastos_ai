from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.1.3", "Descripcion": "Arreglo problema con hora de Verificacion de Correos "}