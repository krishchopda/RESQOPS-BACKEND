from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.ambulance import Ambulance
from models.incident import Incident
from models.hospital import Hospital
from pydantic import BaseModel

router = APIRouter(prefix="/assignments", tags=["Assignments"])

# In-memory assignment store (v1 — will move to DB table later)
active_assignments = {}

class AssignRequest(BaseModel):
    ambulance_id: int
    incident_id: int
    hospital_id: int

class StatusUpdate(BaseModel):
    ambulance_id: int
    status: str  # en_route, on_scene, transporting, at_hospital, available

@router.post("/create")
def create_assignment(req: AssignRequest, db: Session = Depends(get_db)):
    ambulance = db.query(Ambulance).filter(Ambulance.id == req.ambulance_id).first()
    incident = db.query(Incident).filter(Incident.id == req.incident_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == req.hospital_id).first()
    if not all([ambulance, incident, hospital]):
        return {"error": "Invalid ambulance, incident, or hospital ID"}

    ambulance.status = "dispatched"
    db.commit()

    active_assignments[req.ambulance_id] = {
        "ambulance_id": req.ambulance_id,
        "ambulance_name": ambulance.name,
        "phase": "dispatched",
        "incident": {
            "id": incident.id, "type": incident.type,
            "severity": incident.severity, "description": incident.description,
            "latitude": incident.latitude, "longitude": incident.longitude,
        },
        "hospital": {
            "id": hospital.id, "name": hospital.name,
            "trauma_level": hospital.trauma_level,
            "latitude": hospital.latitude, "longitude": hospital.longitude,
        },
    }
    return {"message": f"{ambulance.name} assigned", "assignment": active_assignments[req.ambulance_id]}

@router.get("/unit/{ambulance_id}")
def get_assignment(ambulance_id: int):
    return active_assignments.get(ambulance_id) or {"phase": "idle"}

@router.post("/status")
def update_status(update: StatusUpdate, db: Session = Depends(get_db)):
    assignment = active_assignments.get(update.ambulance_id)
    ambulance = db.query(Ambulance).filter(Ambulance.id == update.ambulance_id).first()
    if not ambulance:
        return {"error": "Ambulance not found"}

    if update.status == "available":
        ambulance.status = "available"
        db.commit()
        active_assignments.pop(update.ambulance_id, None)
        return {"message": "Unit returned to available", "phase": "idle"}

    if assignment:
        assignment["phase"] = update.status
    return {"message": f"Status: {update.status}", "assignment": assignment}