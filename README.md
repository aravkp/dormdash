# DormDash Backend

A minimal MVP backend for a campus delivery service.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
cd backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

- `backend/main.py` - FastAPI application and route handlers
- `backend/database.py` - Database connection and session management
- `backend/models.py` - SQLAlchemy database models
- `backend/schemas.py` - Pydantic schemas for request/response validation
- `backend/crud.py` - Database CRUD operations

## API Endpoints

- `POST /deliveries` - Create a new delivery request
- `GET /deliveries/open` - Get all pending deliveries
- `POST /deliveries/{delivery_id}/accept` - Accept a delivery (requires courier name)
- `POST /deliveries/{delivery_id}/complete` - Mark delivery as completed
