import uuid
from app.db import models
from sqlalchemy.orm import Session
from app.utils.log_utils import setup_logger

logger = setup_logger("crud")

def get_booking_by_mls_and_buyer_phone(db: Session, mls_number: str, buyer_agent_phone_number: str):
    return db.query(models.booking).filter(
        models.booking.mls_number == mls_number,
        models.booking.buyer_agent_phone_number == buyer_agent_phone_number
    ).first()

def get_user_by_phone_number(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def create_user(db: Session, full_name: str, phone_number: str, type: str, agent_id=None, broker_name=None, active_session_id=None):
    try:
        new_user = models.User(full_name=full_name,
                                phone_number=phone_number,
                                type=type,
                                agent_id=agent_id,
                                broker_name=broker_name,
                                active_session_id=active_session_id)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        return None

def get_booking_by_session_id(db: Session, session_id: str):
    return db.query(models.booking).filter(models.booking.listing_agent_session_id == session_id).first()

def get_booking_by_id(db: Session, booking_id: int):
    return db.query(models.booking).filter(models.booking.id == booking_id).first()

def get_booking_by_id_and_buyer_agent_phone_number(db: Session, booking_id: int, buyer_agent_phone_number: str):
    return db.query(models.booking).filter(models.booking.id == booking_id,
                                           models.booking.buyer_agent_phone_number == buyer_agent_phone_number).first()

def get_booking_by_mls_number_and_buyer_agent_phone_number(db: Session, mls_number: str, buyer_agent_phone_number: str):
    return db.query(models.booking).filter(models.booking.mls_number == mls_number,
                                           models.booking.buyer_agent_phone_number == buyer_agent_phone_number).first()

def create_booking(db: Session,
                    buyer_agent_phone_number: str,
                    address: str, mls_number: str,
                    buyer_selected_date: str,
                    buyer_selected_time: str,
                    listing_selected_date: str = None,
                    listing_selected_time: str = None,
                    listing_agent_phone_number: str = None,
                    listing_agent_session_id: str = None,
                    status: str = None):
    try:
        logger.info(f"Creating new booking with mls_number: {mls_number}")
        new_booking = models.booking(buyer_agent_phone_number=buyer_agent_phone_number,
                                    address=address,
                                    mls_number=mls_number,
                                    buyer_selected_date=buyer_selected_date,
                                    buyer_selected_time=buyer_selected_time,
                                    listing_selected_date=listing_selected_date,
                                    listing_selected_time=listing_selected_time,
                                    listing_agent_phone_number=listing_agent_phone_number,
                                    listing_agent_session_id=listing_agent_session_id,
                                    status=status)
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking
    except Exception as e:
        db.rollback()
        print(f"Error creating booking: {e}")
        return None