"""Ponto de entrada da API — instancia o FastAPI e inclui os routers."""
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routers import admin, participante, webhooks  # noqa: E402

app = FastAPI(title="Portal de Pagamentos — Confraternização")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(participante.router)
app.include_router(admin.router)
app.include_router(webhooks.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
