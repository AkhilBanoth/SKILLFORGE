from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.database.mongodb import check_mongodb, close_mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...")
    app.state.mongodb_connected = check_mongodb()
    print(f"MongoDB connected: {app.state.mongodb_connected}")

    
    yield
    
    close_mongodb()
    print("MongoDB connection closed.")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI Learning, Certification & Career Readiness Platform",
    lifespan=lifespan,
)



@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to SkillForge",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "mongodb_connected": getattr(app.state, "mongodb_connected", False,
        ),

    }