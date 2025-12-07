import React, { useState, useEffect } from 'react';
import FaceCaptureComponent from './components/FaceCaptureComponent';
import MetadataFormComponent from './components/MetadataFormComponent';
import ResultsComponent from './components/ResultsComponent';
import { searchFaces, healthCheck } from './utils/api';

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
                        className={`flex-1 h-1 rounded-full transition ${stage === 'capture' || stage === 'form' || stage === 'results'
                                ? 'bg-teal-500'
                                : 'bg-gray-300'
                            }`}
                    ></div>
                    <div className="mx-2"></div>
                    <div
                        className={`flex-1 h-1 rounded-full transition ${stage === 'form' || stage === 'results' ? 'bg-teal-500' : 'bg-gray-300'
                            }`}
                    ></div>
                    <div className="mx-2"></div>
                    <div
                        className={`flex-1 h-1 rounded-full transition ${stage === 'results' ? 'bg-teal-500' : 'bg-gray-300'
                            }`}
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
