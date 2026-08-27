"""Core Application Configuration Settings."""

import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "BuildIQ AI - Automated Pile Foundation Takeoff Engine"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",
    ]

    # NVIDIA NIM API Settings
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_VISION_MODEL: str = "meta/llama-3.2-90b-vision-instruct"
    NVIDIA_TEXT_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"

    # Civil Engineering Design Constants
    DEFAULT_CLEAR_COVER_MM: float = 50.0
    DEFAULT_CONCRETE_GRADE: str = "M35"
    DEFAULT_STEEL_GRADE: str = "Fe500D"
    UNIT_WEIGHT_STEEL_DENOMINATOR: float = 162.28  # IS 1786 standard d^2 / 162.28 kg/m

    # Manpower Estimation Constants (Man-Days)
    MANPOWER_PILING_CONCRETE_PER_M3: float = 0.25  # 0.25 Man-Days per m³
    MANPOWER_REBAR_PER_MT: float = 2.50            # 2.50 Man-Days per MT
    MANPOWER_CHIPPING_PER_PILE: float = 0.50       # 0.50 Man-Days per pile

    # File storage paths
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]


settings = Settings()

# Ensure runtime directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
