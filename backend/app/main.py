"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_health, routes_profile

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NextRupee API",
        version="0.1.0",
        description=(
            "Decision-support engine. All arithmetic is deterministic and code-owned; "
            "the LLM never computes. Educational decision support — not investment advice; "
            "no specific instruments, ever."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tightened to the Vercel domain at deploy time via env
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes_profile.router)
    app.include_router(routes_health.router)

    # Later phases mount: routes_nbca, routes_ask (see docs/project/ROADMAP.md)
    try:
        from app.api import routes_ask, routes_nbca

        app.include_router(routes_nbca.router)
        app.include_router(routes_ask.router)
    except ImportError:
        pass

    return app


app = create_app()
