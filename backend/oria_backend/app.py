import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from loguru import logger

from oria_backend.config import settings
from oria_backend.data_transformers.route import router as data_transformers_router
from oria_backend.logger_utils import initialize_logger
from oria_backend.songs.route import router as songs_router

HERE = os.path.dirname(os.path.abspath(__file__))

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


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(HERE, "static", "favicon.ico"))


@app.get("/manifest.json")
async def manifest():
    return FileResponse(os.path.join(HERE, "static", "manifest.json"))


@app.get("/")
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str = ""):
    if full_path:
        static_file_path = os.path.join(HERE, "static", full_path)
        if not os.path.exists(static_file_path):
            raise HTTPException(status_code=404, detail="Resource not found")
        return FileResponse(static_file_path)

    index_path = os.path.join(HERE, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Resource not found")


@app.on_event("startup")
async def startup_event():
    initialize_logger()
    logger.info(f"Starting up on http://{settings.host}:{settings.port}")
