from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.db import Base, engine
from routers.oauth_router import router as oauth_router
from routers.internal_router import router as internal_router
from routers.health_router import router as health_router
from routers.files_router import router as files_router
from routers.web_app_endpoints import web_app_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aquí puedes colocar cualquier código de inicialización que necesites
    Base.metadata.create_all(bind=engine)
    yield
    # Aquí puedes colocar cualquier código de limpieza que necesites

app = FastAPI(title="Gmail OAuth Backend", lifespan=lifespan, version="1.3.0", description="Backend para autenticación OAuth con Gmail, con verificación de usuario en el endpoint de inicio y manejo de conexiones de usuarios.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(oauth_router)
app.include_router(internal_router)
app.include_router(files_router)
app.include_router(web_app_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)