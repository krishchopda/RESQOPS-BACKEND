from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.incident import IncidentCreate, IncidentResponse
from services.incident_service import get_all_incidents, create_incident
from typing import List

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(status: str = "active", db: Session = Depends(get_db)):
    """
    Returns incidents filtered by status. Defaults to only 'active' incidents
    so resolved cases drop off the dashboard and map automatically.
    Pass ?status=all to see every incident regardless of status.
    """
    incidents = get_all_incidents(db)
    if status == "all":
        return incidents
    return [i for i in incidents if getattr(i, "status", "active") == status]

@router.post("/", response_model=IncidentResponse)
def add_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    return create_incident(db, incident)