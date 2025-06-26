from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from typing import Optional, List
import random
import string

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class Meeting(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=generate_room_code)
    title: str
    owner_id: str
    jitsi_room: str = Field(default_factory=generate_room_code)
    participants: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = Field(default="active")
