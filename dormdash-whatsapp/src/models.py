from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ashoka_id = Column(String, index=True)
    residence_hall = Column(String, index=True)
    room_number = Column(String, index=True)
    service_type = Column(String, index=True)
    phone_number = Column(String, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    courier = Column(String, nullable=True)