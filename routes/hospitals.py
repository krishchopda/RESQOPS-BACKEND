from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.hospital import HospitalCreate, HospitalResponse
from services.hospital_service import get_all_hospitals, create_hospital
from typing import List

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

@router.get("/", response_model=List[HospitalResponse])
def get_hospitals(db: Session = Depends(get_db)):
    return get_all_hospitals(db)

@router.post("/", response_model=HospitalResponse)
def add_hospital(hospital: HospitalCreate, db: Session = Depends(get_db)):
    return create_hospital(db, hospital)