from os import path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = path.join(path.dirname(__file__), "..", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH)

    host: str
    port: int
    env: str
    mongo_uri: str
    mongo_db_name: str


settings = Settings()
