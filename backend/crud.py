from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

import models
from schemas import DeliveryCreate

def create_delivery(db: Session, delivery: DeliveryCreate) -> models.Delivery:
    svc = (delivery.service_type or "").lower()
    phone = (delivery.phone_number or "").strip()
    ashoka = (delivery.ashoka_id or "").strip()

    # basic required validation
    if not delivery.residence_hall:
        raise HTTPException(status_code=400, detail="residence_hall is required")
    if not delivery.room_number:
        raise HTTPException(status_code=400, detail="room_number is required")
    if not phone:
        raise HTTPException(status_code=400, detail="phone_number is required")
    if not phone.isdigit() or len(phone) != 10:
        raise HTTPException(status_code=400, detail="phone_number must be exactly 10 digits")
    if not ashoka:
        raise HTTPException(status_code=400, detail="ashoka_id is required")
    if not ashoka.isdigit() or len(ashoka) != 10:
        raise HTTPException(status_code=400, detail="ashoka_id must be exactly 10 digits")

    # service-specific validation
    if svc == "mail":
        if not delivery.mail_delivery_day:
            raise HTTPException(status_code=400, detail="mail_delivery_day is required for Mail")
        if not delivery.mail_delivery_slot:
            raise HTTPException(status_code=400, detail="mail_delivery_slot is required for Mail")
    if svc == "laundry":
        if not delivery.laundry_type:
            raise HTTPException(status_code=400, detail="laundry_type is required for Laundry")
        if not delivery.laundry_code:
            raise HTTPException(status_code=400, detail="laundry_code is required for Laundry")
        laundry_type = (delivery.laundry_type or "").lower()
        if laundry_type == "drop-off":
            if not delivery.laundry_drop_day:
                raise HTTPException(status_code=400, detail="laundry_drop_day is required for Laundry drop-off")
            if not delivery.laundry_drop_time:
                raise HTTPException(status_code=400, detail="laundry_drop_time is required for Laundry drop-off")
        elif laundry_type == "pickup":
            if not delivery.laundry_pickup_days:
                raise HTTPException(status_code=400, detail="laundry_pickup_days is required for Laundry pickup")
            if not delivery.laundry_pickup_time:
                raise HTTPException(status_code=400, detail="laundry_pickup_time is required for Laundry pickup")
        elif laundry_type == "dropoff+pickup":
            if not delivery.laundry_drop_day:
                raise HTTPException(status_code=400, detail="laundry_drop_day is required for Laundry dropoff+pickup")
            if not delivery.laundry_drop_time:
                raise HTTPException(status_code=400, detail="laundry_drop_time is required for Laundry dropoff+pickup")
            if not delivery.laundry_pickup_days:
                raise HTTPException(status_code=400, detail="laundry_pickup_days is required for Laundry dropoff+pickup")
            if not delivery.laundry_pickup_time:
                raise HTTPException(status_code=400, detail="laundry_pickup_time is required for Laundry dropoff+pickup")
        else:
            raise HTTPException(status_code=400, detail="laundry_type must be drop-off, pickup, or dropoff+pickup")
    if svc == "gate" or svc == "gate pickup":
        if not delivery.gate_number:
            raise HTTPException(status_code=400, detail="gate_number is required for Gate Pickup")
        if not delivery.package_type:
            raise HTTPException(status_code=400, detail="package_type is required for Gate Pickup")
    if svc == "tuckshop" or svc == "tuck shop":
        if not delivery.items_requested:
            raise HTTPException(status_code=400, detail="items_requested is required for Tuck Shop")
        if not delivery.tuck_shop_location:
            raise HTTPException(status_code=400, detail="tuck_shop_location is required for Tuck Shop")
    if svc == "within-residence-hall" or svc == "within residence hall":
        if not delivery.order_from:
            raise HTTPException(status_code=400, detail="order_from is required for Within-Residence-Hall")

    db_obj = models.Delivery(
        # include name
        name=delivery.name,
        ashoka_id=ashoka,
        residence_hall=delivery.residence_hall,
        room_number=delivery.room_number,
        phone_number=phone,
        service_type=delivery.service_type,
        laundry_code=delivery.laundry_code,
        laundry_type=delivery.laundry_type,
        laundry_drop_day=delivery.laundry_drop_day,
        laundry_drop_time=delivery.laundry_drop_time,
        laundry_pickup_days=delivery.laundry_pickup_days,
        laundry_pickup_time=delivery.laundry_pickup_time,
        mail_delivery_day=delivery.mail_delivery_day,
        mail_delivery_slot=delivery.mail_delivery_slot,
        gate_number=delivery.gate_number,
        package_type=delivery.package_type,
        additional_details=delivery.additional_details,
        items_requested=delivery.items_requested,
        tuck_shop_location=delivery.tuck_shop_location,
        order_from=delivery.order_from,
        transaction_id=delivery.transaction_id,
        payment_status=delivery.payment_status or "pending",
        price=delivery.price,
        status="pending",
        parent_delivery_id=None
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_all_deliveries(db: Session, status_filter: Optional[str] = None) -> List[models.Delivery]:
    q = db.query(models.Delivery)
    if status_filter:
        q = q.filter(models.Delivery.status == status_filter)
    return q.order_by(models.Delivery.created_at.desc()).all()

def get_open_deliveries(db: Session, courier_id: Optional[str] = None) -> List[models.Delivery]:
    # couriers should only see approved deliveries
    q = db.query(models.Delivery).filter(models.Delivery.status == "approved")
    if courier_id:
        cid = courier_id.strip().lower()
        q = q.filter((models.Delivery.courier.is_(None)) | (func.lower(models.Delivery.courier) == cid))
    return q.order_by(models.Delivery.created_at.desc()).all()

def get_delivery(db: Session, delivery_id: int) -> Optional[models.Delivery]:
    return db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()

def get_deliveries_by_courier(db: Session, courier_id: str) -> List[models.Delivery]:
    cid = courier_id.strip().lower()
    return db.query(models.Delivery).filter(func.lower(models.Delivery.courier) == cid).order_by(models.Delivery.created_at.desc()).all()

def get_courier_deliveries(db: Session, courier_id: str) -> List[models.Delivery]:
    cid = courier_id.strip().lower()
    return db.query(models.Delivery).filter(func.lower(models.Delivery.courier) == cid, models.Delivery.status == "accepted").order_by(models.Delivery.created_at.desc()).all()

def get_courier_delivery_history(db: Session, courier_id: str) -> List[models.Delivery]:
    cid = courier_id.strip().lower()
    return db.query(models.Delivery).filter(func.lower(models.Delivery.courier) == cid, models.Delivery.status == "delivered").order_by(models.Delivery.created_at.desc()).all()

def accept_delivery(db: Session, delivery_id: int, courier_id: str) -> models.Delivery:
    d = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    # only approved deliveries can be accepted
    if d.status != "approved":
        raise HTTPException(status_code=400, detail="Delivery not available for acceptance")
    input_courier = (courier_id or "").strip()
    if not input_courier:
        raise HTTPException(status_code=400, detail="courier is required")
    if d.courier and d.courier.strip().lower() != input_courier.lower():
        raise HTTPException(status_code=400, detail="Delivery is assigned to another courier")
    d.courier = input_courier
    d.status = "accepted"
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

def assign_delivery(db: Session, delivery_id: int, courier_id: str) -> models.Delivery:
    d = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if d.status != "approved":
        raise HTTPException(status_code=400, detail="Courier can only be assigned on approved deliveries")
    input_courier = (courier_id or "").strip()
    if not input_courier:
        raise HTTPException(status_code=400, detail="courier is required")
    d.courier = input_courier
    d.status = "accepted"  # Set status to accepted when courier is assigned
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

def complete_delivery(db: Session, delivery_id: int) -> models.Delivery:
    d = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    d.status = "delivered"
    db.add(d)
    db.commit()
    db.refresh(d)
    
    # If this is a dropoff+pickup laundry, create the pickup delivery
    if d.service_type and d.service_type.lower() == "laundry":
        laundry_type = (d.laundry_type or "").lower()
        if laundry_type == "dropoff+pickup":
            # Create corresponding pickup delivery
            pickup = models.Delivery(
                name=d.name,
                ashoka_id=d.ashoka_id,
                residence_hall=d.residence_hall,
                room_number=d.room_number,
                phone_number=d.phone_number,
                service_type="Laundry",
                laundry_code=d.laundry_code,
                laundry_type="pickup",
                laundry_pickup_days=d.laundry_pickup_days,
                laundry_pickup_time=d.laundry_pickup_time,
                transaction_id=d.transaction_id,
                payment_status="paid",
                price=d.price,
                status="pending",
                parent_delivery_id=d.id
            )
            db.add(pickup)
            db.commit()
    
    return d

def approve_delivery(db: Session, delivery_id: int) -> Optional[models.Delivery]:
    d = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not d:
        return None
    d.status = "approved"
    db.add(d)
    db.commit()
    db.refresh(d)
    return d
