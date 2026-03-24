import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.crawl_controller import router as crawl_router
from app.core.settings import settings

app = FastAPI(title=settings.app_name)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl_router)
