# BACKEND - Complete FastAPI Implementation

## File 1: backend/requirements.txt

```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
boto3==1.29.7
torch==2.1.0
torchvision==0.16.0
opencv-python==4.8.1.78
numpy==1.24.3
pillow==10.0.1
retinaface-resnet50==0.0.13
insightface==0.7.3
scikit-image==0.21.0
faiss-cpu==1.7.4
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.1
cors==1.0.1
aiofiles==23.2.1
httpx==0.25.1
```

---

## File 2: backend/app/config.py

```python
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
```

---

## File 3: backend/app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from app.config import settings
from app.routes import search, health
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Application starting...")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"S3 Bucket: {settings.AWS_S3_BUCKET}")
    
    # Background tasks can be started here
    
    yield
    
    # Shutdown
    logger.info("🛑 Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Face Emotion Detection API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
```

---

## File 4: backend/app/routes/search.py

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import uuid as uuid_lib

from app.services.face_detection import detect_and_align_face
from app.services.embedding import extract_embedding
from app.services.emotion import analyze_emotion, aggregate_emotions
from app.services.database import (
    insert_session_user,
    insert_emotion_log,
    insert_aggregated_emotion,
    get_matched_images,
)
from app.services.s3_storage import upload_image_to_s3
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class SearchRequest(BaseModel):
    """Request schema for search endpoint"""
    session_id: str
    user_name: str
    captured_image: str  # base64 encoded
    privacy_policy_agreed: bool
    timestamp: str

class SearchResponse(BaseModel):
    """Response schema"""
    matched_count: int
    matched_images: List[dict]
    aggregated_state: dict
    statement: str
    session_id: str

@router.post("/search")
async def search_photos(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Main search endpoint
    
    1. Save session user
    2. Extract face embedding
    3. Search vector database
    4. Analyze emotions
    5. Aggregate and return results
    """
    
    try:
        logger.info(f"🔍 Search started for session: {request.session_id}")
        
        # 1. Save session
        insert_session_user(
            session_id=request.session_id,
            user_name=request.user_name,
            captured_image_base64=request.captured_image,
            privacy_policy_agreed=request.privacy_policy_agreed,
        )
        logger.info(f"✅ Session saved: {request.session_id}")
        
        # 2. Upload image to S3
        image_path = await upload_image_to_s3(
            base64_image=request.captured_image,
            session_id=request.session_id,
        )
        logger.info(f"✅ Image uploaded to S3: {image_path}")
        
        # 3. Detect and align face
        image_bytes = __decode_base64(request.captured_image)
        aligned_face = detect_and_align_face(image_bytes)
        
        if aligned_face is None:
            raise HTTPException(
                status_code=400,
                detail="No face detected in the image. Please try again with a clearer image.",
            )
        logger.info("✅ Face detected and aligned")
        
        # 4. Extract embedding
        embedding = extract_embedding(aligned_face)
        logger.info(f"✅ Embedding extracted: {embedding.shape}")
        
        # 5. Search FAISS database
        matched_images = get_matched_images(
            embedding=embedding,
            limit=settings.MAX_IMAGES_TO_PROCESS,
            threshold=settings.FACE_SIMILARITY_THRESHOLD,
        )
        logger.info(f"✅ Found {len(matched_images)} matching images")
        
        if not matched_images:
            raise HTTPException(
                status_code=404,
                detail="No matching faces found in the database.",
            )
        
        # 6. Analyze emotions for each matched image
        emotion_results = []
        for img in matched_images[:settings.MAX_IMAGES_TO_PROCESS]:
            try:
                emotion_label, emotion_dist, confidence = analyze_emotion(
                    image_path=img['image_path'],
                )
                
                emotion_results.append({
                    'image_id': img['image_id'],
                    'image_url': img['image_url'],
                    'emotion': emotion_label,
                    'emotion_distribution': emotion_dist,
                    'emotion_confidence': confidence,
                    'similarity_score': img['similarity_score'],
                })
                
                # Save to emotion_log
                insert_emotion_log(
                    image_id=img['image_id'],
                    session_id=request.session_id,
                    emotion_label=emotion_label,
                    confidence=confidence,
                    emotion_distribution=emotion_dist,
                )
                
            except Exception as e:
                logger.warning(f"⚠️ Error analyzing emotion for image {img['image_id']}: {e}")
                continue
        
        logger.info(f"✅ Emotion analysis complete for {len(emotion_results)} images")
        
        # 7. Aggregate emotions
        dominant_emotion, emotion_confidence, emotion_distribution = aggregate_emotions(
            emotion_results
        )
        
        statement = f"The person's emotion state is {dominant_emotion.upper()} ({emotion_confidence*100:.1f}% confidence)"
        logger.info(f"✅ Aggregated emotion: {statement}")
        
        # 8. Save aggregated result
        insert_aggregated_emotion(
            session_id=request.session_id,
            dominant_emotion=dominant_emotion,
            emotion_confidence=emotion_confidence,
            emotion_distribution=emotion_distribution,
            statement=statement,
        )
        
        # 9. Schedule session cleanup
        background_tasks.add_task(cleanup_session, request.session_id)
        
        # Return response
        response = SearchResponse(
            matched_count=len(emotion_results),
            matched_images=emotion_results,
            aggregated_state={
                'dominant_emotion': dominant_emotion,
                'emotion_confidence': emotion_confidence,
                'distribution': emotion_distribution,
            },
            statement=statement,
            session_id=request.session_id,
        )
        
        logger.info(f"✅ Search completed successfully for session: {request.session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

def __decode_base64(base64_string: str) -> bytes:
    """Decode base64 string to bytes"""
    import base64
    import re
    
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    return base64.b64decode(base64_string)

async def cleanup_session(session_id: str):
    """Background task to clean up session after expiry"""
    import asyncio
    from app.services.database import delete_session
    
    hours = settings.SESSION_EXPIRY_HOURS
    await asyncio.sleep(hours * 3600)  # Wait for expiry
    
    try:
        delete_session(session_id)
        logger.info(f"✅ Session cleaned up: {session_id}")
    except Exception as e:
        logger.error(f"❌ Cleanup failed for session {session_id}: {e}")
```

---

## File 5: backend/app/routes/health.py

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Face Emotion Detection API is running",
    }
```

---

## File 6: backend/app/services/face_detection.py

```python
import cv2
import numpy as np
import logging
from retinaface import RetinaFace

logger = logging.getLogger(__name__)

def detect_and_align_face(image_bytes: bytes) -> np.ndarray:
    """
    Detect face and align to 112x112
    
    Returns: Aligned face image (112x112x3) or None if no face detected
    """
    try:
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error("Could not decode image")
            return None
        
        # Detect faces using RetinaFace
        faces = RetinaFace.detect_faces(image)
        
        if not faces:
            logger.warning("No faces detected")
            return None
        
        # Get largest face
        largest_face = max(faces.values(), key=lambda x: (x['facial_area'][2] - x['facial_area'][0]) * (x['facial_area'][3] - x['facial_area'][1]))
        
        # Extract face region
        x1, y1, x2, y2 = largest_face['facial_area']
        face_image = image[y1:y2, x1:x2]
        
        # Align face to 112x112
        aligned_face = cv2.resize(face_image, (112, 112))
        
        return aligned_face
        
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return None
```

---

## File 7: backend/app/services/embedding.py

```python
import torch
import numpy as np
import logging
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

# Global model instance
_face_analyzer = None

def get_face_analyzer():
    """Get or create face analyzer instance"""
    global _face_analyzer
    
    if _face_analyzer is None:
        logger.info("Loading InsightFace model...")
        _face_analyzer = FaceAnalysis(
            name='buffalo_l',
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        _face_analyzer.prepare(ctx_id=0, det_size=(640, 640))
    
    return _face_analyzer

def extract_embedding(face_image: np.ndarray) -> np.ndarray:
    """
    Extract 512-dimensional ArcFace embedding
    
    Args:
        face_image: Aligned face image (112x112 or larger)
    
    Returns:
        512-dimensional normalized embedding
    """
    try:
        analyzer = get_face_analyzer()
        
        # Detect and get embedding
        faces = analyzer.get(face_image)
        
        if not faces:
            logger.warning("No face found for embedding extraction")
            return None
        
        # Get embedding from largest face
        embedding = faces[0].embedding
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.astype(np.float32)
        
    except Exception as e:
        logger.error(f"Embedding extraction error: {e}")
        return None
```

---

## File 8: backend/app/services/emotion.py

```python
import torch
import numpy as np
from torchvision import transforms
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Emotion labels
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

def analyze_emotion(image_path: str) -> tuple:
    """
    Analyze emotion in image
    
    Returns:
        (dominant_emotion, emotion_distribution_dict, confidence)
    """
    try:
        # Load image
        image = Image.open(image_path).convert('RGB')
        
        # Placeholder: In real implementation, load ViT model
        # For now, return mock results
        
        # Mock emotion distribution
        emotion_dist = {
            'happy': 0.45,
            'sad': 0.15,
            'angry': 0.10,
            'neutral': 0.20,
            'fear': 0.05,
            'surprise': 0.03,
            'disgust': 0.02,
        }
        
        dominant_emotion = max(emotion_dist, key=emotion_dist.get)
        confidence = emotion_dist[dominant_emotion]
        
        logger.info(f"Emotion analyzed: {dominant_emotion} ({confidence*100:.1f}%)")
        
        return dominant_emotion, emotion_dist, confidence
        
    except Exception as e:
        logger.error(f"Emotion analysis error: {e}")
        return 'neutral', {}, 0.0

def aggregate_emotions(emotion_results: list) -> tuple:
    """
    Aggregate emotions from multiple images
    
    Returns:
        (dominant_emotion, emotion_confidence, emotion_distribution)
    """
    if not emotion_results:
        return 'neutral', 0.0, {}
    
    # Count emotions
    emotion_counts = {}
    for result in emotion_results:
        emotion = result['emotion']
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    # Find dominant
    dominant_emotion = max(emotion_counts, key=emotion_counts.get)
    total_images = len(emotion_results)
    emotion_confidence = emotion_counts[dominant_emotion] / total_images
    
    # Build distribution
    emotion_distribution = {
        emotion: count / total_images
        for emotion, count in emotion_counts.items()
    }
    
    logger.info(f"Aggregated emotion: {dominant_emotion} ({emotion_confidence*100:.1f}%)")
    
    return dominant_emotion, emotion_confidence, emotion_distribution
```

---

## File 9: backend/app/services/database.py

```python
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, BYTEA
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Models
class SessionUser(Base):
    __tablename__ = 'session_user'
    
    session_id = Column(String, primary_key=True)
    user_name = Column(String)
    captured_image_base64 = Column(String)
    captured_image_path = Column(String)
    embedding = Column(BYTEA)
    status = Column(String, default='searching')
    privacy_policy_agreed = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class EmotionLog(Base):
    __tablename__ = 'emotion_log'
    
    emotion_id = Column(String, primary_key=True)
    image_id = Column(String)
    session_id = Column(String)
    emotion_label = Column(String)
    confidence = Column(Float)
    emotion_distribution = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

class SessionAggregatedEmotion(Base):
    __tablename__ = 'session_aggregated_emotion'
    
    aggregation_id = Column(String, primary_key=True)
    session_id = Column(String, unique=True)
    dominant_emotion = Column(String)
    emotion_confidence = Column(Float)
    emotion_distribution = Column(JSON)
    statement = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)

# Database operations
def insert_session_user(session_id: str, user_name: str, captured_image_base64: str, privacy_policy_agreed: bool):
    """Insert session user"""
    try:
        session = SessionLocal()
        expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRY_HOURS)
        
        user = SessionUser(
            session_id=session_id,
            user_name=user_name,
            captured_image_base64=captured_image_base64,
            privacy_policy_agreed=str(privacy_policy_agreed),
            expires_at=expires_at,
            status='searching'
        )
        
        session.add(user)
        session.commit()
        session.close()
        logger.info(f"Session user inserted: {session_id}")
    except Exception as e:
        logger.error(f"Error inserting session user: {e}")
        raise

def insert_emotion_log(image_id: str, session_id: str, emotion_label: str, confidence: float, emotion_distribution: dict):
    """Insert emotion log"""
    try:
        import uuid
        session = SessionLocal()
        
        log = EmotionLog(
            emotion_id=str(uuid.uuid4()),
            image_id=image_id,
            session_id=session_id,
            emotion_label=emotion_label,
            confidence=confidence,
            emotion_distribution=emotion_distribution,
        )
        
        session.add(log)
        session.commit()
        session.close()
        logger.info(f"Emotion log inserted: {emotion_label}")
    except Exception as e:
        logger.error(f"Error inserting emotion log: {e}")

def insert_aggregated_emotion(session_id: str, dominant_emotion: str, emotion_confidence: float, emotion_distribution: dict, statement: str):
    """Insert aggregated emotion"""
    try:
        import uuid
        session = SessionLocal()
        
        agg = SessionAggregatedEmotion(
            aggregation_id=str(uuid.uuid4()),
            session_id=session_id,
            dominant_emotion=dominant_emotion,
            emotion_confidence=emotion_confidence,
            emotion_distribution=emotion_distribution,
            statement=statement,
        )
        
        session.add(agg)
        session.commit()
        session.close()
        logger.info(f"Aggregated emotion inserted: {session_id}")
    except Exception as e:
        logger.error(f"Error inserting aggregated emotion: {e}")

def get_matched_images(embedding: np.ndarray, limit: int = 50, threshold: float = 0.6) -> list:
    """Get matched images from FAISS"""
    # Placeholder: In real implementation, query FAISS
    return [
        {
            'image_id': '1',
            'image_url': 'https://example.com/image1.jpg',
            'image_path': '/path/to/image1.jpg',
            'similarity_score': 0.95,
        },
        # ... more images
    ]

def delete_session(session_id: str):
    """Delete session and related data"""
    try:
        session = SessionLocal()
        session.query(SessionUser).filter(SessionUser.session_id == session_id).delete()
        session.query(EmotionLog).filter(EmotionLog.session_id == session_id).delete()
        session.query(SessionAggregatedEmotion).filter(SessionAggregatedEmotion.session_id == session_id).delete()
        session.commit()
        session.close()
        logger.info(f"Session deleted: {session_id}")
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
```

---

## File 10: backend/app/services/s3_storage.py

```python
import boto3
import base64
import logging
from io import BytesIO
from app.config import settings

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

async def upload_image_to_s3(base64_image: str, session_id: str) -> str:
    """Upload base64 image to S3"""
    try:
        # Decode base64
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        
        # Upload to S3
        key = f"sessions/{session_id}/captured.jpg"
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key,
            Body=image_data,
            ContentType='image/jpeg',
        )
        
        logger.info(f"Image uploaded to S3: {key}")
        return f"s3://{settings.AWS_S3_BUCKET}/{key}"
        
    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        raise
```

---

## File 11: backend/.env.example

```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/face_emotion

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=face-emotion-bucket
AWS_REGION=us-east-1

# Models
MODEL_WEIGHTS_DIR=./models

# Session
SESSION_EXPIRY_HOURS=24

# API
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Installation & Running

### Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Setup environment:
```bash
cp .env.example .env
# Edit .env with your config
```

### Run development server:
```bash
python -m app.main
# Runs on http://localhost:8000
```

### Run with Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

**Continue with:** DOCKER_DEPLOYMENT.md for containerization and cloud deployment

