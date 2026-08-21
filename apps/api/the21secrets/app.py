from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from the21secrets.api import api_router
from the21secrets.bootstrap import seed_admin_user
from the21secrets.config import get_settings
from the21secrets.db.base import get_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async for db in get_db():
        await seed_admin_user(db)
        break
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="The21Secrets AI Ads OS API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
