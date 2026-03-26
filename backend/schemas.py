from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeliveryBase(BaseModel):
    # NEW: name support
    name: Optional[str] = None
    ashoka_id: Optional[str] = None
    residence_hall: Optional[str] = None
    room_number: Optional[str] = None
    phone_number: Optional[str] = None
    service_type: Optional[str] = None

    # optional conditional fields
    laundry_code: Optional[str] = None
    laundry_type: Optional[str] = None
    laundry_drop_day: Optional[str] = None
    laundry_drop_time: Optional[str] = None
    laundry_pickup_days: Optional[str] = None
    laundry_pickup_time: Optional[str] = None
    mail_delivery_day: Optional[str] = None
    mail_delivery_slot: Optional[str] = None
    gate_number: Optional[str] = None
    package_type: Optional[str] = None
    additional_details: Optional[str] = None
    items_requested: Optional[str] = None
    tuck_shop_location: Optional[str] = None
    order_from: Optional[str] = None

    # payment fields
    transaction_id: Optional[str] = None
    payment_status: Optional[str] = None
    price: Optional[int] = None

class DeliveryCreate(DeliveryBase):
    pass

class DeliveryResponse(DeliveryBase):
    id: int
    status: Optional[str] = None
    courier: Optional[str] = None
    parent_delivery_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DeliveryAccept(BaseModel):
    courier: str


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys


class VapidPublicKeyResponse(BaseModel):
    public_key: Optional[str] = None


class NotificationTokenCreate(BaseModel):
    token: str


class FirebaseWebPushKeyResponse(BaseModel):
    web_push_key: Optional[str] = None
