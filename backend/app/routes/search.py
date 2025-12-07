from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import base64
from datetime import datetime
import logging
from app.services.vector_db import store_embedding, search_similar_faces, delete_session_vectors
from app.services.face_detection import detect_faces
from app.services.embedding import extract_embedding

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["search"])

class SearchRequest(BaseModel):
    image_base64: str
    user_name: str
    session_id: str

@router.post("/search")
async def search_faces(request: SearchRequest):
    """Search for similar faces using Pinecone"""
    
    try:
        # Decode image
        image_data = base64.b64decode(request.image_base64.split(',')[1])
        
        # Step 1: Detect faces
        faces = await detect_faces(image_data)
        if not faces:
            raise HTTPException(status_code=400, detail="No faces detected")
        
        # Step 2: Extract embedding from first face
        embedding = await extract_embedding(faces[0])
        
        # Step 3: Search Pinecone for similar faces
        similar_faces = await search_similar_faces(embedding, top_k=10)
        
        # Step 4: Store this embedding in Pinecone
        metadata = {
            "session_id": request.session_id,
            "user_name": request.user_name,
            "timestamp": str(datetime.now())
        }
        await store_embedding(request.session_id, embedding.tolist(), metadata)
        
        return {
            "status": "success",
            "similar_faces": similar_faces,
            "embedding_stored": True,
            "total_matches": len(similar_faces)
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Delete all data for a session (privacy)"""
    
    try:
        # Delete from Pinecone
        await delete_session_vectors(session_id)
        
        return {"status": "success", "message": f"Session {session_id} deleted"}
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
