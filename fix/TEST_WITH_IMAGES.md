# 🎯 TEST YOUR SYSTEM WITH REAL IMAGES

## Problem
App shows "Not Found" - need to:
1. Replace backend search endpoint
2. Test with real images
3. Verify emotion analysis works

---

## ✅ Step 1: Update Backend Search Route

Replace: `backend/app/routes/search.py`

With: `search_updated.py` (download this file)

---

## 📝 Key Endpoints Created

### 1. **POST /api/v1/analyze-face**
Analyzes uploaded face image

```bash
curl -X POST http://localhost:8000/api/v1/analyze-face \
  -F "image=@your_image.jpg" \
  -F "user_name=Kabir" \
  -F "privacy_agreed=true"
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "faces_detected": 1,
  "dominant_emotion": "happy",
  "emotion_confidence": 0.95,
  "all_emotions": {
    "happy": 0.95,
    "sad": 0.02,
    "angry": 0.01,
    ...
  },
  "statement": "You look happy and cheerful! 😊 (Confidence: 95%)",
  "similar_faces": [...],
  "captured_at": "2025-12-07T...",
  "image_path": "uploads/sessions/uuid/image.jpg"
}
```

### 2. **POST /api/v1/search**
Search for similar faces in database

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -F "image=@your_image.jpg" \
  -F "user_name=Kabir"
```

### 3. **GET /api/v1/sessions/{session_id}**
Get session details

```bash
curl http://localhost:8000/api/v1/sessions/your-session-id
```

---

## 🧪 Test with Your Images

### Using Postman/Insomnia:

1. **Create new POST request**
   - URL: `http://localhost:8000/api/v1/analyze-face`

2. **Body - form-data:**
   - `image` (file) - select your image
   - `user_name` (text) - "Kabir" or your name
   - `privacy_agreed` (boolean) - true

3. **Send**

4. **See Response:**
   - ✅ Session created
   - ✅ Emotion analyzed
   - ✅ Similar faces found
   - ✅ Statement generated

---

## 🎬 Frontend Flow

### When You Upload Face in App:

```
1. Capture face from camera
   ↓
2. Frontend converts to base64
   ↓
3. Frontend sends to /api/v1/analyze-face
   ↓
4. Backend:
   - Detects faces
   - Analyzes emotions
   - Saves to database
   - Searches for similar faces
   ↓
5. Returns results
   ↓
6. App displays:
   - Dominant emotion
   - Confidence score
   - All emotions breakdown
   - Emotion statement
   - Similar faces found
```

---

## 📊 What Gets Stored

### Database:
- ✅ Session info (user_name, timestamp, expires_at)
- ✅ Emotion logs (emotion, confidence, distribution)
- ✅ Aggregated emotion (final result)

### File Storage:
- ✅ Original image: `uploads/sessions/{session_id}/`
- ✅ Face crops: `uploads/faces/{session_id}/`
- ✅ Auto-deleted: After 24 hours

---

## 🔧 Installation

```bash
# 1. Replace search.py
cp search_updated.py backend/app/routes/search.py

# 2. Install Pillow if not already installed
cd backend
pip install Pillow

# 3. Restart backend
python -m app.main
```

---

## ✅ Verification Checklist

- [ ] Backend starts without errors
- [ ] GET `/api/health` returns 200 OK
- [ ] Can upload image via `/api/v1/analyze-face`
- [ ] Gets emotion analysis response
- [ ] Emotion saved to database
- [ ] Session ID generated
- [ ] Similar faces searched (may be empty on first run)
- [ ] Images saved to `backend/uploads/`

---

## 🎨 Emotions Detected

Your system can detect:
- 😊 **Happy** - cheerful, smiling
- 😔 **Sad** - unhappy, sorrowful
- 😠 **Angry** - frustrated, annoyed
- 😟 **Fearful** - scared, anxious
- 😮 **Surprised** - shocked, amazed
- 😕 **Disgusted** - repulsed
- 😐 **Neutral** - calm, expressionless

---

## 📸 Test Image Requirements

**Good images:**
- ✅ Clear face visible
- ✅ Good lighting
- ✅ Face 30-50% of image
- ✅ Looking at camera
- ✅ JPG or PNG format

**Bad images:**
- ❌ Face too small/far
- ❌ Multiple faces (use first one)
- ❌ Poor lighting
- ❌ Face turned away
- ❌ Glasses/hats covering face

---

## 🚀 Quick Test

```bash
# In new terminal
cd backend

# 1. Start backend
python -m app.main

# 2. In another terminal, test endpoint
curl -X POST http://localhost:8000/api/v1/analyze-face \
  -F "image=@/path/to/your/image.jpg" \
  -F "user_name=TestUser" \
  -F "privacy_agreed=true"

# Should return JSON with emotion analysis!
```

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| 404 Not Found | Download `search_updated.py` and replace file |
| File upload error | Check image format (JPG/PNG) and size |
| No faces detected | Use clear face image, good lighting |
| Emotion always "neutral" | Check if face is visible in image |
| Timeout | Check if face detection models loaded (takes time) |

---

## 📞 Next Steps

1. ✅ Update search.py
2. ✅ Restart backend
3. ✅ Test with your images
4. ✅ Verify emotions are correct
5. ✅ Check database has records
6. ✅ Test similarity search

---

**Ready to test!** Download `search_updated.py` and follow installation steps! 🎉
