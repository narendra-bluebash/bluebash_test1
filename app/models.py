from sqlalchemy import Column, Integer, JSON, String, DateTime, func, ARRAY
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    full_name = Column(String, default="Unknown")
    agent_id = Column(String, default="")
    type = Column(String, default="buyer")
    broker_name = Column(String, default="")
    current_session_id = Column(String, default="")
    all_session_ids = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())