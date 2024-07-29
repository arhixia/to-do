from sqlalchemy import Column, Integer, String, DateTime
from src.database import Base

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    list_name = Column(String, index=True)
    description = Column(String)
    due_date = Column(DateTime)
    created_at = Column(DateTime)

