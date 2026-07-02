from sqlalchemy.orm import Session
from models.incident import Incident
from schemas.incident import IncidentCreate

def get_all_incidents(db: Session):
    return db.query(Incident).all()

def create_incident(db: Session, data: IncidentCreate):
    incident = Incident(**data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident