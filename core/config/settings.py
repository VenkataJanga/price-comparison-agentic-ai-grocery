from pydantic import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"
    class Config:
        env_file = ".env"

settings = Settings()
