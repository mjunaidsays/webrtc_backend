import asyncio
import os
import uuid
# import whisper  # Remove whisper import
import numpy as np
from datetime import datetime
from typing import Optional, List
import aiofiles
from pydub import AudioSegment
from pydub.utils import make_chunks
import tempfile
import logging
import subprocess
from deepgram import Deepgram

logger = logging.getLogger(__name__)

DEEPGRAM_API_KEY = "cbfbec93d0b50d7c430a3f5d71ca3fed751f8046"

dg_client = Deepgram(DEEPGRAM_API_KEY)

class AudioProcessor:
    def __init__(self):
        self.recordings_dir = "recordings"
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.recordings_dir, exist_ok=True)
        os.makedirs("temp", exist_ok=True)
    
    async def save_audio_chunk(self, meeting_id: str, audio_data: bytes) -> str:
        """Append an audio chunk to the meeting's .webm file."""
        webm_filepath = os.path.join(self.recordings_dir, f"{meeting_id}_all.webm")
        async with aiofiles.open(webm_filepath, 'ab') as f:
            await f.write(audio_data)
        # Log file size after saving chunk
        try:
            size = os.path.getsize(webm_filepath)
            logger.info(f"[AUDIO] Saved chunk for meeting {meeting_id}: {webm_filepath} (size: {size} bytes)")
        except Exception as e:
            logger.warning(f"[AUDIO] Could not get file size for {webm_filepath}: {e}")
        return webm_filepath

    async def transcode_meeting_audio(self, meeting_id: str) -> str:
        """Transcode the concatenated .webm file to .wav after meeting ends."""
        webm_filepath = os.path.join(self.recordings_dir, f"{meeting_id}_all.webm")
        wav_filepath = os.path.join(self.recordings_dir, f"{meeting_id}_all.wav")
        logger.info(f"[AUDIO] Starting transcoding for meeting {meeting_id}: {webm_filepath} -> {wav_filepath}")
        cmd = [
            'ffmpeg', '-y', '-i', webm_filepath,
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', wav_filepath
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"[AUDIO] Transcoding complete for meeting {meeting_id}: {wav_filepath}")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error (webm->wav): {e.stderr}")
            raise
        return wav_filepath

    async def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> dict:
        """Transcribe audio using Deepgram API"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        try:
            with open(audio_path, "rb") as audio_file:
                source = {"buffer": audio_file, "mimetype": "audio/wav"}
                options = {"punctuate": True, "language": language or "en"}
                response = await dg_client.transcription.prerecorded(source, options)
                if not response or "results" not in response or not response["results"].get("channels"):
                    logger.error(f"Deepgram returned no results for {audio_path}: {response}")
                    return {"text": "", "segments": [], "language": language or "en"}
                try:
                    transcript = response["results"]["channels"][0]["alternatives"][0].get("transcript", "")
                except Exception as e:
                    logger.error(f"Error parsing Deepgram response: {e}, response: {response}")
                    transcript = ""
                return {
                    "text": transcript,
                    "segments": [],
                    "language": language or "en"
                }
        except Exception as e:
            logger.error(f"Deepgram transcription failed: {e}")
            logger.error(f"Full Deepgram response: {locals().get('response', None)}")
            raise

    async def process_meeting_audio(self, meeting_id: str) -> dict:
        """Transcode and transcribe the full meeting audio after all chunks are received."""
        try:
            # Transcode the full .webm file to .wav
            wav_path = await self.transcode_meeting_audio(meeting_id)
            # Transcribe
            transcription_result = await self.transcribe_audio(wav_path)
            # Clean up files
            try:
                os.remove(wav_path)
            except OSError:
                pass
            try:
                os.remove(os.path.join(self.recordings_dir, f"{meeting_id}_all.webm"))
            except OSError:
                pass
            return transcription_result
        except Exception as e:
            logger.error(f"Audio processing failed for meeting {meeting_id}: {e}")
            raise

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0

# Global instance
audio_processor = AudioProcessor() 