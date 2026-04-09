from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.1.0", "Descripcion": "Modificacion a entrad ade historial de obtencion de correos"}