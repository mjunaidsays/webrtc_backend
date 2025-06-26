from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Transcription(SQLModel, table=True):
    id: str = Field(primary_key=True, default=None)
    meeting_id: str = Field(foreign_key="meeting.id")
    content: str
    speaker: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
