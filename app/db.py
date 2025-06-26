from sqlmodel import create_engine
from app.config import settings

print("DATABASE_URL in use:", settings.DATABASE_URL)  # Add this line

engine = create_engine(settings.DATABASE_URL, echo=True)