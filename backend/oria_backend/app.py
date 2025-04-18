from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from oria_backend.config import settings
from oria_backend.data_transformers.route import router as data_transformers_router
from oria_backend.logger_utils import initialize_logger
from oria_backend.songs.route import router as songs_router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_transformers_router)
app.include_router(songs_router)


@app.on_event("startup")
async def startup_event():
    initialize_logger()
    logger.info(f"Starting up on http://{settings.host}:{settings.port}")
