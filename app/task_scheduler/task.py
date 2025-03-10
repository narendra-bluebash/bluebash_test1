import requests, os, json
from celery import Celery
from app.utils.log_utils import setup_logger

logger = setup_logger("task")

ai_agnet_number = os.getenv("AI_AGENT_NUMBER")
n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
app.conf.broker_connection_retry_on_startup = True

@app.task
def schedule_n8n_workflow(from_number, body):
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
        logger.info(f"Payload for whatsapp webhook: {payload}")
        headers = {"Content-Type": "application/json"}
        response = requests.post(n8n_webhook_url, headers=headers, data=json.dumps(payload))
        logger.info(f"Response for whatsapp webhook: {response.text}")
    except Exception as e:
        logger.error(f"Error in sending message to agent: {e}")
        return f"Error in sending message to agent: {str(e)}"
    return "Message sent successfully"
