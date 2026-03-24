# DormDash WhatsApp Chatbot

This project implements a WhatsApp chatbot for the DormDash delivery service using Twilio. The chatbot allows users to create delivery requests through WhatsApp, providing a seamless experience for campus deliveries.

## Project Structure

```
dormdash-whatsapp
├── src
│   ├── main.py          # Entry point of the FastAPI application
│   ├── whatsapp.py      # Logic for handling incoming WhatsApp messages
│   ├── crud.py          # CRUD operations for managing delivery requests
│   ├── models.py        # SQLAlchemy models for delivery requests
│   ├── schemas.py       # Pydantic schemas for validating incoming data
│   ├── database.py      # Database connection and session management
│   └── state.py         # Conversation state and user data management
├── requirements.txt      # Project dependencies
├── .env.example          # Example environment variables
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd dormdash-whatsapp
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in the required Twilio credentials.

5. **Run the application:**
   ```
   uvicorn src.main:app --reload
   ```

## Usage

- Send a message to the Twilio WhatsApp number to start interacting with the DormDash chatbot.
- Follow the prompts to create a delivery request by providing the necessary information.

## Features

- Handles incoming WhatsApp messages and responds in TwiML format.
- Tracks user conversation state to guide them through the delivery request process.
- Integrates with existing CRUD operations to create delivery requests in the database.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.