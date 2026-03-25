from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

try:
    from . import crud, models, schemas
    from .database import SessionLocal, engine
except ImportError:
    import crud  # type: ignore
    import models  # type: ignore
    import schemas  # type: ignore
    from database import SessionLocal, engine  # type: ignore

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DormDash API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins now
    allow_credentials=True,
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/deliveries", response_model=schemas.DeliveryResponse)
def create_delivery(delivery: schemas.DeliveryCreate, db: Session = Depends(get_db)):
    return crud.create_delivery(db=db, delivery=delivery)

@app.get("/deliveries", response_model=List[schemas.DeliveryResponse])
def list_deliveries(status: Optional[str] = Query(None, description="Filter by status: pending/approved/accepted/delivered"), db: Session = Depends(get_db)):
    return crud.get_all_deliveries(db, status_filter=status)

@app.get("/deliveries/open", response_model=List[schemas.DeliveryResponse])
def list_open(courier_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    # returns approved deliveries so couriers see only approved items
    return crud.get_open_deliveries(db, courier_id=courier_id)

@app.get("/deliveries/{delivery_id}", response_model=schemas.DeliveryResponse)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    d = crud.get_delivery(db, delivery_id)
    if not d:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return d

@app.get("/deliveries/courier/{courier_id}", response_model=List[schemas.DeliveryResponse])
def list_by_courier(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_deliveries_by_courier(db, courier_id)

@app.get("/deliveries/courier/{courier_id}/accepted", response_model=List[schemas.DeliveryResponse])
def list_courier_accepted(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_courier_deliveries(db, courier_id)

@app.get("/deliveries/courier/{courier_id}/history", response_model=List[schemas.DeliveryResponse])
def list_courier_history(courier_id: str, db: Session = Depends(get_db)):
    return crud.get_courier_delivery_history(db, courier_id)

@app.post("/deliveries/{delivery_id}/accept", response_model=schemas.DeliveryResponse)
def accept_delivery(delivery_id: int, accept: schemas.DeliveryAccept, db: Session = Depends(get_db)):
    # accept only if delivery was approved
    return crud.accept_delivery(db, delivery_id, accept.courier)

@app.post("/deliveries/{delivery_id}/complete", response_model=schemas.DeliveryResponse)
def complete_delivery(delivery_id: int, db: Session = Depends(get_db)):
    return crud.complete_delivery(db, delivery_id)

@app.post("/deliveries/{delivery_id}/approve", response_model=schemas.DeliveryResponse)
def approve_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = crud.approve_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

@app.post("/deliveries/{delivery_id}/assign", response_model=schemas.DeliveryResponse)
def assign_delivery(delivery_id: int, assign: schemas.DeliveryAccept, db: Session = Depends(get_db)):
    return crud.assign_delivery(db, delivery_id, assign.courier)

@app.post("/deliveries/{delivery_id}/reject", response_model=schemas.DeliveryResponse)
def reject_delivery(delivery_id: int, db: Session = Depends(get_db)):
    delivery = crud.reject_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery
