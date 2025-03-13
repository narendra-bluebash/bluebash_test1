from app.db import crud
from app.db import models
from twilio.rest import Client
import os, json, random, requests
from sqlalchemy.orm import Session
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from app.utils.log_utils import setup_logger
from app.db.database import SessionLocal, engine
from app.services.realtor_service import RealtorService
from fastapi import Request, Depends, APIRouter, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
from app.services.properties_service import get_property_by_address_or_mls_number
from app.services.agent_service import verify_agent_by_agent_id_and_broker_name
from app.db.schemas import BuyerRealtorConfirmation, BuyerRealtorSignUP, CreatebookingRequest, GetBooking, ListingRealtorConfirmation, ListingRealtorSignUP, MessageRequestSignUP, CollectFeedback

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


@router.post('/realtor/get_properties')
async def get_properties(address: str=None, mls_number: str=None, db: Session = Depends(get_db)):
    logger.warning(f"get_properties request: address: {address}, mls_number: {mls_number}")
    response = get_property_by_address_or_mls_number(mls_number=mls_number, address=address)
    return JSONResponse(content=response)

@router.post('/realtor/verify_agent')
async def verify_agent(agent_id: str, broker_name: str, db: Session = Depends(get_db)):
    logger.warning(f"verify_agent request: agent_id: {agent_id}, broker_name: {broker_name}")
    return verify_agent_by_agent_id_and_broker_name(agent_id=agent_id, broker_name=broker_name)

@router.post('/realtor/signup')
async def realtor_sign_up(request: MessageRequestSignUP, db: Session = Depends(get_db)):
    logger.warning(f"singup request: {request}")
    user = crud.create_user(db, full_name=request.full_name, phone_number=request.phone_number, type=request.type, agent_id=request.agent_id, broker_name=request.broker_name)
    if not user:
        raise HTTPException(status_code=400, detail="User creation failed")
    return JSONResponse(content="user is signed up sucessfully.")


@router.post('/realtor/create_booking')
async def create_booking(request: CreatebookingRequest, db: Session = Depends(get_db)):
    logger.warning(f"Create booking request: {request}")
    try:
        booking = crud.create_booking(db, buyer_agent_phone_number=request.buyer_agent_phone_number,
                                            address=request.address, mls_number=request.mls_number, buyer_selected_date=request.buyer_selected_date,
                                            buyer_selected_time=request.buyer_selected_time, listing_agent_phone_number=request.listing_agent_phone_number,
                                            listing_agent_session_id=request.listing_agent_session_id, status=request.status)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in creating booking: {e}")
        raise HTTPException(status_code=400, detail="booking creation failed")
    return JSONResponse(content=booking)


@router.post('/realtor/book_showings')
async def buyer_book_showings(request: ListingRealtorSignUP, db: Session = Depends(get_db)):
    logger.warning(f"Listing realtor singup request: {request}")
    realtor_service = RealtorService()
    response = realtor_service.book_showings(db, request.booking_address, request.mls_number, request.date, request.time, request.buyer_agent_phone_number)
    logger.warning(f"Listing realtor sign up response: {response}")
    return JSONResponse(content=response)

@router.post('/buyer_realtor/get_booking')
async def buyer_realtor_get_booking(request: GetBooking, db: Session = Depends(get_db)):
    realtor_service = RealtorService()
    response = realtor_service.buyer_realtor_get_booking(db, request.query_type, booking_id=request.booking_id, mls_number=request.mls_number, phone_number=request.phone_number)
    logger.warning(f"Get booking response: {response}")
    return JSONResponse(content=response)

@router.post('/listing_realtor/get_booking')
async def listing_realtor_get_booking(request: GetBooking, db: Session = Depends(get_db)):
    realtor_service = RealtorService()
    response = realtor_service.listing_realtor_get_booking(db, request.query_type, booking_id=request.booking_id, mls_number=request.mls_number, phone_number=request.phone_number)
    logger.warning(f"Get booking response: {response}")
    return JSONResponse(content=response)

@router.post('/buyer_realtor/signup')
async def buyer_realtor_sign_up(request: BuyerRealtorSignUP, db: Session = Depends(get_db)):
    logger.warning(f"Buyer realtor singup request: {request}")
    type = "buyer"
    realtor_service = RealtorService()
    response = realtor_service.buyer_realtor_sign_up(db, request.full_name, request.agent_id, request.broker_name, request.phone_number, type)
    logger.warning(f"Buyer realtor sign up response: {response}")
    return JSONResponse(content=response)

@router.post('/buyer_realtor/confirmation')
async def buyer_realtor_confirmation(request: BuyerRealtorConfirmation, db: Session = Depends(get_db)):
    logger.warning(f"Buyer realtor confirmation request: {request}")
    realtor_service = RealtorService()
    response = realtor_service.buyer_realtor_confirmation(db, request.phone_number, request.booking_id, request.mls_number, request.date, request.time, request.confirmation, request.reason)
    logger.warning(f"Buyer realtor confirmation response: {response}")
    return JSONResponse(content=response)

@router.post('/listing_realtor/confirmation')
async def listing_realtor_confirmation(request: ListingRealtorConfirmation, db: Session = Depends(get_db)):
    logger.warning(f"Listing realtor confirmation request: {request}")
    realtor_service = RealtorService()
    response = realtor_service.listing_realtor_confirmation(db, request.session_id, request.date, request.time, request.confirmation, request.reason)
    logger.warning(f"Listing realtor confirmation response: {response}")
    return JSONResponse(content=response)

@router.post('/realtor/collect_feedback')
async def collect_feedback(request: CollectFeedback, db: Session = Depends(get_db)):
    realtor_service = RealtorService()
    response = realtor_service.collect_feedback(db, request.phone_number, request.booking_id, request.mls_number, request.feedback_msg)
    logger.warning(f"Collect feedback response: {response}")
    return JSONResponse(content=response)

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

