from fastapi import APIRouter

from app.api.routes import assets, chat, dashboard, discovery, findings, integrations

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(assets.router)
api_router.include_router(findings.router)
api_router.include_router(integrations.router)
api_router.include_router(chat.router)
api_router.include_router(discovery.router)
