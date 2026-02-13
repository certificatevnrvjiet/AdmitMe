from typing import Dict
from fastapi import WebSocket

# Store active WebSocket connections: {username: websocket}
active_connections: Dict[str, WebSocket] = {}

async def register_connection(username: str, websocket: WebSocket):
    await websocket.accept()
    active_connections[username] = websocket

def remove_connection(username: str):
    if username in active_connections:
        del active_connections[username]

async def notify_user(username: str, message: dict):
    websocket = active_connections.get(username)
    if websocket:
        await websocket.send_json(message)
