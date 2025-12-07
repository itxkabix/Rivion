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
