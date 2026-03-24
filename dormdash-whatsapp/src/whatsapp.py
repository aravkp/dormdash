from fastapi import FastAPI, Request
from fastapi.responses import XMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from crud import create_delivery
from schemas import DeliveryCreate
from state import user_states, user_data

app = FastAPI()

@app.post("/whatsapp", response_class=XMLResponse)
async def handle_whatsapp_message(request: Request):
    form = await request.form()
    message_body = form.get("Body").strip().lower()
    sender_number = form.get("From")

    # Initialize user state if not present
    if sender_number not in user_states:
        user_states[sender_number] = "start"

    response = MessagingResponse()

    if user_states[sender_number] == "start":
        response.message("Welcome to DormDash!\nWhat service do you need?\n\n1. Mail\n2. Laundry")
        user_states[sender_number] = "awaiting_service"
    
    elif user_states[sender_number] == "awaiting_service":
        if message_body == "1":
            user_states[sender_number] = "mail_ashoka_id"
            response.message("Please provide your Ashoka ID.")
        elif message_body == "2":
            user_states[sender_number] = "laundry_ashoka_id"
            response.message("Please provide your Ashoka ID.")
        else:
            response.message("Please select a valid option: 1 for Mail, 2 for Laundry.")
    
    elif user_states[sender_number] in ["mail_ashoka_id", "laundry_ashoka_id"]:
        user_data[sender_number] = {"ashoka_id": message_body}
        user_states[sender_number] = "residence_hall"
        response.message("Please provide your residence hall.")

    elif user_states[sender_number] == "residence_hall":
        user_data[sender_number]["residence_hall"] = message_body
        user_states[sender_number] = "room_number"
        response.message("Please provide your room number.")

    elif user_states[sender_number] == "room_number":
        user_data[sender_number]["room_number"] = message_body
        if user_states[sender_number].startswith("mail"):
            user_states[sender_number] = "number_of_items"
            response.message("Please provide the number of items.")
        else:
            user_states[sender_number] = "number_of_bags"
            response.message("Please provide the number of bags.")

    elif user_states[sender_number] in ["number_of_items", "number_of_bags"]:
        if user_states[sender_number] == "number_of_items":
            user_data[sender_number]["number_of_items"] = message_body
        else:
            user_data[sender_number]["number_of_bags"] = message_body
        
        user_states[sender_number] = "phone_number"
        response.message("Please provide your phone number.")

    elif user_states[sender_number] == "phone_number":
        user_data[sender_number]["phone_number"] = message_body
        service_type = "Mail" if user_states[sender_number].startswith("mail") else "Laundry"
        delivery_data = DeliveryCreate(
            name=user_data[sender_number]["ashoka_id"],
            ashoka_id=user_data[sender_number]["ashoka_id"],
            residence_hall=user_data[sender_number]["residence_hall"],
            room_number=user_data[sender_number]["room_number"],
            service_type=service_type,
            phone_number=user_data[sender_number]["phone_number"]
        )
        create_delivery(delivery_data)
        response.message("Your request has been created successfully!")
        # Reset user state
        user_states.pop(sender_number, None)
        user_data.pop(sender_number, None)

    return response