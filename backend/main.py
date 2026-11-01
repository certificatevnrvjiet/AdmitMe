from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from GoogleService import get_drive_service, get_sheets_service
from config.settings import FRONTEND_URL, LOCAL_STORAGE_ROOT, SECRET_KEY, ALGORITHM
from routers import auth, students, sync, applications, engines, forms
from services.notification_service import register_connection, remove_connection
from storage import get_storage_provider
from storage.gdrive import GoogleDriveStorageProvider
from storage.local import LocalStorageProvider
from jose import jwt, JWTError
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    app.state.sheets_service = None
    app.state.drive_service = None
    local_provider = LocalStorageProvider(LOCAL_STORAGE_ROOT)
    storage_providers = {"local": local_provider}

    try:
        app.state.sheets_service = get_sheets_service()
        app.state.drive_service = get_drive_service()
        logger.info("Google Services initialized successfully")
    except Exception as e:
        logger.warning(f"Google services unavailable: {e}")

    if app.state.drive_service:
        storage_providers["gdrive"] = GoogleDriveStorageProvider(app.state.drive_service)

    # Explicitly fail startup for unsupported/misconfigured provider setups.
    app.state.storage = get_storage_provider(app.state.drive_service)
    storage_providers[app.state.storage.name] = app.state.storage
    app.state.storage_providers = storage_providers

    try:
        from services.gemini_batch_service import resume_unfinished_batch_jobs

        asyncio.create_task(resume_unfinished_batch_jobs(app))
    except Exception as e:
        logger.warning(f"Could not schedule Gemini batch resume: {e}")
    
    yield
    # Shutdown logic
    logger.info("Shutting down")

app = FastAPI(lifespan=lifespan, title="AdmitMe API")

# CORS configuration
ORIGINS = [
    origin
    for origin in {
        FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.37.250:5173",
    }
    if origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(students.router, tags=["Students"])
app.include_router(sync.router, tags=["Sync"])
app.include_router(applications.router, tags=["Applications"])
app.include_router(engines.router, tags=["Engines"])
app.include_router(forms.router, tags=["Forms"])

@app.get("/")
def read_root():
    return {"message": "AdmitMe API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = (payload.get("sub") or "").strip().lower()
        if not username:
            raise JWTError("Missing subject")
    except Exception:
        await websocket.close(code=1008)
        return

    await register_connection(username, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        remove_connection(username)
