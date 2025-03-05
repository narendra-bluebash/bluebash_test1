from app import models
import uuid
from sqlalchemy.orm import Session
from utils.log_utils import setup_logger

logger = setup_logger("crud")

def get_property_by_mls_and_buyer_phone(db: Session, mls_number: str, buyer_agent_phone_number: str):
    return db.query(models.Property).filter(
        models.Property.mls_number == mls_number,
        models.Property.buyer_agent_phone_number == buyer_agent_phone_number
    ).first()

def get_user_by_phone_number(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def create_user(db: Session, full_name: str, phone_number: str, type: str, agent_id=None, broker_name=None):
    try:
        if type == "listing":
            new_session_id = uuid.uuid4()
            logger.info(f"Lisitng Agent Found: Creating listing agent with phone number: {phone_number}")
            user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
            if user:
                if user.active_session_id:
                    logger.info(f"User Already exist, with phone_number: {phone_number}")
                else:
                    logger.info(f"User Already exist, with phone_number: {phone_number}")
                    user.active_session_id = new_session_id
                user.all_session_ids = user.all_session_ids + [new_session_id]
                db.commit()
                db.refresh(user)
                return user
            else:
                logger.info(f"Creating new user with phone_number: {phone_number}")
                new_user = models.User(full_name=full_name,
                                       phone_number=phone_number,
                                       type=type,
                                       agent_id=agent_id,
                                       broker_name=broker_name,
                                       active_session_id=new_session_id,
                                       all_session_ids=[new_session_id])
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user
        else:
            logger.info(f"Buyer Agent Found: Creating buyer agent with phone number: {phone_number}")
            new_user = models.User(full_name=full_name,
                                    phone_number=phone_number,
                                    type="buyer",
                                    agent_id=agent_id,
                                    broker_name=broker_name)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return None

def get_property_by_session_id(db: Session, session_id: str):
    return db.query(models.Property).filter(models.Property.listing_agent_session_id == session_id).first()


def create_property(db: Session,
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
        property = db.query(models.Property).filter(models.Property.mls_number == mls_number,
                                                    models.Property.buyer_agent_phone_number == buyer_agent_phone_number).first()
        if property:
            logger.info(f"Property already exist: Updating property with mls_number: {mls_number}")
            property.buyer_selected_date = buyer_selected_date
            property.buyer_selected_time = buyer_selected_time
            db.commit()
            db.refresh(property)
            return property
        else:
            logger.info(f"Creating new property with mls_number: {mls_number}")
            new_property = models.Property(buyer_agent_phone_number=buyer_agent_phone_number,
                                        address=address,
                                        mls_number=mls_number,
                                        buyer_selected_date=buyer_selected_date,
                                        buyer_selected_time=buyer_selected_time,
                                        listing_selected_date=listing_selected_date,
                                        listing_selected_time=listing_selected_time,
                                        listing_agent_phone_number=listing_agent_phone_number,
                                        listing_agent_session_id=listing_agent_session_id,
                                        status=status)
            db.add(new_property)
            db.commit()
            db.refresh(new_property)
            return new_property
    except Exception as e:
        db.rollback()
        print(f"Error creating property: {e}")
        return None