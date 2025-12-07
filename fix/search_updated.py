"""
Backend API endpoint for face emotion detection
Handles face capture, emotion analysis, and similarity search
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

# Import your services
from app.services.database import insert_session_user, insert_emotion_log, insert_aggregated_emotion, get_matched_images
from app.services.face_detection import detect_faces
from app.services.emotion import analyze_emotions
from app.services.embedding import get_face_embedding
from app.services.image_storage import save_session_image, save_face_image
from app.config import settings

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
        image: Uploaded image file
        user_name: User's name
        privacy_agreed: Privacy policy agreement
    
    Returns:
        JSON with analysis results
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Read image file
        image_data = await image.read()
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to numpy array
        image_array = np.array(pil_image)
        
        # Convert to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        logger.info(f"Processing image for session: {session_id}")
        
        # Detect faces
        face_detections = detect_faces(image_array)
        
        if not face_detections:
            logger.warning(f"No faces detected in session {session_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "No face detected in the image. Please try again.",
                    "session_id": session_id
                }
            )
        
        logger.info(f"Found {len(face_detections)} face(s) in session {session_id}")
        
        # Analyze emotions for each face
        emotions_data = []
        face_embeddings = []
        
        for idx, face_img in enumerate(face_detections):
            # Emotion analysis
            emotion_result = analyze_emotions(face_img)
            emotions_data.append(emotion_result)
            
            # Get face embedding
            embedding = get_face_embedding(face_img)
            face_embeddings.append(embedding)
            
            logger.info(f"Emotion analysis for face {idx+1}: {emotion_result['dominant_emotion']}")
        
        # Save image to storage
        image_path = save_session_image(session_id, image_data)
        
        # Store in database
        try:
            insert_session_user(
                session_id=session_id,
                user_name=user_name,
                captured_image_base64=base64_image,
                privacy_policy_agreed=privacy_agreed
            )
            logger.info(f"Session user stored: {session_id}")
        except Exception as e:
            logger.error(f"Error storing session user: {e}")
        
        # Store emotion logs
        for idx, emotion in enumerate(emotions_data):
            try:
                face_id = f"{session_id}_face_{idx}"
                insert_emotion_log(
                    image_id=face_id,
                    session_id=session_id,
                    emotion_label=emotion['dominant_emotion'],
                    confidence=emotion['confidence'],
                    emotion_distribution=emotion['all_emotions']
                )
                logger.info(f"Emotion log stored for face {idx}")
            except Exception as e:
                logger.error(f"Error storing emotion log: {e}")
        
        # Get aggregated emotion
        aggregated = aggregate_emotions(emotions_data)
        
        # Store aggregated emotion
        try:
            insert_aggregated_emotion(
                session_id=session_id,
                dominant_emotion=aggregated['dominant_emotion'],
                emotion_confidence=aggregated['confidence'],
                emotion_distribution=aggregated['all_emotions'],
                statement=aggregated['statement']
            )
            logger.info(f"Aggregated emotion stored: {session_id}")
        except Exception as e:
            logger.error(f"Error storing aggregated emotion: {e}")
        
        # Search for similar faces in database
        if face_embeddings:
            try:
                similar_images = get_matched_images(
                    embedding=face_embeddings[0],
                    limit=5,
                    threshold=0.6
                )
                logger.info(f"Found {len(similar_images)} similar faces")
            except Exception as e:
                logger.warning(f"Error searching similar faces: {e}")
                similar_images = []
        else:
            similar_images = []
        
        # Return results
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "session_id": session_id,
                "user_name": user_name,
                "faces_detected": len(face_detections),
                "dominant_emotion": aggregated['dominant_emotion'],
                "emotion_confidence": float(aggregated['confidence']),
                "all_emotions": aggregated['all_emotions'],
                "statement": aggregated['statement'],
                "similar_faces": similar_images,
                "captured_at": datetime.utcnow().isoformat(),
                "image_path": image_path
            }
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
    Search for similar faces in database
    
    Args:
        image: Uploaded image file
        user_name: User's name for logging
    
    Returns:
        Similar faces from database
    """
    try:
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        image_array = np.array(pil_image)
        
        logger.info(f"Searching similar faces for user: {user_name}")
        
        # Detect faces
        face_detections = detect_faces(image_array)
        
        if not face_detections:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "No face detected",
                    "similar_faces": []
                }
            )
        
        # Get embedding for first face
        embedding = get_face_embedding(face_detections[0])
        
        # Search database
        similar_images = get_matched_images(
            embedding=embedding,
            limit=10,
            threshold=0.5
        )
        
        logger.info(f"Found {len(similar_images)} similar faces")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "user_name": user_name,
                "faces_detected": len(face_detections),
                "similar_faces": similar_images,
                "searched_at": datetime.utcnow().isoformat()
            }
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
        # Query database for session
        logger.info(f"Fetching session: {session_id}")
        
        # This would query your database
        # For now, return placeholder
        return JSONResponse(
            status_code=200,
            content={
                "session_id": session_id,
                "message": "Session details retrieved successfully"
            }
        )
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error fetching session"}
        )


# ==================== HELPER FUNCTIONS ====================

def aggregate_emotions(emotions_list):
    """
    Aggregate emotions from multiple faces
    
    Args:
        emotions_list: List of emotion results
    
    Returns:
        Aggregated emotion data
    """
    if not emotions_list:
        return {
            "dominant_emotion": "neutral",
            "confidence": 0.0,
            "all_emotions": {},
            "statement": "Unable to analyze emotion"
        }
    
    # If single face, return its emotion
    if len(emotions_list) == 1:
        emotion = emotions_list[0]
        return {
            "dominant_emotion": emotion['dominant_emotion'],
            "confidence": emotion['confidence'],
            "all_emotions": emotion['all_emotions'],
            "statement": generate_emotion_statement(emotion['dominant_emotion'], emotion['confidence'])
        }
    
    # If multiple faces, average emotions
    emotion_sums = {}
    for emotion_data in emotions_list:
        for emotion, value in emotion_data['all_emotions'].items():
            emotion_sums[emotion] = emotion_sums.get(emotion, 0) + value
    
    avg_emotions = {k: v / len(emotions_list) for k, v in emotion_sums.items()}
    dominant = max(avg_emotions.items(), key=lambda x: x[1])
    
    return {
        "dominant_emotion": dominant[0],
        "confidence": dominant[1],
        "all_emotions": avg_emotions,
        "statement": generate_emotion_statement(dominant[0], dominant[1])
    }


def generate_emotion_statement(emotion: str, confidence: float) -> str:
    """
    Generate human-readable emotion statement
    
    Args:
        emotion: Emotion label
        confidence: Confidence score (0-1)
    
    Returns:
        Human-readable statement
    """
    emotion_descriptions = {
        "happy": "You look happy and cheerful! 😊",
        "sad": "You seem to be feeling sad. 😔",
        "angry": "You appear to be feeling angry. 😠",
        "fearful": "You seem fearful or anxious. 😟",
        "surprised": "You look surprised! 😮",
        "disgusted": "You seem disgusted. 😕",
        "neutral": "Your expression is neutral. 😐"
    }
    
    confidence_pct = int(confidence * 100)
    base_statement = emotion_descriptions.get(emotion, "Your emotional state is unclear.")
    
    return f"{base_statement} (Confidence: {confidence_pct}%)"
