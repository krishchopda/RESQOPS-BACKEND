from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.incident import IncidentCreate, IncidentResponse
from services.incident_service import get_all_incidents, create_incident
from typing import List

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    return get_all_incidents(db)

@router.post("/", response_model=IncidentResponse)
def add_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    return create_incident(db, incident)