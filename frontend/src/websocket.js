// websocket.js
import API from './api';

export const createWebSocket = (path) => {
  const token = localStorage.getItem("token");
  if (!token) return null;

  // Convert API baseURL to WS protocol
  const baseWsUrl = API.defaults.baseURL.replace(/^http/, "ws");

  return new WebSocket(`${baseWsUrl}${path}?token=${token}`);
};
