from app.db import crud
import requests, os, json, uuid
from app.utils.log_utils import setup_logger
from sqlalchemy.orm.attributes import flag_modified
from app.task_scheduler.task import schedule_n8n_workflow
from app.services.agent_service import verify_agent_by_agent_id_and_broker_name
from app.services.properties_service import get_property_by_address_or_mls_number
from dotenv import load_dotenv
load_dotenv()

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
ai_agnet_number = os.getenv("AI_AGENT_NUMBER")
n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

logger = setup_logger("realtor_service")

def create_payload_for_whatsapp_message(from_number, body):
    payload = [
        {
            "SmsMessageSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "NumMedia": "0",
            "ProfileName": "",
            "MessageType": "text",
            "SmsSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "WaId": from_number,
            "SmsStatus": "received",
            "Body": f"paparaphrase this: {body}",
            "To": f"whatsapp:{ai_agnet_number}",
            "NumSegments": "1",
            "ReferralNumMedia": "0",
            "MessageSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "AccountSid": "",
            "From": f"whatsapp:{from_number}",
            "ApiVersion": "2010-04-01"
        }
    ]

    try:

        headers = {"Content-Type": "application/json"}
        response = requests.post(n8n_webhook_url, headers=headers, data=json.dumps(payload))
        logger.info(f"Response for whatsapp webhook: {response.text}")
    except Exception as e:
        logger.error(f"Error in sending message to agent: {e}")
        return f"Error in sending message to agent: {str(e)}"
    return "Message sent successfully"


class RealtorService:
    def __init__(self):
        pass

    def book_showings(self, db, booking_address, mls_number, date, time, buyer_agent_phone_number):
        buyer_selected_date = date
        buyer_selected_time = time
        logger.warning(f"Listing realtore - booking_address: {booking_address}, mls_number: {mls_number}, date: {buyer_selected_date}, time: {buyer_selected_time}, buyer_agent_phone_number: {buyer_agent_phone_number}")
        #TODO: Add logic to get booking details from mls_number
        response = get_property_by_address_or_mls_number(mls_number=mls_number, address=booking_address)
        if response is None:
            return "Invalid mls_number or address"
        listing_agent_full_name = response["agent_name"]
        listing_agent_phone_number = response["agent_phone"]
        type = "listing"
        booking_address = response["address"]
        try:
            buyer_user = crud.get_user_by_phone_number(db, phone_number=buyer_agent_phone_number)
            if not buyer_user:
                return "Buyer agent not found"

            new_session_id = uuid.uuid4()
            listing_user = crud.get_user_by_phone_number(db, phone_number=listing_agent_phone_number)
            if listing_user:
                if listing_user.active_session_id:
                    listing_user.queued_session_ids = listing_user.queued_session_ids + [new_session_id]
                    logger.info(f"The user already exists with the provided phone number and has an active session. Therefore, the task is being added to the queue: {buyer_agent_phone_number}")
                    db.commit()
                    db.refresh(listing_user)
                    booking = crud.get_booking_by_mls_number_and_buyer_agent_phone_number(db, mls_number=mls_number, buyer_agent_phone_number=buyer_agent_phone_number)
                    if booking:
                        booking.buyer_selected_date = buyer_selected_date
                        booking.buyer_selected_time = buyer_selected_time
                        booking.status = "pending"
                        db.commit()
                        db.refresh(booking)
                        return f"A booking already exists with this MLS number. The rescheduling request has been successfully processed. Your booking ID is {booking.id} for future reference."
                    else:
                        booking = crud.create_booking(db, buyer_agent_phone_number=buyer_agent_phone_number,
                                                        address=booking_address, mls_number=mls_number, buyer_selected_date=buyer_selected_date,
                                                        buyer_selected_time=buyer_selected_time, listing_agent_phone_number=listing_agent_phone_number,
                                                        listing_agent_session_id=new_session_id)
                        return f"Do not say like its booked successfully say like: Your showing request is awaiting confirmation from the listing agent, {listing_user.full_name}. I will notify you once the listing agent confirms the showing appointment. Your booking ID is #{booking.id} for future reference."
                else:
                    logger.info(f"The user already exists but no active session found : {buyer_agent_phone_number}")
                    listing_user.active_session_id = new_session_id
                    db.commit()
                    db.refresh(listing_user)
                    booking = crud.get_booking_by_mls_number_and_buyer_agent_phone_number(db, mls_number=mls_number, buyer_agent_phone_number=buyer_agent_phone_number)
                    if booking:
                        booking.buyer_selected_date = buyer_selected_date
                        booking.buyer_selected_time = buyer_selected_time
                        db.commit()
                        db.refresh(booking)
                        return f"Rescheduling request has been successfully processed. Your booking ID is {booking.id}."
                    else:
                        booking = crud.create_booking(db, buyer_agent_phone_number=buyer_agent_phone_number,
                                                        address=booking_address, mls_number=mls_number, buyer_selected_date=buyer_selected_date,
                                                        buyer_selected_time=buyer_selected_time, listing_agent_phone_number=listing_agent_phone_number,
                                                        listing_agent_session_id=listing_user.active_session_id)
            else:
                listing_user = crud.create_user(db, full_name=listing_agent_full_name, phone_number=listing_agent_phone_number, type=type, active_session_id=new_session_id)
                if not listing_user:
                    logger.info(f"Error in creating listing agent.")
                    return "Error in creating listing agent."
                booking = crud.create_booking(db, buyer_agent_phone_number=buyer_agent_phone_number,
                                                address=booking_address, mls_number=mls_number, buyer_selected_date=buyer_selected_date,
                                                buyer_selected_time=buyer_selected_time, listing_agent_phone_number=listing_agent_phone_number,
                                                listing_agent_session_id=new_session_id)

        except Exception as e:
            db.rollback()
            logger.error(f"Error in creating booking: {e}")
            return "booking creation failed"

        if int(buyer_selected_time[:2])>12:
            buyer_selected_time = f"{int(buyer_selected_time[:2])-12}{buyer_selected_time[2:]} PM"
        else:
            buyer_selected_time = f"{buyer_selected_time} AM"

        listing_agent_body = f"Hello {listing_agent_full_name}, this is Alice assistant of {buyer_user.full_name}. We would like to schedule a showing for {booking_address} (MLS # {mls_number}) at {buyer_selected_time} on {buyer_selected_date}. The booking ID for this request is #{booking.id} for future reference. Can you make that work?."
        logger.info(f"Sending message to listing agent from: {ai_agnet_number}, body: {listing_agent_body}, to: {listing_agent_phone_number}")
        response = create_payload_for_whatsapp_message(from_number=listing_agent_phone_number, body=listing_agent_body)
        if response == "Message sent successfully":
            return f"Do not say like its booked successfully say like: Your showing request is awaiting confirmation from the listing agent, {listing_user.full_name}. I will notify you once the listing agent confirms the showing appointment. Your booking ID is #{booking.id} for future reference."
        return "Error in sending message to listing agent"


    def listing_realtor_confirmation(self, db, session_id, listing_selected_date, listing_selected_time, confirmation):
        is_listing_user_session_queued = False
        logger.warning(f"Listing realtore - listing_selected_date: {listing_selected_date}, listing_selected_time: {listing_selected_time}, session_id: {session_id}, confirmation: {confirmation}.")
        try:
            booking = crud.get_booking_by_session_id(db, session_id=session_id)
            listing_user = crud.get_user_by_phone_number(db, phone_number=booking.listing_agent_phone_number)
        except Exception as e:
            logger.error(f"Error in creating user: {e}")
            return f"booking not found with this session id, Error: {str(e)}"
        if not booking:
            return "booking not found with this session id"
        booking.listing_selected_date = listing_selected_date
        booking.listing_selected_time = listing_selected_time

        if listing_selected_date == booking.buyer_selected_date and listing_selected_time == booking.buyer_selected_time:
            logger.info(f"listing_selected_date and listing_selected_time are same as buyer_selected_date and buyer_selected_time")
            confirmation = "confirmed"
        if int(listing_selected_time[:2])>12:
            listing_selected_time = f"{int(listing_selected_time[:2])-12}{listing_selected_time[2:]} PM"
        else:
            listing_selected_time = f"{listing_selected_time} AM"
        if confirmation == "confirmed":
            logger.warning(f"booking Schudule is confirmed by listing agent.")
            if listing_user.queued_session_ids:
                logger.info(f"listing user has queued sessions Found. active session id: {listing_user.active_session_id}, queued sessions: {listing_user.queued_session_ids}")
                listing_user.completed_session_ids = listing_user.completed_session_ids + [listing_user.active_session_id]
                listing_user.active_session_id = listing_user.queued_session_ids.pop(0)
                flag_modified(listing_user, "queued_session_ids")
                is_listing_user_session_queued = True
            booking.status = "confirmed"
            listing_agent_body = f"Your showing at {booking.address} (MLS # {booking.mls_number}) is confirmed on {listing_selected_date} at {listing_selected_time}. I'll send you a reminder the day before to ensure you're prepared. The booking ID for this request is #{booking.id} for future reference."
            buyer_agent_body = f"Your showing at {booking.address} (MLS # {booking.mls_number}) is confirmed by {listing_user.full_name} on {listing_selected_date} at {listing_selected_time} . I'll send you a reminder the day before to ensure you're prepared. The booking ID for this request is #{booking.id} for future reference."

        elif confirmation == "cancelled":
            logger.warning(f"booking Schudule is cancelled by listing agent.")
            if listing_user.queued_session_ids:
                logger.info(f"listing user has queued sessions Found. active session id: {listing_user.active_session_id}, queued sessions: {listing_user.queued_session_ids}")
                listing_user.completed_session_ids = listing_user.completed_session_ids + [listing_user.active_session_id]
                listing_user.active_session_id = listing_user.queued_session_ids.pop(0)
                flag_modified(listing_user, "queued_session_ids")
                is_listing_user_session_queued = True
            booking.status = "cancelled"
            listing_agent_body = f"Thank you for letting us know. I'll inform the buyer that the showing has been canceled. The booking ID for this request is #{booking.id} for future reference."
            buyer_agent_body = f"Unfortunately, the listing agent, {listing_user.full_name} has canceled the showing for the property at {booking.address} (MLS # {booking.mls_number}). We apologize for any inconvenience. Your booking ID is #{booking.id} for future reference."

        elif confirmation == "rescheduled":
            logger.warning(f"booking Schudule is rescheduled by listing agent. because of listing_selected_date: {listing_selected_date}, listing_selected_time: {listing_selected_time} and buyer_selected_date: {booking.buyer_selected_date}, buyer_selected_time: {booking.buyer_selected_time}")
            booking.status = "rescheduled"
            listing_agent_body = f"paparaphrase this: Your reschedule request for the showing has been submitted and is waiting for confirmation from the buyer agent. I’ll update you once they confirm the showing appointment. Your booking ID is #{booking.id} for reference."
            buyer_agent_body = f"The listing agent for the booking at {booking.address} (MLS # {booking.mls_number}) wants to rescheduled the showing on {listing_selected_date} at {listing_selected_time} . Your booking ID is #{booking.id} for future reference, Please confirm if this new time works for you."
        else:
            logger.warning(f"Invalid confirmation status")
            return "Invalid confirmation status"

        if is_listing_user_session_queued:
            countdown_second=60
            queued_booking = crud.get_booking_by_session_id(db, listing_user.active_session_id)
            logger.info(f"Queued sessions id: {queued_booking.listing_agent_session_id}")
            buyer_user = queued_booking.buyer_agent
            listing_agent_body = f"Hello {listing_user.full_name}, this is Alice assistant of {buyer_user.full_name}. We would like to schedule a showing for {queued_booking.address} (MLS # {queued_booking.mls_number}) at {queued_booking.buyer_selected_time} on {queued_booking.buyer_selected_date}. The booking ID for this request is #{queued_booking.id} for future reference. Can you make that work?."
            logger.info(f"Sending message to listing agent, body: {listing_agent_body}, to: {listing_user.phone_number}")
            result = schedule_n8n_workflow.apply_async(args = [listing_user.phone_number, listing_agent_body], countdown=countdown_second)
            logger.info(f"Task scheduled to run in {countdown_second} seconds.")

        logger.info(f"Sending message to listing agent, body: {buyer_agent_body}, to: {booking.buyer_agent_phone_number}")
        response = create_payload_for_whatsapp_message(from_number=booking.buyer_agent_phone_number, body=buyer_agent_body)
        if response != "Message sent successfully":
            logger.error(f"Error in sending message to listing agent")
            return "Error in sending message to buyer agent"
        db.commit()
        return listing_agent_body

    def buyer_realtor_confirmation(self, db, buyer_agent_phone_number, booking_id, mls_number, buyer_selected_date, buyer_selected_time, confirmation):
        is_listing_user_session_queued = False
        logger.warning(f"Buyer realtore - booking_id: {booking_id}, mls_number: {mls_number}, buyer_selected_date: {buyer_selected_date}, buyer_selected_time: {buyer_selected_time}, confirmation: {confirmation}.")
        try:
            if booking_id:
                booking = crud.get_booking_by_id_and_buyer_agent_phone_number(db, booking_id=booking_id, buyer_agent_phone_number=buyer_agent_phone_number)
            elif mls_number:
                booking = crud.get_booking_by_mls_number_and_buyer_agent_phone_number(db, mls_number=mls_number, buyer_agent_phone_number=buyer_agent_phone_number)
            else:
                return "Invalid booking id or mls number"
            listing_user = crud.get_user_by_phone_number(db, phone_number=booking.listing_agent_phone_number)
        except Exception as e:
            logger.error(f"Error in creating user: {e}")
            return f"booking not found with this booking id, Error: {str(e)}"
        if not booking:
            return "booking not found with this booking id"
        booking.buyer_selected_date = buyer_selected_date
        booking.buyer_selected_time = buyer_selected_time
        if buyer_selected_date == booking.listing_selected_date and buyer_selected_time == booking.listing_selected_time:
            logger.info(f"buyer_selected_date and buyer_selected_time are same as listing_selected_date and listing_selected_time")
            confirmation = "confirmed"
        if int(buyer_selected_time[:2])>12:
            buyer_selected_time = f"{int(buyer_selected_time[:2])-12}{buyer_selected_time[2:]} PM"
        else:
            buyer_selected_time = f"{buyer_selected_time} AM"
        if confirmation == "confirmed":
            logger.warning(f"booking Schudule is confirmed by buyer agent.")
            if listing_user.queued_session_ids:
                logger.info(f"listing user has queued sessions Found. active session id: {listing_user.active_session_id}, queued sessions: {listing_user.queued_session_ids}")
                listing_user.completed_session_ids = listing_user.completed_session_ids + [listing_user.active_session_id]
                listing_user.active_session_id = listing_user.queued_session_ids.pop(0)
                flag_modified(listing_user, "queued_session_ids")
                is_listing_user_session_queued = True
            booking.status = "confirmed"
            buyer_agent_body = f"Your showing at {booking.address} (MLS # {booking.mls_number}) is confirmed on {buyer_selected_date} at {buyer_selected_time}. Your booking ID is {booking.id} for future reference. I'll send you a reminder the day before to ensure you're prepared."
            listing_agent_body = f"Your showing at {booking.address} (MLS # {booking.mls_number}) is confirmed on {buyer_selected_date} at {buyer_selected_time} . Your booking ID is {booking.id} for future reference. I'll send you a reminder the day before to ensure you're prepared."

        elif confirmation == "cancelled":
            logger.warning(f"booking Schudule is cancelled by buyer agent.")
            if listing_user.queued_session_ids:
                logger.info(f"listing user has queued sessions Found. active session id: {listing_user.active_session_id}, queued sessions: {listing_user.queued_session_ids}")
                listing_user.completed_session_ids = listing_user.completed_session_ids + [listing_user.active_session_id]
                listing_user.active_session_id = listing_user.queued_session_ids.pop(0)
                flag_modified(listing_user, "queued_session_ids")
                is_listing_user_session_queued = True
            booking.status = "cancelled"
            buyer_agent_body = f"Thank you for letting us know. I'll inform the listing agent that the showing has been canceled. The booking ID for this request is #{booking.id} for future reference."
            listing_agent_body = f"Unfortunately, the Buyer agent, {booking.buyer_agent.full_name} has canceled the showing for the property at {booking.address} (MLS # {booking.mls_number}). We apologize for any inconvenience. Your booking ID is #{booking.id} for future reference."

        elif confirmation == "rescheduled":
            logger.warning(f"booking Schudule is rescheduled by Buyer agent. because of listing_selected_date: {buyer_selected_date}, listing_selected_time: {buyer_selected_time} and buyer_selected_date: {booking.buyer_selected_date}, buyer_selected_time: {booking.buyer_selected_time}")
            booking.status = "rescheduled"
            buyer_agent_body = f"paparaphrase this: Your reschedule request for the showing has been submitted and is waiting for confirmation from the buyer agent. I’ll update you once they confirm the showing appointment. Your booking ID is #{booking.id} for reference."
            listing_agent_body = f"The Buyer agent for the booking at {booking.address} (MLS # {booking.mls_number}) wants to rescheduled the showing on {buyer_selected_date} at {buyer_selected_time}. Your booking ID is #{booking.id} for future reference. Please confirm if this new time works for you."

        else:
            logger.warning(f"Invalid confirmation status")
            return "Invalid confirmation status"

        if is_listing_user_session_queued:
            countdown_second=60
            queued_booking = crud.get_booking_by_session_id(db, listing_user.active_session_id)
            logger.info(f"Queued sessions id: {queued_booking.listing_agent_session_id}")
            buyer_user = queued_booking.buyer_agent
            listing_agent_body = f"Hello {listing_user.full_name}, this is Alice assistant of {buyer_user.full_name}. We would like to schedule a showing for {queued_booking.address} (MLS # {queued_booking.mls_number}) at {queued_booking.buyer_selected_time} on {queued_booking.buyer_selected_date}. The booking ID for this request is #{queued_booking.id} for future reference. Can you make that work?."
            logger.info(f"Sending message to listing agent, body: {listing_agent_body}, to: {listing_user.phone_number}")
            result = schedule_n8n_workflow.apply_async(args = [listing_user.phone_number, listing_agent_body], countdown=countdown_second)
            logger.info(f"Task scheduled to run in {countdown_second} seconds.")

        logger.info(f"Sending message to listing agent from: {ai_agnet_number}, body: {listing_agent_body}, to: {booking.listing_agent_phone_number}")
        response = create_payload_for_whatsapp_message(from_number=booking.listing_agent_phone_number, body=listing_agent_body)
        if response != "Message sent successfully":
            logger.error(f"Error in sending message to listing agent")
            return "Error in sending message to Listing agent"
        db.commit()
        return buyer_agent_body


    def buyer_realtor_sign_up(self, db, full_name, agent_id, broker_name, phone_number, type):
        logger.warning(f"Buyer realtor singup request: {full_name}, {agent_id}, {broker_name}, {phone_number}, {type}")
        #TODO: Add logic to verify agent_id and broker_name
        if not verify_agent_by_agent_id_and_broker_name(agent_id=agent_id, broker_name=broker_name):
            logger.warning(f"Invalid agent_id or broker_name")
            return "Wrong agent id or broker name"
        user = crud.create_user(db, full_name=full_name, phone_number=phone_number, type=type, agent_id=agent_id, broker_name=broker_name)
        if not user:
            "User creation failed"
        return "user is signed up sucessfully. Now you can book the showing with the listing agent. would you like to book a showing now?"


    def get_booking(self, db, booking_id, mls_number, phone_number):
        logger.warning(f"Get booking request: {booking_id}, {mls_number}, {phone_number}")
        if booking_id:
            booking = crud.get_booking_by_id_and_buyer_agent_phone_number(db, booking_id=booking_id, buyer_agent_phone_number=phone_number)
        elif mls_number:
            booking = crud.get_booking_by_mls_number_and_buyer_agent_phone_number(db, mls_number=mls_number, buyer_agent_phone_number=phone_number)
        else:
            return "Invalid booking_id or mls_number or phone_number"
        if not booking:
            return "booking not found"
        logger.info(f"booking details: {str(vars(booking))}")
        return str(vars(booking))