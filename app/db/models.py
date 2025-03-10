from sqlalchemy import Column, Integer, JSON,ForeignKey, String, DateTime, func, ARRAY
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    full_name = Column(String, default="Unknown")
    agent_id = Column(String, default="")
    type = Column(String, default="buyer")
    broker_name = Column(String, default="")
    active_session_id = Column(String, default="")
    queued_session_ids = Column(ARRAY(String), default=[])
    completed_session_ids = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("booking", back_populates="buyer_agent")

class booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    buyer_agent_phone_number = Column(String, ForeignKey("users.phone_number"), nullable=False)
    address = Column(String, default="")
    mls_number = Column(String, default="")
    buyer_selected_date = Column(String, default="")
    buyer_selected_time = Column(String, default="")
    listing_selected_date = Column(String, default="")
    listing_selected_time = Column(String, default="")
    listing_agent_phone_number = Column(String, default="")
    listing_agent_session_id = Column(String, default="")
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer_agent = relationship("User", back_populates="bookings")