
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
from dotenv import load_dotenv
load_dotenv()

logger = setup_logger("router")
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


class ListingRealtorSignUP(BaseModel):
    property_address: str = Field(default="property_address_test")
    mls_number: str = Field(default="mls_number_test")
    date: str = Field(default="date_test")
    time: str = Field(default="time_test")

@router.post('/listing_realtor/signup')
async def listing_realtor_sign_up(request: ListingRealtorSignUP, db: Session = Depends(get_db)):
    logger.warning(f"Listing realtor singup request: {request}")

    property_address = request.property_address
    mls_number = request.mls_number
    date = request.date
    time = request.time

    logger.warning(f"Listing realtore - property_address: {property_address}, mls_number: {mls_number}, date: {date}, time: {time}")
    full_name = "king123"
    phone_number = "123"
    type = "listing"

    user = crud.create_user(db, full_name=full_name, phone_number=phone_number, type=type)
    if not user:
        raise HTTPException(status_code=400, detail="User creation failed")

    return JSONResponse(content="user is signed up sucessfully.")


@router.get('/helth_check')
async def helth_check():
    logger.warning(f"singup request: Comes")
    return JSONResponse(content="Success")

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
        current_session_id = user.current_session_id

    else:
        logger.error(f"Message received by  type : {user.type}")

