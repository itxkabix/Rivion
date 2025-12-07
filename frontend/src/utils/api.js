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
