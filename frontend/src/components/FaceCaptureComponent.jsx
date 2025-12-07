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
                className={`px-6 py-3 rounded-lg font-semibold text-white transition ${faceDetected
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
