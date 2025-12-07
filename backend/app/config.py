from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """Application configuration"""
    
    # API
    API_TITLE: str = "Face Emotion Detection API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Real-time face recognition and emotion detection"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/face_emotion"
    )
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "face-emotion-bucket")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Models
    MODEL_WEIGHTS_DIR: str = os.getenv("MODEL_WEIGHTS_DIR", "./models")
    RETINAFACE_WEIGHTS: str = "retinaface_resnet50"
    ARCFACE_WEIGHTS: str = "arcface_resnet50"
    VIT_EMOTION_WEIGHTS: str = "vit_emotion"
    
    # Processing
    MAX_IMAGES_TO_PROCESS: int = 50
    FACE_SIMILARITY_THRESHOLD: float = 0.6
    EMOTION_CONFIDENCE_THRESHOLD: float = 0.3
    
    # Session
    SESSION_EXPIRY_HOURS: int = 24
    SESSION_CLEANUP_INTERVAL_HOURS: int = 1
    
    # Security
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
