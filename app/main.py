import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.api.routes import router as api_router
from eval.run_security import seed_corpus_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_corpus_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Permission-aware enterprise RAG platform enforcing authorization at retrieval time and answer time.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/healthz", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": "1.0.0"}


@app.get("/", response_class=HTMLResponse, tags=["UI"])
def serve_ui():
    """Serves the SentinelRAG web interface."""
    ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>SentinelRAG API is running</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
