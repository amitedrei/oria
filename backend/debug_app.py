import uvicorn
from oria_backend.config import settings


def main():
    uvicorn.run(
        app="oria_backend.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env == "dev",
        workers=1,
    )


if __name__ == "__main__":
    main()
