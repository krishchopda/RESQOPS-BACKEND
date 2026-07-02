from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.ambulance import AmbulanceCreate, AmbulanceResponse
from services.ambulance_service import get_all_ambulances, create_ambulance
from typing import List

router = APIRouter(prefix="/ambulances", tags=["Ambulances"])

@router.get("/", response_model=List[AmbulanceResponse])
def get_ambulances(db: Session = Depends(get_db)):
    return get_all_ambulances(db)

@router.post("/", response_model=AmbulanceResponse)
def add_ambulance(ambulance: AmbulanceCreate, db: Session = Depends(get_db)):
    return create_ambulance(db, ambulance)