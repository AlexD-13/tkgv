import datetime
import os

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from routers import dishes, registrations, proposals

app.include_router(dishes.router, prefix="/api")
app.include_router(registrations.router, prefix="/api")
app.include_router(proposals.router, prefix="/api")
# ...

@app.get("/status", include_in_schema=False)
async def detailed_status():
    return {
        "status": "running",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": "production",
    }

# Servir el frontend compilado (si existe).
if os.path.isdir("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
