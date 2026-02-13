from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from GoogleService import get_drive_service, get_sheets_service
from config.settings import FRONTEND_URL
from routers import auth, students, sync
from services.notification_service import register_connection, remove_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        app.state.sheets_service = get_sheets_service()
        app.state.drive_service = get_drive_service()
        logger.info("Google Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Google Services: {e}")
        app.state.sheets_service = None
        app.state.drive_service = None
    
    yield
    # Shutdown logic
    logger.info("Shutting down")

app = FastAPI(lifespan=lifespan, title="AdmitMe API")

# CORS configuration
ORIGINS = [
    FRONTEND_URL, 
    "http://localhost:5173", 
    "http://192.168.37.250:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(students.router, tags=["Students"])
app.include_router(sync.router, tags=["Sync"])

@app.get("/")
def read_root():
    return {"message": "AdmitMe API is running"}

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await register_connection(username, websocket)
    try:
        while True:
            # Keep the connection alive and listen for any client messages if needed
            data = await websocket.receive_text()
            # Echo or process if needed, for now just keep alive
    except WebSocketDisconnect:
        remove_connection(username)