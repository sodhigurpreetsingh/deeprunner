from fastapi import APIRouter
from app.api.routes import documents, search, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(health.router)
