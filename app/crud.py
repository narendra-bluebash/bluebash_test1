from app import models
import uuid
from sqlalchemy.orm import Session


def get_user_by_phone_number(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def create_user(db: Session, full_name: str, phone_number: str, type: str, agent_id=None, broker_name=None):
    try:
        if type == "listing":
            current_session_id = uuid.uuid4()
            user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
            if user:
                user.current_session_id = current_session_id
                user.all_session_ids = user.all_session_ids + [current_session_id]
                db.commit()
                db.refresh(user)
                return user
            else:
                new_user = models.User(full_name=full_name,
                                       phone_number=phone_number,
                                       type=type,
                                       agent_id=agent_id,
                                       broker_name=broker_name,
                                       current_session_id=current_session_id,
                                       all_session_ids=[current_session_id])
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user

        else:
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