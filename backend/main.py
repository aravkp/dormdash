from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy.orm import Session

import crud, models
from database import get_db, init_db
from schemas import DeliveryCreate, DeliveryResponse, DeliveryAccept

app = FastAPI(title="DormDash API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/deliveries", response_model=DeliveryResponse)
def create_delivery_endpoint(delivery: DeliveryCreate, db: Session = Depends(get_db)):
    created = crud.create_delivery(db, delivery)
    return created

@app.get("/deliveries", response_model=List[DeliveryResponse])
def list_deliveries(status: Optional[str] = Query(None, description="Filter by status: pending/approved/accepted/delivered"), db: Session = Depends(get_db)):
    return crud.get_all_deliveries(db, status_filter=status)

@app.get("/deliveries/open", response_model=List[DeliveryResponse])
def list_open(courier_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    # returns approved deliveries so couriers see only approved items
    return crud.get_open_deliveries(db, courier_id=courier_id)

@app.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def get_delivery_endpoint(delivery_id: int, db: Session = Depends(get_db)):
    d = crud.get_delivery(db, delivery_id)
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return d

@app.get("/deliveries/courier/{courier_id}", response_model=List[DeliveryResponse])
def list_by_courier(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_deliveries_by_courier(db, courier_id)

@app.get("/deliveries/courier/{courier_id}/accepted", response_model=List[DeliveryResponse])
def list_courier_accepted(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_courier_deliveries(db, courier_id)

@app.get("/deliveries/courier/{courier_id}/history", response_model=List[DeliveryResponse])
def list_courier_history(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_courier_delivery_history(db, courier_id)

@app.post("/deliveries/{delivery_id}/accept", response_model=DeliveryResponse)
def accept_delivery_endpoint(delivery_id: int, accept: DeliveryAccept, db: Session = Depends(get_db)):
    # accept only if delivery was approved
    return crud.accept_delivery(db, delivery_id, accept.courier)

@app.post("/deliveries/{delivery_id}/complete", response_model=DeliveryResponse)
def complete_delivery_endpoint(delivery_id: int, db: Session = Depends(get_db)):
    return crud.complete_delivery(db, delivery_id)

@app.post("/deliveries/{delivery_id}/approve", response_model=DeliveryResponse)
def approve_delivery_endpoint(delivery_id: int, db: Session = Depends(get_db)):
    delivery = crud.approve_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

@app.post("/deliveries/{delivery_id}/assign", response_model=DeliveryResponse)
def assign_delivery_endpoint(delivery_id: int, assign: DeliveryAccept, db: Session = Depends(get_db)):
    return crud.assign_delivery(db, delivery_id, assign.courier)
