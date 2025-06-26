from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Query
from sqlmodel import Session, select
import uuid
from datetime import datetime
from app.db import engine
from app.models.meeting import Meeting, generate_room_code
from app.services.insight_generator import generate_insights_for_meeting
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

SECRET_KEY = 'vLnUHUAnHv8PK7T1qNeTZMIrMzNOm6CGU0VGOywzGOB5jfSzitP3YDwXMSR8ghvL06u5DJ3tqTpTot20ofSeFA'
APP_ID = 'vpaas-magic-cookie-4d98055dcb7a4e7e818e22aa1b84781d'

class JoinRequest(BaseModel):
    user_name: str

@router.post("/create")
def create_meeting(title: str = Query(...), owner_name: str = Query(...)):
    """Create a new meeting"""
    try:
        meeting = Meeting(
            title=title,
            owner_id=owner_name,
            participants=[owner_name]
        )
        with Session(engine) as s:
            s.add(meeting)
            s.commit()
            s.refresh(meeting)
        return meeting
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        raise HTTPException(500, "Failed to create meeting")

@router.get("/{meeting_id}")
def get_meeting(meeting_id: str):
    """Get meeting details"""
    try:
        with Session(engine) as s:
            m = s.exec(select(Meeting).where(Meeting.id == meeting_id)).one_or_none()
        if not m:
            raise HTTPException(404, "Meeting not found")
        return m
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.post("/{meeting_id}/join")
def join_meeting(meeting_id: str, req: JoinRequest):
    """Join an existing meeting"""
    user_name = req.user_name
    try:
        with Session(engine) as s:
            m = s.exec(select(Meeting).where(Meeting.id == meeting_id)).one_or_none()
            if not m:
                raise HTTPException(404, "Meeting not found")
            if m.status != "active":
                raise HTTPException(400, "Meeting has ended")
            if len(m.participants) >= 4:
                raise HTTPException(403, "Room is full (max 4 participants)")
            if user_name not in m.participants:
                m.participants.append(user_name)
                s.add(m)
                s.commit()
                s.refresh(m)
        return m
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.post("/{meeting_id}/end")
async def end_meeting(meeting_id: str, background_tasks: BackgroundTasks):
    """End a meeting and trigger summary generation"""
    try:
        with Session(engine) as s:
            m = s.exec(select(Meeting).where(Meeting.id == meeting_id)).one_or_none()
            if not m:
                raise HTTPException(404, "Meeting not found")
            
            # Update meeting status
            m.status = "ended"
            m.ended_at = datetime.utcnow()
            s.add(m)
            s.commit()
            s.refresh(m)
        
        # Trigger insight generation in background
        background_tasks.add_task(generate_insights_for_meeting, meeting_id)
        
        return {
            "message": "Meeting ended successfully",
            "meeting_id": meeting_id,
            "summary_generation": "started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end meeting {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")

@router.get("/{meeting_id}/status")
def get_meeting_status(meeting_id: str):
    """Get meeting status and summary availability"""
    try:
        with Session(engine) as s:
            m = s.exec(select(Meeting).where(Meeting.id == meeting_id)).one_or_none()
            if not m:
                raise HTTPException(404, "Meeting not found")
            
            # Check if insights exist
            from app.models.insight import Insight
            insight = s.exec(select(Insight).where(Insight.meeting_id == meeting_id)).first()
            
            return {
                "meeting_id": meeting_id,
                "status": m.status,
                "participants": m.participants,
                "created_at": m.created_at,
                "ended_at": m.ended_at,
                "summary_available": insight is not None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting status {meeting_id}: {e}")
        raise HTTPException(500, "Internal server error")
