from app.db import crud
import requests, os, json
from celery import Celery
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.utils.log_utils import setup_logger

logger = setup_logger("task")

ai_agnet_number = os.getenv("AI_AGENT_NUMBER")
n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
redis_host = os.getenv("REDIS_HOST", "localhost")
reminder_before_visit_time = os.getenv("REMINDER_BEFORE_VISIT_TIME")
feedback_after_visit_time = os.getenv("FEEDBACK_AFTER_VISIT_TIME")
tz = ZoneInfo("Asia/Kolkata")

app = Celery(
    "tasks",
    broker=f"redis://{redis_host}:6379/0",
    backend=f"redis://{redis_host}:6379/0",
)
app.conf.broker_connection_retry_on_startup = True


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


@app.task
def schedule_n8n_workflow(from_number, body):
    create_payload_for_whatsapp_message(from_number, body)

@app.task
def send_schedule_showing_reminder_for_booking(booking_id):
    listing_agent_body= None
    buyer_agent_body = None
    db = SessionLocal()
    try:
        booking = crud.get_booking_by_id(db, booking_id)
        if booking and booking.status=="confirmed":
            time = booking.listing_selected_time
            if int(time[:2])>12:
                time_am_pm = f"{int(time[:2])-12}{time[2:]} PM"
            else:
                time_am_pm = f"{time} AM"
            listing_agent_body = f"""Hello {booking.listing_agent.full_name},
                This is a reminder about your scheduled property showing today at {booking.address} (MLS # {booking.mls_number}) at {time_am_pm} with {booking.buyer_agent.full_name}
                Please ensure you are prepared. If you have any questions or need to reschedule, let us know. Your booking ID is #{booking.id} for reference. Thank you!"""

            buyer_agent_body = f"""Hello {booking.buyer_agent.full_name},
                Just a friendly reminder that your scheduled property showing at {booking.address} (MLS # {booking.mls_number}) is today at {time_am_pm} with {booking.listing_agent.full_name}
                Please be on time and let us know if you encounter any issues. Your booking ID is #{booking.id} for reference. Looking forward to a successful showing!"""

            logger.info(f"Booking message for Listing agent:- {listing_agent_body}")
            logger.info(f"Booking message for Buyer agent:- {buyer_agent_body}")
            create_payload_for_whatsapp_message(booking.buyer_agent.phone_number, buyer_agent_body)
            create_payload_for_whatsapp_message(booking.listing_agent.phone_number, listing_agent_body)
            buyer_agent_reminder_msg = f"""Hello {booking.buyer_agent.full_name},
                Hope your scheduled property showing at {booking.address} (MLS # {booking.mls_number}) with {booking.listing_agent.full_name} went well today.
                We would love to hear your feedback about your experience. Please reply to this message with any comments or suggestions you may have.
                Thank you for choosing us! Your booking ID is #{booking.id} for reference."""
            logger.info(f"Feedback message for Buyer agent:- {buyer_agent_reminder_msg}")
            schedule_n8n_workflow.apply_async(args=[booking.buyer_agent.phone_number, buyer_agent_reminder_msg], countdown=int(feedback_after_visit_time))
        else:
            logger.warning(f"No booking found with ID: {booking_id}")
            return "Booking not found or may be cancelled"
    finally:
        db.close()
    return "Booking reminder scheduled successfully"


def schedule_showing_reminder_for_booking(booking_id, listing_selected_date, listing_selected_time):
    target_datetime_kolkata = datetime.strptime(f"{listing_selected_date} {listing_selected_time}:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    target_datetime_utc = target_datetime_kolkata.astimezone(timezone.utc)
    current_utc = datetime.now(timezone.utc)
    seconds_from_now = int((target_datetime_utc - current_utc).total_seconds())
    logger.info(f"Sending showing reminder for booking ID: {booking_id} in {seconds_from_now} seconds")
    seconds_from_now = seconds_from_now - int(reminder_before_visit_time)
    if seconds_from_now > 0:
        logger.info(f"Task scheduled to run in {seconds_from_now} seconds.")
        send_schedule_showing_reminder_for_booking.apply_async(args=[booking_id], countdown=seconds_from_now)
        return "Reminder scheduled successfully"
    else:
        logger.warning(f"Second from now scheduled is less than expected. Not scheduling reminder. seconds_from_now: {seconds_from_now}")
        return f"Second from now scheduled is less than expected. Not scheduling"