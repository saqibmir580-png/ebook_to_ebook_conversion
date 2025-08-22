from fastapi import APIRouter

from app.routes import auth, upload, dashboard, pricing, ocr


api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(upload.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
# downloads router is included separately in main.py to handle public endpoints
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])