from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.1.2", "Descripcion": "Agregado Fechas a devolucion de peticion de correos. Error Arreglado con Fecha "}