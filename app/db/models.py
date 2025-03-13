from sqlalchemy import Column, Integer, JSON, ForeignKey, String, DateTime, func, ARRAY
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

    bookings_as_buyer = relationship("Booking", foreign_keys="[Booking.buyer_agent_phone_number]", back_populates="buyer_agent")
    bookings_as_listing_agent = relationship("Booking", foreign_keys="[Booking.listing_agent_phone_number]", back_populates="listing_agent")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    buyer_agent_phone_number = Column(String, ForeignKey("users.phone_number"), nullable=False)
    listing_agent_phone_number = Column(String, ForeignKey("users.phone_number"), nullable=False)
    address = Column(String, default="")
    mls_number = Column(String, default="")
    buyer_selected_date = Column(String, default="")
    buyer_selected_time = Column(String, default="")
    listing_selected_date = Column(String, default="")
    listing_selected_time = Column(String, default="")
    listing_agent_session_id = Column(String, default="")
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    buyer_agent = relationship("User", foreign_keys=[buyer_agent_phone_number], back_populates="bookings_as_buyer")
    listing_agent = relationship("User", foreign_keys=[listing_agent_phone_number], back_populates="bookings_as_listing_agent")
