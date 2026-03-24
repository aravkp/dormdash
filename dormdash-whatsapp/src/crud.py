from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models import Delivery
from schemas import DeliveryCreate
from datetime import datetime

def create_delivery(db: Session, delivery: DeliveryCreate) -> Delivery:
    """Create a new delivery request."""
    db_delivery = Delivery(
        name=delivery.name,
        ashoka_id=delivery.ashoka_id,
        residence_hall=delivery.residence_hall,
        room_number=delivery.room_number,
        service_type=delivery.service_type,
        phone_number=delivery.phone_number,
        status="pending"
    )
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

def get_open_deliveries(db: Session) -> list[Delivery]:
    """Get all deliveries with status 'pending'."""
    return db.query(Delivery).filter(Delivery.status == "pending").all()

def get_all_deliveries(db: Session, status_filter: str = None) -> list[Delivery]:
    """Get all deliveries, optionally filtered by status."""
    query = db.query(Delivery)
    if status_filter:
        query = query.filter(Delivery.status == status_filter)
    # Order by newest first
    query = query.order_by(Delivery.created_at.desc())
    return query.all()

def get_courier_deliveries(db: Session, courier_id: str) -> list[Delivery]:
    """Get all 'accepted' deliveries assigned to a specific courier."""
    return (
        db.query(Delivery)
        .filter(Delivery.courier == courier_id, Delivery.status == "accepted")
        .all()
    )

def get_courier_delivery_history(db: Session, courier_id: str) -> list[Delivery]:
    """Get all 'delivered' deliveries assigned to a specific courier."""
    return (
        db.query(Delivery)
        .filter(Delivery.courier == courier_id, Delivery.status == "delivered")
        .order_by(Delivery.completed_at.desc())
        .all()
    )

def get_delivery(db: Session, delivery_id: int) -> Delivery:
    """Get a delivery by ID."""
    return db.query(Delivery).filter(Delivery.id == delivery_id).first()

def accept_delivery(db: Session, delivery_id: int, courier: str) -> Delivery:
    """Assign a courier to a delivery and change status to 'accepted'."""
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        return None
    if delivery.status != "pending":
        raise ValueError(f"Delivery {delivery_id} cannot be accepted. Current status: {delivery.status}")
    delivery.courier = courier
    delivery.status = "accepted"
    db.commit()
    db.refresh(delivery)
    return delivery

def complete_delivery(db: Session, delivery_id: int) -> Delivery:
    """Mark a delivery as 'delivered'."""
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        return None
    if delivery.status != "accepted":
        raise ValueError(f"Delivery {delivery_id} cannot be completed. Current status: {delivery.status}")
    delivery.status = "delivered"
    delivery.completed_at = datetime.now()
    db.commit()
    db.refresh(delivery)
    return delivery