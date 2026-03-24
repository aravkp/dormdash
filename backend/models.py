from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    # NEW: user name
    name = Column(String, nullable=True)

    # basic fields
    ashoka_id = Column(String, nullable=True)
    residence_hall = Column(String, nullable=True)
    room_number = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    # service
    service_type = Column(String, nullable=True)  # Mail, Laundry, Gate Pickup, Tuck Shop

    # optional service-specific fields
    laundry_code = Column(String, nullable=True)
    laundry_type = Column(String, nullable=True)  # drop-off, pickup
    laundry_drop_day = Column(String, nullable=True)
    laundry_drop_time = Column(String, nullable=True)
    laundry_pickup_days = Column(String, nullable=True)
    laundry_pickup_time = Column(String, nullable=True)
    mail_delivery_day = Column(String, nullable=True)
    mail_delivery_slot = Column(String, nullable=True)  # morning, evening
    gate_number = Column(String, nullable=True)
    package_type = Column(String, nullable=True)
    additional_details = Column(String, nullable=True)
    items_requested = Column(String, nullable=True)
    tuck_shop_location = Column(String, nullable=True)
    order_from = Column(String, nullable=True)

    # payment fields
    transaction_id = Column(String, nullable=True)
    payment_status = Column(String, default="pending", nullable=True)
    price = Column(Integer, nullable=True)

    # workflow
    status = Column(String, default="pending", nullable=False)  # pending, approved, accepted, delivered
    courier = Column(String, nullable=True)
    parent_delivery_id = Column(Integer, nullable=True)  # For pickup deliveries created from dropoff+pickup

    created_at = Column(DateTime, default=datetime.utcnow)
