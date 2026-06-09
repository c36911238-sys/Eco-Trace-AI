from fastapi import APIRouter
from app.api.v1.endpoints import auth, carbon

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    return {"status": "ok"}

api_router.include_router(auth.router, tags=["login"])
api_router.include_router(carbon.router, prefix="/carbon", tags=["carbon"])
