from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from sqlmodel import select, Session
from app.db import engine
from app.models.transcription import Transcription
from app.services.transcription_service import transcribe_and_save, get_meeting_transcriptions
import logging
import io
import os

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{meeting_id}")
async def get_meeting_transcriptions_endpoint(meeting_id: str):
    """Get all transcriptions for a meeting"""
    try:
        transcriptions = await get_meeting_transcriptions(meeting_id)
        return transcriptions
    except Exception as e:
        logger.error(f"Failed to get transcriptions for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.post("/{meeting_id}/upload")
async def upload_audio_and_transcribe(
    meeting_id: str, 
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload audio file and transcribe it"""
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(400, "File must be an audio file")
        
        # Save uploaded file as recordings/{meeting_id}_all.webm
        recordings_dir = "recordings"
        os.makedirs(recordings_dir, exist_ok=True)
        file_path = os.path.join(recordings_dir, f"{meeting_id}_all.webm")
        with open(file_path, "wb") as f:
            f.write(await audio_file.read())
        
        # Process transcription
        transcription = await transcribe_and_save(meeting_id)
        
        return {
            "message": "Audio uploaded and transcribed successfully",
            "transcription_id": transcription.id,
            "content_length": len(transcription.content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process audio for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Failed to process audio")

@router.post("/{meeting_id}/process")
async def process_meeting_audio(
    meeting_id: str,
    background_tasks: BackgroundTasks
):
    """Process meeting audio and generate transcription"""
    try:
        # This would typically be called after a meeting ends
        # For now, we'll return a placeholder response
        return {
            "message": "Audio processing started",
            "meeting_id": meeting_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start audio processing for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Failed to start audio processing")

@router.delete("/{meeting_id}")
async def delete_meeting_transcriptions_endpoint(meeting_id: str):
    """Delete all transcriptions for a meeting"""
    try:
        from app.services.transcription_service import delete_meeting_transcriptions
        await delete_meeting_transcriptions(meeting_id)
        return {"message": "Transcriptions deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete transcriptions for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")
