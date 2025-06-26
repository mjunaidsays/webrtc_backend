import uuid
import asyncio
from sqlmodel import Session
from app.db import engine
from app.models.transcription import Transcription
from app.services.audio_processor import audio_processor
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

async def transcribe_and_save(meeting_id: str) -> Transcription:
    """Transcribe the full meeting audio and save to database"""
    try:
        audio_file_path = f"recordings/{meeting_id}_all.wav"
        # Log audio file existence and size
        if not os.path.exists(audio_file_path):
            logger.warning(f"[TRANSCRIBE] Audio file missing for meeting {meeting_id}: {audio_file_path}")
        else:
            size = os.path.getsize(audio_file_path)
            logger.info(f"[TRANSCRIBE] Audio file for meeting {meeting_id}: {audio_file_path} ({size} bytes)")
            if size < 1000:
                logger.warning(f"[TRANSCRIBE] Audio file for meeting {meeting_id} is very small (likely empty)")
        # Process audio and get transcription
        transcription_result = await audio_processor.process_meeting_audio(meeting_id)
        logger.info(f"[TRANSCRIBE] Transcription result for meeting {meeting_id}: '{transcription_result['text'][:100]}'")
        if not (transcription_result["text"] or "").strip():
            logger.warning(f"[TRANSCRIBE] Empty transcription for meeting {meeting_id}")
        
        # Save transcription to database
        transcription = Transcription(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            content=transcription_result["text"],
            speaker=None,  # Whisper doesn't provide speaker identification by default
            timestamp=datetime.utcnow()
        )
        
        with Session(engine) as s:
            s.add(transcription)
            s.commit()
            s.refresh(transcription)
            
        logger.info(f"Transcription saved for meeting {meeting_id}")
        return transcription
        
    except Exception as e:
        logger.error(f"[TRANSCRIPTION ERROR] for meeting {meeting_id}: {e}", exc_info=True)
        return None

async def get_meeting_transcriptions(meeting_id: str) -> list:
    """Get all transcriptions for a meeting"""
    with Session(engine) as s:
        transcriptions = s.exec(
            Session.query(Transcription).where(Transcription.meeting_id == meeting_id)
        ).all()
    return transcriptions

async def delete_meeting_transcriptions(meeting_id: str):
    """Delete all transcriptions for a meeting"""
    with Session(engine) as s:
        s.exec(
            Session.query(Transcription).where(Transcription.meeting_id == meeting_id).delete()
        )
        s.commit() 