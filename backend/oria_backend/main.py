import uvicorn
from fastapi import FastAPI
from config import settings

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


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
