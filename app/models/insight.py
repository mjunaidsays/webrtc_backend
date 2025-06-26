from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text
from datetime import datetime

class Insight(SQLModel, table=True):
    id: str = Field(primary_key=True, default=None)
    meeting_id: str = Field(foreign_key="meeting.id")
    summary: str = Field(sa_column=Column(Text))
    action_items: str = Field(sa_column=Column(Text))
    decisions: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
