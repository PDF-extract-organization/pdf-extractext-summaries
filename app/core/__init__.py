"""Configuración leída de variables de entorno o del .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "pdf_extractext"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
