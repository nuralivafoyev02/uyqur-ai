from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import build_container
from app.routes import (
    admin_audit,
    admin_agents,
    admin_auth,
    admin_groups,
    admin_kb,
    admin_settings,
    admin_stats,
    admin_tickets,
    health,
    webhook,
)


def create_app(env_source=None) -> FastAPI:
    app = FastAPI(title="Uyqur AI Backend", version="0.1.0")
    container = build_container(env_source)
    app.state.container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=container.settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(webhook.router)
    app.include_router(admin_auth.router)
    app.include_router(admin_groups.router)
    app.include_router(admin_tickets.router)
    app.include_router(admin_agents.router)
    app.include_router(admin_settings.router)
    app.include_router(admin_kb.router)
    app.include_router(admin_stats.router)
    app.include_router(admin_audit.router)
    return app
