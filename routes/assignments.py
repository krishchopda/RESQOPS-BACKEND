from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from core.database import get_db
from models.ambulance import Ambulance
from models.incident import Incident
from models.hospital import Hospital
from services.dispatch_engine import get_recommendation
from pydantic import BaseModel

router = APIRouter(prefix="/assignments", tags=["Assignments"])

# In-memory assignment store (v1 — will move to DB table later)
active_assignments = {}

ACCEPT_TIMEOUT_SECONDS = 60

class AssignRequest(BaseModel):
    ambulance_id: int
    incident_id: int
    hospital_id: int

class StatusUpdate(BaseModel):
    ambulance_id: int
    status: str  # en_route, on_scene, transporting, at_hospital, available


def _build_assignment(ambulance: Ambulance, incident: Incident, hospital: Hospital) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "ambulance_id": ambulance.id,
        "ambulance_name": ambulance.name,
        "phase": "dispatched",
        "created_at": now,
        "phase_updated_at": now,
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


@router.post("/create")
def create_assignment(req: AssignRequest, db: Session = Depends(get_db)):
    ambulance = db.query(Ambulance).filter(Ambulance.id == req.ambulance_id).first()
    incident = db.query(Incident).filter(Incident.id == req.incident_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == req.hospital_id).first()
    if not all([ambulance, incident, hospital]):
        return {"error": "Invalid ambulance, incident, or hospital ID"}

    ambulance.status = "dispatched"
    db.commit()

    active_assignments[req.ambulance_id] = _build_assignment(ambulance, incident, hospital)
    return {"message": f"{ambulance.name} assigned", "assignment": active_assignments[req.ambulance_id]}


@router.get("/unit/{ambulance_id}")
def get_assignment(ambulance_id: int):
    return active_assignments.get(ambulance_id) or {"phase": "idle"}


@router.get("/active")
def list_active_assignments():
    """All currently active assignments — used for timeout/reassignment checks
    and by the frontend's auto-suggest queue."""
    return list(active_assignments.values())


@router.post("/status")
def update_status(update: StatusUpdate, db: Session = Depends(get_db)):
    assignment = active_assignments.get(update.ambulance_id)
    ambulance = db.query(Ambulance).filter(Ambulance.id == update.ambulance_id).first()
    if not ambulance:
        return {"error": "Ambulance not found"}

    if update.status == "available":
        # Case complete: mark the incident resolved so it drops off the
        # active incidents list and the map, then free up the ambulance.
        if assignment:
            incident = db.query(Incident).filter(Incident.id == assignment["incident"]["id"]).first()
            if incident:
                incident.status = "resolved"
                db.commit()

        ambulance.status = "available"
        db.commit()
        active_assignments.pop(update.ambulance_id, None)
        return {"message": "Unit returned to available", "phase": "idle"}

    if assignment:
        assignment["phase"] = update.status
        assignment["phase_updated_at"] = datetime.now(timezone.utc).isoformat()

        # Move the ambulance's map marker to the hospital once it arrives.
        if update.status == "at_hospital":
            hospital = assignment.get("hospital")
            if hospital:
                ambulance.latitude = hospital["latitude"]
                ambulance.longitude = hospital["longitude"]
                db.commit()

    return {"message": f"Status: {update.status}", "assignment": assignment}


def check_and_reassign_timeouts(db: Session) -> list[dict]:
    """
    Scans active assignments for any unit still sitting in 'dispatched' phase
    (i.e. not yet accepted by the Responder) for longer than
    ACCEPT_TIMEOUT_SECONDS. Frees that unit and re-runs the dispatch engine,
    excluding it, to find the next-closest available ambulance for the same
    incident. Returns a list of reassignment events that occurred, so callers
    (like a background loop) can log or notify on them.
    """
    now = datetime.now(timezone.utc)
    events = []

    stale_ambulance_ids = []
    for ambulance_id, assignment in list(active_assignments.items()):
        if assignment["phase"] != "dispatched":
            continue
        created_at = datetime.fromisoformat(assignment["created_at"])
        elapsed = (now - created_at).total_seconds()
        if elapsed >= ACCEPT_TIMEOUT_SECONDS:
            stale_ambulance_ids.append(ambulance_id)

    for old_ambulance_id in stale_ambulance_ids:
        assignment = active_assignments.pop(old_ambulance_id, None)
        if not assignment:
            continue

        incident_id = assignment["incident"]["id"]

        # Free the unresponsive ambulance.
        old_ambulance = db.query(Ambulance).filter(Ambulance.id == old_ambulance_id).first()
        if old_ambulance:
            old_ambulance.status = "available"
            db.commit()

        # Confirm the incident is still active (not resolved/cancelled elsewhere).
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident or getattr(incident, "status", "active") != "active":
            events.append({
                "old_ambulance_id": old_ambulance_id,
                "incident_id": incident_id,
                "result": "skipped — incident no longer active"
            })
            continue

        recommendation = get_recommendation(incident_id, db, exclude_ambulance_ids=[old_ambulance_id])
        if recommendation.get("error"):
            events.append({
                "old_ambulance_id": old_ambulance_id,
                "incident_id": incident_id,
                "result": f"no replacement found — {recommendation['error']}"
            })
            continue

        new_ambulance = db.query(Ambulance).filter(Ambulance.id == recommendation["ambulance"]["id"]).first()
        new_hospital = db.query(Hospital).filter(Hospital.id == recommendation["hospital"]["id"]).first()
        if not new_ambulance or not new_hospital:
            events.append({
                "old_ambulance_id": old_ambulance_id,
                "incident_id": incident_id,
                "result": "error — recommended ambulance/hospital not found in DB"
            })
            continue

        new_ambulance.status = "dispatched"
        db.commit()
        active_assignments[new_ambulance.id] = _build_assignment(new_ambulance, incident, new_hospital)

        events.append({
            "old_ambulance_id": old_ambulance_id,
            "new_ambulance_id": new_ambulance.id,
            "new_ambulance_name": new_ambulance.name,
            "incident_id": incident_id,
            "result": "reassigned"
        })

    return events


@router.post("/check-timeouts")
def manual_check_timeouts(db: Session = Depends(get_db)):
    """Manually trigger a timeout sweep — useful for testing without waiting
    for the background loop, or for platforms without background task support."""
    events = check_and_reassign_timeouts(db)
    return {"checked": True, "events": events}