from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.transcription_service import transcribe_and_save, get_meeting_transcriptions
from app.services.insight_generator import generate_and_save
from typing import Dict, List

router = APIRouter()
sessions = {}

# --- Chat WebSocket ---
chat_connections = {}

@router.websocket("/ws/chat/{meeting_id}")
async def ws_chat(ws: WebSocket, meeting_id: str):
    await ws.accept()
    if meeting_id not in chat_connections:
        chat_connections[meeting_id] = []
    chat_connections[meeting_id].append(ws)
    try:
        while True:
            data = await ws.receive_json()
            # Broadcast to all in the room
            for conn in chat_connections[meeting_id]:
                if conn != ws:
                    await conn.send_json({"type": "chat", "user": data.get("user"), "message": data.get("message")})
    except WebSocketDisconnect:
        chat_connections[meeting_id].remove(ws)
        if not chat_connections[meeting_id]:
            del chat_connections[meeting_id]

# --- Audio WebSocket (existing) ---
@router.websocket("/ws/audio/{meeting_id}")
async def ws_audio(ws: WebSocket, meeting_id: str):
    await ws.accept()
    from app.services.transcription_service import transcribe_and_save
    try:
        while True:
            chunk = await ws.receive_bytes()
            from app.services.audio_processor import audio_processor
            await audio_processor.save_audio_chunk(meeting_id, chunk)
            # Transcribe and save after each chunk (real-time)
            try:
                await transcribe_and_save(meeting_id)
            except Exception:
                pass
    except:
        # On disconnect, do nothing (transcription is already up-to-date)
        pass

# --- Summary WebSocket ---
summary_connections = {}

@router.websocket("/ws/summary/{meeting_id}")
async def ws_summary(ws: WebSocket, meeting_id: str):
    await ws.accept()
    if meeting_id not in summary_connections:
        summary_connections[meeting_id] = []
    summary_connections[meeting_id].append(ws)
    try:
        while True:
            await ws.receive_text()  # Keep connection alive, but ignore messages
    except WebSocketDisconnect:
        summary_connections[meeting_id].remove(ws)
        if not summary_connections[meeting_id]:
            del summary_connections[meeting_id]

# Utility function to broadcast summary to all clients
async def broadcast_summary(meeting_id: str, summary_data: dict):
    if meeting_id in summary_connections:
        for ws in summary_connections[meeting_id]:
            try:
                await ws.send_json({"type": "summary", **summary_data})
            except Exception:
                pass

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_summary(self, room_id: str, summary: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json({"type": "summary", **summary})
                except Exception as e:
                    print(f"Error sending summary: {e}")
                    continue

manager = ConnectionManager()
