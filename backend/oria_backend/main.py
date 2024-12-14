import uvicorn
from fastapi import FastAPI
from config import settings
from data_transformers.route import router as data_transformers_router

app = FastAPI()
app.include_router(data_transformers_router)


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
