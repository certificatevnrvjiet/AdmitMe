import axios from 'axios';

const API = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Function to get image URL from backend
export const getImageUrl = (fileId, token) => {
  if (!fileId) return null;
  return {
    url: `${API.defaults.baseURL}/image/${fileId}`,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  };
};

export default API;
