"""
Backend API endpoint for face emotion detection
Handles face capture, emotion analysis, and similarity search
Compatible with existing emotion.py and services
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import base64
import io
import uuid
from datetime import datetime
import logging
from PIL import Image
import numpy as np
import os

# Import your existing services (matching your actual code)
from app.services.emotion import analyze_emotion, aggregate_emotions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["face-emotion"])

# ==================== FACE CAPTURE & ANALYSIS ====================

@router.post("/analyze-face")
async def analyze_face(
    image: UploadFile = File(...),
    user_name: str = Form(...),
    privacy_agreed: bool = Form(...)
):
    """
    Analyze face from uploaded image
    
    Args:
        image: Uploaded image file (JPG/PNG)
        user_name: User's name
        privacy_agreed: Privacy policy agreement
    
    Returns:
        JSON with emotion analysis results
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Read image file
        image_data = await image.read()
        
        # Save temporary image file
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_image_path = os.path.join(temp_dir, f"{session_id}.jpg")
        
        # Write image to temp file
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)
        
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        logger.info(f"Processing image for session: {session_id}")
        
        # Analyze emotion using existing function
        dominant_emotion, emotion_dist, confidence = analyze_emotion(temp_image_path)
        
        if dominant_emotion == 'neutral' and confidence == 0.0:
            logger.warning(f"Emotion analysis failed for session {session_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Could not analyze image. Please ensure it contains a clear face.",
                    "session_id": session_id
                }
            )
        
        logger.info(f"Emotion analysis for session {session_id}: {dominant_emotion} ({confidence*100:.1f}%)")
        
        # Generate emotion statement
        emotion_statement = generate_emotion_statement(dominant_emotion, confidence)
        
        # Prepare response
        response_data = {
            "success": True,
            "session_id": session_id,
            "user_name": user_name,
            "dominant_emotion": dominant_emotion,
            "emotion_confidence": float(confidence),
            "all_emotions": emotion_dist,
            "statement": emotion_statement,
            "captured_at": datetime.utcnow().isoformat(),
            "image_base64": base64_image,
            "temp_image_path": temp_image_path
        }
        
        logger.info(f"Analysis complete for session {session_id}")
        
        # Clean up temp file
        try:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file: {e}")
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error analyzing face: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error processing image: {str(e)}"
            }
        )


@router.post("/search")
async def search_faces(
    image: UploadFile = File(...),
    user_name: str = Form(...)
):
    """
    Search for similar faces and analyze emotion
    
    Args:
        image: Uploaded image file
        user_name: User's name for logging
    
    Returns:
        Emotion analysis and similar faces
    """
    try:
        image_data = await image.read()
        
        # Save temporary image file
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        session_id = str(uuid.uuid4())
        temp_image_path = os.path.join(temp_dir, f"{session_id}.jpg")
        
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Searching similar faces for user: {user_name}")
        
        # Analyze emotion
        dominant_emotion, emotion_dist, confidence = analyze_emotion(temp_image_path)
        
        if dominant_emotion == 'neutral' and confidence == 0.0:
            logger.warning(f"Analysis failed for user {user_name}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Could not analyze image",
                    "similar_faces": []
                }
            )
        
        logger.info(f"Found emotion: {dominant_emotion}")
        
        emotion_statement = generate_emotion_statement(dominant_emotion, confidence)
        
        # For now, return empty similar faces (implement with vector DB later)
        similar_faces = []
        
        response_data = {
            "success": True,
            "user_name": user_name,
            "session_id": session_id,
            "dominant_emotion": dominant_emotion,
            "emotion_confidence": float(confidence),
            "all_emotions": emotion_dist,
            "statement": emotion_statement,
            "similar_faces": similar_faces,
            "searched_at": datetime.utcnow().isoformat()
        }
        
        # Clean up temp file
        try:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file: {e}")
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error searching faces: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error searching: {str(e)}",
                "similar_faces": []
            }
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details by session ID"""
    try:
        logger.info(f"Fetching session: {session_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "session_id": session_id,
                "status": "Session retrieved successfully"
            }
        )
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error fetching session"}
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "face-emotion-analyzer",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ==================== HELPER FUNCTIONS ====================

def generate_emotion_statement(emotion: str, confidence: float) -> str:
    """
    Generate human-readable emotion statement
    
    Args:
        emotion: Emotion label ('happy', 'sad', 'angry', 'fear', 'neutral', 'disgust', 'surprise')
        confidence: Confidence score (0-1)
    
    Returns:
        Human-readable statement with emoji
    """
    emotion_descriptions = {
        "happy": "😊 You look happy and cheerful!",
        "sad": "😔 You seem to be feeling sad.",
        "angry": "😠 You appear to be feeling angry.",
        "fear": "😟 You seem fearful or anxious.",
        "surprise": "😮 You look surprised!",
        "disgust": "😕 You seem disgusted.",
        "neutral": "😐 Your expression is neutral.",
        "disgust": "😕 You seem disgusted."
    }
    
    confidence_pct = int(confidence * 100)
    base_statement = emotion_descriptions.get(emotion, "Your emotional state is unclear.")
    
    return f"{base_statement} (Confidence: {confidence_pct}%)"
