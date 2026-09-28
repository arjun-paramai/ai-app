from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://clausecompass:local@localhost:5432/clausecompass"
    jwt_secret: str = Field(min_length=32)
    ollama_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    chat_model: str = "llama3.2"
    cookie_secure: bool = False


settings = Settings()
