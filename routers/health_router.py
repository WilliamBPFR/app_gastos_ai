from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "message": "API is healthy", "version": "1.0.2", "Descripcion": "Agregado verificacion de usuario a endpoint de start oauth, para evitar errores al iniciar el proceso de autorizacion con un usuario no registrado en la base de datos. Arreglo User ID"}