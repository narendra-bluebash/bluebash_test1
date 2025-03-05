
from app import models, crud
from app.database import SessionLocal, engine
from utils.log_utils import setup_logger
from fastapi import Request, Depends, APIRouter, HTTPException
import os, json, random, requests
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from twilio.twiml.messaging_response import MessagingResponse
from fastapi.responses import Response
from pydantic import BaseModel, Field
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()

logger = setup_logger("router")

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
ai_agnet_number = os.getenv("AI_AGENT_NUMBER")
n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

router = APIRouter()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MessageRequestSignUP(BaseModel):
    phone_number: str = Field(default="+917389058485")
    agent_id: str = Field(default="")
    full_name: str = Field(default="agent_full_name")
    broker_name: str = Field(default="")
    type: str = Field(default="buyer")
    listing_realtor_msg: str = Field(default="")

@router.post('/realtor/signup')
async def realtor_sign_up(request: MessageRequestSignUP, db: Session = Depends(get_db)):
    logger.warning(f"singup request: {request}")
    user = crud.create_user(db, full_name=request.full_name, phone_number=request.phone_number, type=request.type, agent_id=request.agent_id, broker_name=request.broker_name)
    if not user:
        raise HTTPException(status_code=400, detail="User creation failed")
    return JSONResponse(content="user is signed up sucessfully.")

def create_payload_for_whatsapp_message(from_number, to_number, body):
    payload = [
        {
            "SmsMessageSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "NumMedia": "0",
            "ProfileName": "",
            "MessageType": "text",
            "SmsSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "WaId": from_number,
            "SmsStatus": "received",
            "Body": f"Mimic the input text exactly and return it unchanged: {body}",
            "To": f"whatsapp:{to_number}",
            "NumSegments": "1",
            "ReferralNumMedia": "0",
            "MessageSid": "SM0b07afa5f1ede39427957b4dc127cab3",
            "AccountSid": "",
            "From": f"whatsapp:{from_number}",
            "ApiVersion": "2010-04-01"
        }
    ]

    return payload


class CreatePropertyRequest(BaseModel):
    buyer_agent_phone_number: str = Field(default="+917389058485")
    address: str = Field(default="property_address_test")
    mls_number: str = Field(default="mls_number_test")
    buyer_selected_date: str = Field(default="date_test")
    buyer_selected_time: str = Field(default="time_test")
    listing_agent_phone_number: str = Field(default="")
    listing_agent_session_id: str = Field(default="")
    status: str = Field(default="pending")

@router.post('/realtor/create_property')
async def create_property(request: CreatePropertyRequest, db: Session = Depends(get_db)):
    logger.warning(f"Create property request: {request}")

    buyer_agent_phone_number = request.buyer_agent_phone_number
    address = request.address
    mls_number = request.mls_number
    buyer_selected_date = request.buyer_selected_date
    buyer_selected_time = request.buyer_selected_time
    listing_agent_phone_number = request.listing_agent_phone_number
    listing_agent_session_id = request.listing_agent_session_id
    status = request.status

    try:
        property = crud.create_property(db, buyer_agent_phone_number=buyer_agent_phone_number,
                                            address=address, mls_number=mls_number, buyer_selected_date=buyer_selected_date,
                                            buyer_selected_time=buyer_selected_time, listing_agent_phone_number=listing_agent_phone_number,
                                            listing_agent_session_id=listing_agent_session_id, status=status)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in creating property: {e}")
        raise HTTPException(status_code=400, detail="Property creation failed")

    return JSONResponse(content="Property is created successfully.")

class ListingRealtorSignUP(BaseModel):
    property_address: str = Field(default="property_address_test")
    mls_number: str = Field(default="mls_number_test")
    date: str = Field(default="date_test")
    time: str = Field(default="time_test")
    buyer_agent_phone_number: str = Field(default="")

@router.post('/listing_realtor/signup')
async def listing_realtor_sign_up(request: ListingRealtorSignUP, db: Session = Depends(get_db)):
    logger.warning(f"Listing realtor singup request: {request}")

    property_address = request.property_address
    mls_number = request.mls_number
    buyer_selected_date = request.date
    buyer_selected_time = request.time
    buyer_agent_phone_number = request.buyer_agent_phone_number

    logger.warning(f"Listing realtore - property_address: {property_address}, mls_number: {mls_number}, date: {buyer_selected_date}, time: {buyer_selected_time}, buyer_agent_phone_number: {buyer_agent_phone_number}")
    #TODO: Add logic to get property details from mls_number
    listing_agent_full_name = "Bob"
    listing_agent_phone_number = "+917347256305"
    type = "listing"
    property_address = "123 Main Street"
    try:
        buyer_user = crud.get_user_by_phone_number(db, phone_number=buyer_agent_phone_number)
        if not buyer_user:
            raise HTTPException(status_code=400, detail="Buyer agent not found")
        listing_user = crud.create_user(db, full_name=listing_agent_full_name, phone_number=listing_agent_phone_number, type=type)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in creating user: {e}")
        raise HTTPException(status_code=400, detail="User creation failed")

    try:
        property = crud.create_property(db, buyer_agent_phone_number=buyer_agent_phone_number,
                                            address=property_address, mls_number=mls_number, buyer_selected_date=buyer_selected_date,
                                            buyer_selected_time=buyer_selected_time, listing_agent_phone_number=listing_agent_phone_number,
                                            listing_agent_session_id=listing_user.active_session_id)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in creating property: {e}")
        raise HTTPException(status_code=400, detail="Property creation failed")

    listing_agent_body = f"Hello {listing_agent_full_name}, this is Alice assistant of {buyer_user.full_name}. We would like to schedule a showing for {property_address} (MLS # {mls_number}) at {buyer_selected_time} on {buyer_selected_date}. Can you make that work?"

    try:
        logger.info(f"Sending message to listing agent from: {ai_agnet_number}, body: {listing_agent_body}, to: {listing_agent_phone_number}")
        payload  = create_payload_for_whatsapp_message(from_number=listing_agent_phone_number, to_number=ai_agnet_number, body=listing_agent_body)
        headers = {"Content-Type": "application/json"}
        response = requests.post(n8n_webhook_url, headers=headers, data=json.dumps(payload))
        logger.info(f"Response for whatsapp webhook: {response.text}")

    except Exception as e:
        db.rollback()
        logger.error(f"Error in sending message to listing agent: {e}")
        raise HTTPException(status_code=400, detail=f"Error in sending message to listing agent: {e}")

    return JSONResponse(content="I will inform you as soon as the listing agent confirms the property showing. The notification has been sent to them successfully.")


class ListingRealtorConfirmation(BaseModel):
    date: str = Field(default="date_test")
    time: str = Field(default="time_test")
    session_id: str = Field(default="")
    confirmation: str = Field(default="")

@router.post('/listing_realtor/confirmation')
async def listing_realtor_sign_up(request: ListingRealtorConfirmation, db: Session = Depends(get_db)):

    listing_selected_date = request.date
    listing_selected_time = request.time
    session_id = request.session_id
    confirmation = request.confirmation

    logger.warning(f"Listing realtore - listing_selected_date: {listing_selected_date}, listing_selected_time: {listing_selected_time}, session_id: {session_id}, confirmation: {confirmation}.")
    try:
        property = crud.get_property_by_session_id(db, session_id=session_id)
        listing_user = crud.get_user_by_phone_number(db, phone_number=property.listing_agent_phone_number)
    except Exception as e:
        logger.error(f"Error in creating user: {e}")
        raise HTTPException(status_code=400, detail=f"property not found with this session id, Error: {str(e)}")
    if not property:
        raise HTTPException(status_code=400, detail="property not found with this session id")
    property.listing_selected_date = listing_selected_date
    property.listing_selected_time = listing_selected_time
    if confirmation == "confirmed":
        logger.warning(f"Property Schudule is confirmed by listing agent.")
        property.status = "confirmed"
        listing_agent_body = f"Your showing at {property.address} (MLS # {property.mls_number}) is confirmed on {listing_selected_date} at {listing_selected_time}. I'll send you a reminder the day before to ensure you're prepared."
        buyer_agent_body = f"Your showing at {property.address} (MLS # {property.mls_number}) is confirmed by {listing_user.full_name} on {listing_selected_date} at {listing_selected_time}. I'll send you a reminder the day before to ensure you're prepared."
    elif confirmation == "cancelled":
        logger.warning(f"Property Schudule is cancelled by listing agent.")
        property.status = "cancelled"
        listing_agent_body = f"Thank you for letting us know. We will inform the buyer that the showing has been cancelled."
        buyer_agent_body = f"Unfortunately, the listing agent has cancelled the showing. We apologize for any inconvenience caused."
    elif confirmation == "reschedule":
        logger.warning(f"Property Schudule is rescheduled by listing agent. because of listing_selected_date: {listing_selected_date}, listing_selected_time: {listing_selected_time} and buyer_selected_date: {property.buyer_selected_date}, buyer_selected_time: {property.buyer_selected_time}")
        property.status = "rescheduled"
        listing_agent_body = f"Thank you for letting us know. I will inform the buyer agent that you have rescheduled the showing on {listing_selected_date} at {listing_selected_time}."
        buyer_agent_body = f"The listing agent for the property at {property.address} (MLS # {property.mls_number}) has rescheduled the showing on {listing_selected_date} at {listing_selected_time}. Please confirm if this new time works for you."
    else:
        raise HTTPException(status_code=400, detail="Invalid confirmation status")

    logger.warning(f"Property Schudule is {confirmation} by listing agent. listing_agent_body: {listing_agent_body}, buyer_agent_body: {buyer_agent_body}")
    try:
        logger.info(f"Sending message to listing agent from: {ai_agnet_number}, body: {listing_agent_body}, to: {property.buyer_agent_phone_number}")
        payload  = create_payload_for_whatsapp_message(from_number=property.buyer_agent_phone_number, to_number=ai_agnet_number, body=buyer_agent_body)
        headers = {"Content-Type": "application/json"}
        response = requests.post(n8n_webhook_url, headers=headers, data=json.dumps(payload))
        logger.info(f"Response for whatsapp webhook: {response.text}")

    except Exception as e:
        logger.error(f"Error in sending message to buyer agent: {e}")
        raise HTTPException(status_code=400, detail=f"Error in sending message to buyer agent: {e}")
    db.commit()
    return JSONResponse(content=listing_agent_body)





# @router.post("/webhook/sms")
# async def receive_sms(request: Request):
#     form_data = await request.form()
#     logger.warning(f"Received SMS: {form_data}")
#     sender = form_data.get("From")[9:]
#     message_body = form_data.get("Body")

#     logger.warning(f"Received SMS from {sender}: {message_body}")
#     # # Reply to the sender
#     # response = MessagingResponse()
#     # response.message(f"Hello! You sent: {message_body}")

#     # return str(response)


@router.get('/helth_check')
async def helth_check():
    logger.warning(f"singup request: Comes")
    return JSONResponse(content="Success")

@router.get('/')
async def test():
    logger.warning(f"test request: Comes")
    return JSONResponse(content="Go to /docs")


@router.post('/chatbot')
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    num_media = int(form_data.get('NumMedia', 0))
    phone_number = form_data.get("From")[9:]
    profile_name = form_data.get("ProfileName")
    user_query = form_data.get("Body")
    logger.warning(f"num_media: {num_media}, phone_number: {phone_number}, ProfileName: {profile_name}, user_query: {user_query}")

    user = crud.get_user_by_phone_number(db, phone_number=phone_number)
    if not user:
        payload = {
            "input_value": user_query,
            "session_id": phone_number
        }
        logger.info(f"Payload: {payload}")
        headers = {
            'Content-Type': 'application/json'
        }
        url = "https://workflows.kickcall.ai/api/v1/run/067c7617-4758-4f07-8f4e-457b4d10dbb6?stream=false&user_id=1"

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            logger.info(f"[Langflow][run] Response status code received: {response.status_code}")

            if response.status_code == 200:
                response_json = response.json()
                logger.info(f"[Langflow][run] Response: {response_json}")
                output_text = response_json["outputs"][0]["outputs"][0]["results"]["message"]["data"]["text"]

                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(output_text)

                return Response(content=str(bot_resp), media_type="application/xml")
            else:
                logger.info(f"Error: Received status code {response.status_code}")
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("I'm sorry, I couldn't process your request at the moment. Please try again later.")
                return Response(content=str(bot_resp), media_type="application/xml")

        except Exception as e:
            logger.info(f"Error in processing user query: {e}")
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("I'm sorry, an unexpected error occurred. Please try again later.")
            return Response(content=str(bot_resp), media_type="application/xml")

    if user.type == "buyer":
        payload = {
            "input_value": user_query,
            "session_id": phone_number
        }
        logger.info(f"Payload: {payload}")
        headers = {
            'Content-Type': 'application/json'
        }
        url = "https://workflows.kickcall.ai/api/v1/run/c94b14f5-d7a7-4fc8-89d8-eb672716c778?stream=false&user_id=1"

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            logger.info(f"[Langflow][run] Response status code received: {response.status_code}")

            if response.status_code == 200:
                response_json = response.json()
                logger.info(f"[Langflow][run] Response: {response_json}")
                output_text = response_json["outputs"][0]["outputs"][0]["results"]["message"]["data"]["text"]

                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body(output_text)

                return Response(content=str(bot_resp), media_type="application/xml")
            else:
                logger.info(f"Error: Received status code {response.status_code}")
                bot_resp = MessagingResponse()
                msg = bot_resp.message()
                msg.body("I'm sorry, I couldn't process your request at the moment. Please try again later.")
                return Response(content=str(bot_resp), media_type="application/xml")

        except Exception as e:
            logger.info(f"Error in processing user query: {e}")
            bot_resp = MessagingResponse()
            msg = bot_resp.message()
            msg.body("I'm sorry, an unexpected error occurred. Please try again later.")
            return Response(content=str(bot_resp), media_type="application/xml")

    elif user.type == "listing":
        logger.info(f"Message received by listing realto's ")
        active_session_id = user.active_session_id

    else:
        logger.error(f"Message received by  type : {user.type}")

