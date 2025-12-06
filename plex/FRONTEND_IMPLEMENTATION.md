# FRONTEND - Complete React Implementation

## File 1: frontend/package.json

```json
{
  "name": "face-emotion-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext js,jsx"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "uuid": "^9.0.0",
    "@tensorflow/tfjs": "^4.10.0",
    "@tensorflow-models/blazeface": "^0.0.7",
    "recharts": "^2.10.0",
    "react-hook-form": "^7.48.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.1.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## File 2: frontend/src/utils/api.js

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for emotion analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens if needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const searchFaces = async (payload) => {
  try {
    const response = await api.post('/api/v1/search', payload);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Search failed');
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    throw new Error('Backend unreachable');
  }
};

export default api;
```

---

## File 3: frontend/src/components/FaceCaptureComponent.jsx

```javascript
import React, { useRef, useEffect, useState } from 'react';
import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';

const FaceCaptureComponent = ({ onCapture }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [model, setModel] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeCamera = async () => {
      try {
        setLoading(true);

        // Load Blazeface model
        const blazeFaceModel = await blazeface.load();
        setModel(blazeFaceModel);

        // Access webcam
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        setLoading(false);
      } catch (err) {
        setError('Camera access denied or not available');
        console.error('Error initializing camera:', err);
        setLoading(false);
      }
    };

    initializeCamera();
  }, []);

  useEffect(() => {
    if (!model || !videoRef.current) return;

    let animationId;

    const detectFaces = async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        // Draw video to canvas
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Detect faces
        const predictions = await model.estimateFaces(video, false);

        if (predictions.length > 0) {
          setFaceDetected(true);

          // Draw bounding box around face
          const face = predictions[0];
          const start = face.start;
          const end = face.end;
          const width = end[0] - start[0];
          const height = end[1] - start[1];

          // Green bounding box
          ctx.strokeStyle = '#00FF00';
          ctx.lineWidth = 3;
          ctx.strokeRect(start[0], start[1], width, height);

          // Draw landmarks
          ctx.fillStyle = '#00FF00';
          face.landmarks.forEach((landmark) => {
            ctx.beginPath();
            ctx.arc(landmark[0], landmark[1], 5, 0, 2 * Math.PI);
            ctx.fill();
          });
        } else {
          setFaceDetected(false);
        }
      }

      animationId = requestAnimationFrame(detectFaces);
    };

    detectFaces();

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [model]);

  const handleCapture = () => {
    if (!canvasRef.current || !faceDetected) {
      alert('Please ensure your face is visible in the camera');
      return;
    }

    const base64Image = canvasRef.current.toDataURL('image/jpeg', 0.9);
    onCapture(base64Image);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
        <p className="mt-4 text-gray-600">Loading camera...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <video
          ref={videoRef}
          className="hidden"
          autoPlay
          playsInline
        />
        <canvas
          ref={canvasRef}
          className="border-2 border-gray-300 rounded-lg max-w-md"
        />
        {!faceDetected && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-500 bg-opacity-20 rounded-lg">
            <p className="text-white text-lg font-bold">Face not detected</p>
          </div>
        )}
      </div>

      <div className="text-center">
        <p className="text-gray-600 mb-2">
          {faceDetected ? '✅ Face detected!' : '❌ Please face the camera'}
        </p>
      </div>

      <button
        onClick={handleCapture}
        disabled={!faceDetected}
        className={`px-6 py-3 rounded-lg font-semibold text-white transition ${
          faceDetected
            ? 'bg-teal-500 hover:bg-teal-600 cursor-pointer'
            : 'bg-gray-400 cursor-not-allowed'
        }`}
      >
        📸 Capture Face
      </button>
    </div>
  );
};

export default FaceCaptureComponent;
```

---

## File 4: frontend/src/components/MetadataFormComponent.jsx

```javascript
import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { v4 as uuidv4 } from 'uuid';

const MetadataFormComponent = ({ capturedImage, onSearch, isLoading }) => {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [privacyAgreed, setPrivacyAgreed] = useState(false);

  const onSubmit = async (data) => {
    if (!privacyAgreed) {
      alert('Please agree to the privacy policy');
      return;
    }

    const payload = {
      session_id: uuidv4(),
      user_name: data.userName,
      captured_image: capturedImage,
      privacy_policy_agreed: true,
      timestamp: new Date().toISOString(),
    };

    onSearch(payload);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-md">
      {/* Name Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Name
        </label>
        <input
          type="text"
          placeholder="Enter your full name"
          {...register('userName', {
            required: 'Name is required',
            minLength: { value: 2, message: 'Name must be at least 2 characters' },
          })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        {errors.userName && (
          <p className="text-red-500 text-sm mt-1">{errors.userName.message}</p>
        )}
      </div>

      {/* Privacy Policy */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={privacyAgreed}
            onChange={(e) => setPrivacyAgreed(e.target.checked)}
            className="mt-1 w-4 h-4 text-teal-500 rounded focus:ring-2 focus:ring-teal-500"
          />
          <span className="text-sm text-gray-700">
            I agree to the{' '}
            <a href="/privacy" className="text-teal-600 hover:underline">
              Privacy Policy
            </a>
            . I understand that my facial image will be temporarily stored for analysis and automatically deleted after 24 hours.
          </span>
        </label>
      </div>

      {/* Search Button */}
      <button
        type="submit"
        disabled={isLoading || !privacyAgreed}
        className={`w-full px-4 py-3 rounded-lg font-semibold text-white transition ${
          isLoading || !privacyAgreed
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-teal-500 hover:bg-teal-600 cursor-pointer'
        }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="animate-spin h-4 w-4 border-b-2 border-white"></div>
            Searching...
          </span>
        ) : (
          '🔍 Search Photos'
        )}
      </button>
    </form>
  );
};

export default MetadataFormComponent;
```

---

## File 5: frontend/src/components/ResultsComponent.jsx

```javascript
import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const ResultsComponent = ({ results }) => {
  if (!results) {
    return <div>Loading results...</div>;
  }

  const { matched_count, matched_images, aggregated_state, statement } = results;

  // Prepare emotion distribution data
  const emotionData = Object.entries(aggregated_state.distribution).map(
    ([emotion, percentage]) => ({
      name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
      value: Math.round(percentage * 100),
    })
  );

  const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];

  const emotionEmoji = {
    happy: '😊',
    sad: '😢',
    angry: '😠',
    neutral: '😐',
    fear: '😨',
    surprise: '😲',
    disgust: '🤢',
  };

  const dominantEmotion = aggregated_state.dominant_emotion;
  const confidence = (aggregated_state.emotion_confidence * 100).toFixed(1);

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      {/* Success Message */}
      <div className="bg-green-50 border border-green-200 p-6 rounded-lg">
        <h2 className="text-2xl font-bold text-green-800 mb-2">✅ Analysis Complete</h2>
        <p className="text-green-700">Found {matched_count} matching images</p>
      </div>

      {/* Dominant Emotion */}
      <div className="bg-gradient-to-r from-teal-50 to-blue-50 p-8 rounded-lg border border-teal-200">
        <div className="text-center">
          <div className="text-6xl mb-4">{emotionEmoji[dominantEmotion] || '😊'}</div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            {dominantEmotion.toUpperCase()}
          </h1>
          <p className="text-2xl text-gray-600 font-semibold">{confidence}% Confidence</p>
          <p className="text-lg text-gray-700 mt-4">{statement}</p>
        </div>
      </div>

      {/* Emotion Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Bar Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Emotion Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={emotionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `${value}%`} />
              <Bar dataKey="value" fill="#4ECDC4" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Emotion Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={emotionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {emotionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Matched Images Grid */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Matched Images</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {matched_images.slice(0, 12).map((image, idx) => (
            <div
              key={idx}
              className="bg-gray-100 rounded-lg overflow-hidden border border-gray-300 hover:shadow-lg transition"
            >
              <img
                src={image.image_url}
                alt={`Match ${idx}`}
                className="w-full h-32 object-cover"
              />
              <div className="p-2 bg-white">
                <p className="text-sm font-semibold">
                  {emotionEmoji[image.emotion]} {image.emotion}
                </p>
                <p className="text-xs text-gray-600">
                  {(image.emotion_confidence * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-gray-500">
                  Match: {(image.similarity_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-center">
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 font-semibold"
        >
          🔄 New Search
        </button>
        <button
          onClick={() => alert('Download report feature coming soon!')}
          className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 font-semibold"
        >
          📥 Download Report
        </button>
      </div>
    </div>
  );
};

export default ResultsComponent;
```

---

## File 6: frontend/src/App.jsx

```javascript
import React, { useState, useEffect } from 'react';
import FaceCaptureComponent from './components/FaceCaptureComponent';
import MetadataFormComponent from './components/MetadataFormComponent';
import ResultsComponent from './components/ResultsComponent';
import { searchFaces, healthCheck } from './utils/api';
import './App.css';

function App() {
  const [stage, setStage] = useState('capture'); // capture, form, results
  const [capturedImage, setCapturedImage] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendOnline, setBackendOnline] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await healthCheck();
        setBackendOnline(true);
      } catch (err) {
        setBackendOnline(false);
        console.error('Backend offline:', err);
      }
    };

    checkBackend();
  }, []);

  const handleCapture = (base64Image) => {
    setCapturedImage(base64Image);
    setStage('form');
  };

  const handleSearch = async (payload) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await searchFaces(payload);
      setResults(response);
      setStage('results');
    } catch (err) {
      setError(err.message || 'Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            😊 Face Emotion Analyzer
          </h1>
          <p className="text-gray-600">
            Capture your face and discover your emotional state
          </p>
          {!backendOnline && (
            <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
              ⚠️ Backend offline. Please ensure the server is running.
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="flex justify-between mb-8 max-w-md mx-auto">
          <div
            className={`flex-1 h-1 ${
              stage === 'capture' || stage === 'form' || stage === 'results'
                ? 'bg-teal-500'
                : 'bg-gray-300'
            } rounded-full`}
          ></div>
          <div className="mx-2"></div>
          <div
            className={`flex-1 h-1 ${
              stage === 'form' || stage === 'results' ? 'bg-teal-500' : 'bg-gray-300'
            } rounded-full`}
          ></div>
          <div className="mx-2"></div>
          <div
            className={`flex-1 h-1 ${
              stage === 'results' ? 'bg-teal-500' : 'bg-gray-300'
            } rounded-full`}
          ></div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          {error && (
            <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {stage === 'capture' && (
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Step 1: Capture Your Face
              </h2>
              <FaceCaptureComponent onCapture={handleCapture} />
            </div>
          )}

          {stage === 'form' && (
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Step 2: Enter Your Details
              </h2>
              <MetadataFormComponent
                capturedImage={capturedImage}
                onSearch={handleSearch}
                isLoading={isLoading}
              />
            </div>
          )}

          {stage === 'results' && (
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Step 3: Your Results
              </h2>
              <ResultsComponent results={results} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-gray-600 text-sm">
          <p>
            🔒 Your facial data is temporary and auto-deleted after 24 hours
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
```

---

## File 7: frontend/tailwind.config.js

```javascript
export default {
  content: ['./src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        teal: {
          50: '#f0fdfa',
          500: '#14b8a6',
          600: '#0d9488',
        },
      },
    },
  },
  plugins: [],
};
```

---

## Installation & Running

### Install dependencies:
```bash
cd frontend
npm install
```

### Start development server:
```bash
npm run dev
# Runs on http://localhost:3000
```

### Build for production:
```bash
npm run build
```

---

**Next:** Create BACKEND_IMPLEMENTATION.md for FastAPI services

