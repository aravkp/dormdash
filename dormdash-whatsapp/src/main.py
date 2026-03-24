from fastapi import FastAPI, Request
from fastapi.responses import XMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from whatsapp import handle_whatsapp_message

app = FastAPI()

@app.post("/whatsapp", response_class=XMLResponse)
async def whatsapp_webhook(request: Request):
    body = await request.body()
    response = handle_whatsapp_message(body)
    return response