from pydantic import BaseModel

class DeliveryCreate(BaseModel):
    name: str
    ashoka_id: str
    residence_hall: str
    room_number: str
    service_type: str
    phone_number: str
    number_of_items: int = None  # For mail service
    number_of_bags: int = None    # For laundry service