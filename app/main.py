from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.config import settings
from app.routers import meetings, transcriptions, insights
from app.services.websocket_manager import router as ws_router
from app.db import engine
from app.routers.jaas import router as jaas_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://webrtc-frontend-two.vercel.app",  # Vercel deployment
        "http://localhost:3000",                     # Local development
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

app.include_router(meetings.router, prefix="/api/meetings")
app.include_router(transcriptions.router, prefix="/api/transcriptions")
app.include_router(insights.router, prefix="/api/insights")
app.include_router(ws_router)
app.include_router(jaas_router, prefix='/api/jaas-jwt')
