from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str          # uppercase – matches .env and code
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    LOG_TO_FILE: bool = False
    REDIS_URL: str = "redis://redis:6379/0"   # add this line
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    FINNHUB_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()