import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, conversations, documents
from app.core.config import settings
from app import models  # noqa: F401 — гарантирует, что все SQLAlchemy-модели зарегистрированы

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-powered travel assistant platform",
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(documents.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "travel-ai-backend"}


@app.get("/")
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} API",
        "version": settings.PROJECT_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)