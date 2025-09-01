// API.js
import axios from 'axios';

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const API = axios.create({
  baseURL: BASE_URL,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const getImageUrl = (fileId) => {
  if (!fileId) return null;
  return `${API.defaults.baseURL}/image/${fileId}`;
};

export default API;
