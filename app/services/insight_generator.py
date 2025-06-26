import uuid
import asyncio
from sqlmodel import Session, select
from app.db import engine
from app.models.transcription import Transcription
from app.models.insight import Insight
from app.utils.openai_client import get_insights_from_transcript
import logging

logger = logging.getLogger(__name__)

async def generate_and_save(meeting_id: str):
    """Generate insights from meeting transcription and save to database"""
    try:
        # Get all transcriptions for the meeting
        with Session(engine) as s:
            transcriptions = s.exec(
                select(Transcription).where(Transcription.meeting_id == meeting_id)
            ).all()
            
        if not transcriptions:
            logger.warning(f"No transcriptions found for meeting {meeting_id}")
            return None
            
        # Combine all transcription content
        full_transcript = "\n".join([t.content for t in transcriptions])
        
        if not full_transcript.strip():
            logger.warning(f"Empty transcript for meeting {meeting_id}")
            return None
            
        # Generate insights using OpenAI
        insights = await get_insights_from_transcript(full_transcript)
        
        # Parse the structured response
        summary, action_items, decisions = parse_insights_response(insights)
        
        # Create and save insight
        insight = Insight(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            summary=summary,
            action_items=action_items,
            decisions=decisions
        )
        
        with Session(engine) as s:
            s.add(insight)
            s.commit()
            s.refresh(insight)
            
        # Broadcast summary to WebSocket clients
        try:
            from app.services.websocket_manager import broadcast_summary
            await broadcast_summary(meeting_id, {
                "summary": insight.summary,
                "action_items": insight.action_items,
                "decisions": insight.decisions,
                "summary_available": True
            })
        except Exception as e:
            logger.error(f"Failed to broadcast summary for meeting {meeting_id}: {e}")
            
        logger.info(f"Generated insights for meeting {meeting_id}")
        return insight
        
    except Exception as e:
        logger.error(f"[INSIGHT GENERATION ERROR] for meeting {meeting_id}: {e}", exc_info=True)
        return None

def parse_insights_response(response: str) -> tuple:
    """Parse the structured response from OpenAI into separate sections. If the response is empty or generic, generate a basic summary from the transcript."""
    try:
        # Split by section markers
        sections = response.split("---")
        if len(sections) >= 3:
            summary = sections[0].strip()
            action_items = sections[1].strip()
            decisions = sections[2].strip()
        else:
            # Fallback parsing
            lines = response.split('\n')
            summary = ""
            action_items = ""
            decisions = ""
            current_section = "summary"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "action" in line.lower() or "todo" in line.lower():
                    current_section = "actions"
                elif "decision" in line.lower() or "conclusion" in line.lower():
                    current_section = "decisions"
                else:
                    if current_section == "summary":
                        summary += line + "\n"
                    elif current_section == "actions":
                        action_items += line + "\n"
                    elif current_section == "decisions":
                        decisions += line + "\n"
        # Clean up the text
        summary = summary.strip()
        action_items = action_items.strip()
        decisions = decisions.strip()
        fallback_phrases = [
            "No summary available for this meeting.",
            "Summary generation failed.",
            "Unable to extract action items.",
            "Unable to extract decisions.",
            "The transcript provided is incomplete and contains only a fragment of speech.",
            "No clear topics, goals, or outcomes can be determined from the limited content.",
            "Further context or additional transcript content is needed for meaningful analysis."
        ]
        if not summary or summary in fallback_phrases:
            # If the summary is empty or fallback, show the transcript itself as the summary
            summary = f"This meeting was very brief. Transcript: {response.strip()[:300]}" if response.strip() else "No transcript available."
        if not action_items or action_items in fallback_phrases:
            action_items = "No specific action items identified."
        if not decisions or decisions in fallback_phrases:
            decisions = "No key decisions recorded."
        return summary, action_items, decisions
    except Exception as e:
        logger.error(f"Failed to parse insights response: {e}")
        return (
            "Summary generation failed.",
            "Unable to extract action items.",
            "Unable to extract decisions."
        )

async def generate_insights_for_meeting(meeting_id: str) -> Insight:
    """Main function to generate insights for a meeting"""
    try:
        return await generate_and_save(meeting_id)
    except Exception as e:
        logger.error(f"[INSIGHT GENERATION ERROR - OUTER] for meeting {meeting_id}: {e}", exc_info=True)
        return None
