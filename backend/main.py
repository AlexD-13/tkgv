import datetime
import os

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import CORS_ORIGINS
from config.logging_config import setup_logging
from database.session import init_pragmas_check

# Configurar logging al iniciar la aplicación
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pragmas_check()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers se registran aquí a medida que se implementan:
from routers import dishes, registrations, proposals, admin

app.include_router(dishes.router, prefix="/api")
app.include_router(registrations.router, prefix="/api")
app.include_router(proposals.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/status", include_in_schema=False)
async def detailed_status():
    return {
        "status": "running",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": "production",
    }

# Servir assets del frontend compilado.
if os.path.isdir("public/_nuxt"):
    app.mount("/_nuxt", StaticFiles(directory="public/_nuxt"), name="nuxt_assets")

# SPA catch-all: cualquier ruta no-API devuelve index.html (Vue Router toma el control).
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    # Archivos estáticos existentes en public/ (favicon, etc.)
    file_path = os.path.join("public", full_path)
    if full_path and os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = os.path.join("public", "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
