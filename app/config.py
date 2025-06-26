from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database settings
    # DATABASE_URL is loaded from .env if present. No default: must be set in .env
    DATABASE_URL: str
    
    # OpenAI settings
    # OPENAI_API_KEY is loaded from .env if present. No default: must be set in .env
    OPENAI_API_KEY: str
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True
    
    # CORS settings
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Audio processing settings
    WHISPER_MODEL: str = "base"
    MAX_AUDIO_SIZE: int = 50 * 1024 * 1024  # 50MB
    AUDIO_FORMATS: list = ["wav", "mp3", "m4a", "flac"]
    
    # Meeting settings
    MAX_PARTICIPANTS: int = 4
    ROOM_CODE_LENGTH: int = 6
    
    # File storage settings
    RECORDINGS_DIR: str = "recordings"
    TEMP_DIR: str = "temp"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.RECORDINGS_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
