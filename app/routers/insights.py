from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from app.db import engine
from app.models.insight import Insight
from app.models.transcription import Transcription
from app.services.insight_generator import generate_insights_for_meeting
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{meeting_id}")
async def get_meeting_insights(meeting_id: str):
    """Get insights for a specific meeting"""
    try:
        with Session(engine) as s:
            insight = s.exec(
                select(Insight).where(Insight.meeting_id == meeting_id)
            ).first()
            
        if not insight:
            raise HTTPException(404, "Insights not found for this meeting")
            
        return insight
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insights for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.post("/{meeting_id}/generate")
async def generate_meeting_insights(meeting_id: str, background_tasks: BackgroundTasks):
    """Generate insights for a meeting (triggers background processing)"""
    try:
        # Check if insights already exist
        with Session(engine) as s:
            existing = s.exec(
                select(Insight).where(Insight.meeting_id == meeting_id)
            ).first()
            
        if existing:
            return {"message": "Insights already exist", "insight": existing}
            
        # Add to background tasks
        background_tasks.add_task(generate_insights_for_meeting, meeting_id)
        
        return {"message": "Insight generation started", "meeting_id": meeting_id}
        
    except Exception as e:
        logger.error(f"Failed to start insight generation for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Failed to start insight generation")

@router.delete("/{meeting_id}")
async def delete_meeting_insights(meeting_id: str):
    """Delete insights for a meeting"""
    try:
        with Session(engine) as s:
            insight = s.exec(
                select(Insight).where(Insight.meeting_id == meeting_id)
            ).first()
            
        if not insight:
            raise HTTPException(404, "Insights not found")
            
        with Session(engine) as s:
            s.delete(insight)
            s.commit()
            
        return {"message": "Insights deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete insights for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/{meeting_id}/view")
async def view_or_generate_meeting_insights(meeting_id: str, background_tasks: BackgroundTasks):
    """View or trigger generation of insights for a meeting."""
    print(f"[INSIGHTS] /view endpoint called for meeting_id={meeting_id}")
    try:
        with Session(engine) as s:
            insight = s.exec(
                select(Insight).where(Insight.meeting_id == meeting_id)
            ).first()
        if insight:
            # Always return a flat JSON object with non-null strings
            return {
                "summary": getattr(insight, "summary", "") or "",
                "action_items": getattr(insight, "action_items", "") or "",
                "decisions": getattr(insight, "decisions", "") or "",
                "summary_available": True
            }
        # Check if there are any transcriptions
        with Session(engine) as s:
            transcriptions = s.exec(
                select(Transcription).where(Transcription.meeting_id == meeting_id)
            ).all()
        if not transcriptions or all((t.content or '').strip() == '' for t in transcriptions):
            return {"message": "This meeting does not have any summary", "summary_available": False}
        # If not found, trigger background generation
        background_tasks.add_task(generate_insights_for_meeting, meeting_id)
        return {"message": "Summary generation started. Please wait...", "summary_available": False}
    except Exception as e:
        logger.error(f"Failed to view or generate insights for meeting {meeting_id}: {e}")
        raise HTTPException(500, "Failed to view or generate insights")
