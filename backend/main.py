# main.py
import datetime
import os

import uvicorn
from decouple import config
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.logging_config import setup_logging

# Configurar logging al iniciar la aplicación
setup_logging()


def main():
    print("Hello from backend!")


app = FastAPI()

# CORS: necesario para que el navegador envíe/reciba la cookie de sesión
# desde el frontend (otro origen/puerto). allow_credentials obliga a
# restringir origins (no se puede usar "*").
cors_origins = [
    origin.strip()
    for origin in config(
        "CORS_ORIGINS",
        default="http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Habilita el envío de cookies httpOnly
    allow_methods=["*"],
    allow_headers=["*"],
)

# example
# app.include_router(auth_router, prefix="/api/v1", tags=["Auth & Cuentas"])

@app.get("/status", include_in_schema=False)
async def detailed_status():
    return {
        "status": "running",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": "production"
    }

# --- Configuración para servir Vue ---

# # 1. Montamos la carpeta 'assets' (JS, CSS, Imágenes)
# # Esto asume que tu carpeta 'dist' está al mismo nivel que main.py
# if os.path.exists("public/_nuxt"):
#     app.mount("/_nuxt", StaticFiles(directory="public/_nuxt"), name="static")

# # 2. Ruta "Catch-all" para la SPA (Single Page Application)
# # Esta ruta debe ir AL FINAL de todas tus rutas.
# @app.get("/{full_path:path}")
# async def serve_spa(full_path: str):
#     # Si el usuario pide un archivo que existe en dist (ej: favicon.ico)
#     file_path = os.path.join("dist", full_path)
#     if os.path.isfile(file_path):
#         return FileResponse(file_path)

#     # Para cualquier otra ruta (ej: /home, /acerca-de), servimos el index.html
#     # Esto permite que Vue Router tome el control en el navegador.
#     return FileResponse("public/index.html")


app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    main()
    uvicorn.run(app, host="0.0.0.0", port=8000)
