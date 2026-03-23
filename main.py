from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.crawl_controller import router as crawl_router
from app.core.settings import settings

app = FastAPI(title=settings.app_name)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl_router)
