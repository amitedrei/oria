import uvicorn
from config import settings
from data_transformers.route import router as data_transformers_router
from fastapi import FastAPI

from logger_utils import initialize_logger

app = FastAPI()
app.include_router(data_transformers_router)
from loguru import logger


@app.on_event("startup")
async def startup_event():
    initialize_logger()
    logger.info(f"Starting up on http://{settings.host}:{settings.port}")


def main():
    uvicorn.run(
        app="main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "dev",
        workers=1,
    )


if __name__ == "__main__":
    main()
