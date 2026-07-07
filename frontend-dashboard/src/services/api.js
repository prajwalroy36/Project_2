// src/services/api.js
import axios from 'axios';

// Connects to your FastAPI server
const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_FRONTEND_API_KEY || 'super_secret_dev_key_123';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
});

export const getOrders = async () => {
    const res = await apiClient.get('/api/dashboard/orders');
    return res.data.data;
};

export const getOrderDetails = async (db_id) => {
    const res = await apiClient.get(`/api/dashboard/orders/${db_id}`);
    return res.data.data;
};