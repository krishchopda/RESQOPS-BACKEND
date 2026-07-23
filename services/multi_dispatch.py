import math
from sqlalchemy.orm import Session
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident
from services.dispatch_engine import (
    haversine,
    get_travel_time,
    ambulance_meets_requirements,
    hospital_meets_requirements,
    compute_score,
    EQUIPMENT_HIERARCHY,
    SEVERITY_EQUIPMENT_REQUIREMENT,
    SEVERITY_TRAUMA_REQUIREMENT,
)


# ─────────────────────────────────────────────
# CASUALTY ESTIMATION
# How many ambulances does this incident need?
# ─────────────────────────────────────────────

CASUALTY_ESTIMATES = {
    # (incident_type, severity) -> (min_ambulances, max_ambulances)
    
    ("cardiac", "critical"):   (1, 1),  # single patient, 1 specialized unit
    ("cardiac", "high"):       (1, 1),
    ("accident", "critical"):  (3, 5),  # multiple casualties likely
    ("accident", "high"):      (2, 3),
    ("accident", "medium"):    (1, 2),
    ("fire", "critical"):      (4, 6),  # building fire, multiple casualties
    ("fire", "high"):          (2, 4),
    ("fire", "medium"):        (1, 2),
    ("trauma", "critical"):    (2, 3),
    ("trauma", "high"):        (1, 2),
    ("mass_casualty", "critical"): (6, 10),
}

def estimate_ambulances_needed(incident: Incident, override: int = None) -> tuple[int, str]:
    """Returns (count, reasoning)"""
    if override:
        return override, f"Dispatcher requested {override} ambulances."

    key = (incident.type.lower(), incident.severity.lower())
    min_amb, max_amb = CASUALTY_ESTIMATES.get(key, (1, 2))

    # Use midpoint rounded up
    count = math.ceil((min_amb + max_amb) / 2)

    reasoning = (
        f"{incident.type.title()} incident with {incident.severity} severity "
        f"typically requires {min_amb}–{max_amb} ambulances. "
        f"Deploying {count}."
    )
    return count, reasoning


# ─────────────────────────────────────────────
# HOSPITAL LOAD BALANCER
# Distributes patients across hospitals to
# avoid overloading any single facility
# ─────────────────────────────────────────────

class HospitalLoadBalancer:
    def __init__(self, hospitals: list[Hospital]):
        # Track remaining capacity dynamically as we assign patients
        self.capacity = {h.id: h.available_beds for h in hospitals}
        self.hospitals = {h.id: h for h in hospitals}
        self.assignments = {}  # hospital_id -> count assigned

    def assign_patient(self, hospital: Hospital) -> bool:
        """Try to assign one patient to this hospital. Returns True if successful."""
        if self.capacity.get(hospital.id, 0) > 0:
            self.capacity[hospital.id] -= 1
            self.assignments[hospital.id] = self.assignments.get(hospital.id, 0) + 1
            return True
        return False

    def get_current_load(self, hospital: Hospital) -> float:
        """Get current load percentage including pending assignments."""
        original = hospital.available_beds
        assigned = self.assignments.get(hospital.id, 0)
        remaining = original - assigned
        return 1 - (remaining / hospital.total_beds)

    def is_available(self, hospital: Hospital) -> bool:
        remaining = self.capacity.get(hospital.id, 0)
        load = self.get_current_load(hospital)
        return remaining > 0 and load < 0.95


# ─────────────────────────────────────────────
# MAIN MULTI-DISPATCH ENGINE
# ─────────────────────────────────────────────

def get_multi_recommendation(
    incident_id: int,
    db: Session,
    ambulances_override: int = None
) -> dict:
    # 1. Fetch incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": f"Incident {incident_id} not found"}

    # 2. Estimate ambulances needed
    ambulances_needed, casualty_reasoning = estimate_ambulances_needed(
        incident, ambulances_override
    )

    # 3. Get all available ambulances and hospitals
    all_ambulances = db.query(Ambulance).filter(
        Ambulance.status == "available",
        Ambulance.is_active == True
    ).all()

    all_hospitals = db.query(Hospital).all()

    # 4. Filter eligible ambulances
    eligible_ambulances = []
    rejected_ambulances = []
    for amb in all_ambulances:
        ok, reason = ambulance_meets_requirements(amb, incident)
        if ok:
            eligible_ambulances.append(amb)
        else:
            rejected_ambulances.append(reason)

    # For mass casualty — relax equipment constraints if not enough ambulances
    if len(eligible_ambulances) < ambulances_needed:
        shortage = ambulances_needed - len(eligible_ambulances)
        ineligible = [a for a in all_ambulances if a not in eligible_ambulances]
        eligible_ambulances.extend(ineligible[:shortage])
        if ineligible:
            rejected_ambulances.append(
                f"WARNING: {shortage} ambulance(s) dispatched with suboptimal equipment due to mass casualty."
            )

    # 5. Filter eligible hospitals
    eligible_hospitals = []
    rejected_hospitals = []
    for hosp in all_hospitals:
        ok, reason = hospital_meets_requirements(hosp, incident)
        if ok:
            eligible_hospitals.append(hosp)
        else:
            rejected_hospitals.append(reason)

    if not eligible_hospitals:
        return {"error": "No eligible hospitals", "rejected_reasons": rejected_hospitals}

    if not eligible_ambulances:
        return {"error": "No ambulances available", "rejected_reasons": rejected_ambulances}

    # 6. Rank ambulances by travel time to incident
    ambulances_with_time = []
    for amb in eligible_ambulances:
        travel_time = get_travel_time(
            amb.latitude, amb.longitude,
            incident.latitude, incident.longitude
        )
        dist = haversine(
            amb.latitude, amb.longitude,
            incident.latitude, incident.longitude
        )
        ambulances_with_time.append((amb, travel_time, dist))

    # Sort by travel time — fastest first
    ambulances_with_time.sort(key=lambda x: x[1])

    # Take the top N ambulances needed
    selected = ambulances_with_time[:ambulances_needed]

    # 7. Assign each ambulance to best available hospital using load balancer
    balancer = HospitalLoadBalancer(eligible_hospitals)
    deployments = []

    for amb, time_to_incident, dist_to_incident in selected:
        # Find best hospital for this ambulance considering current load
        best_hospital = None
        best_score = float("inf")
        best_time_to_hosp = None
        best_dist_to_hosp = None

        for hosp in eligible_hospitals:
            if not balancer.is_available(hosp):
                continue
            time_to_hosp = get_travel_time(
                incident.latitude, incident.longitude,
                hosp.latitude, hosp.longitude
            )
            dist_to_hosp = haversine(
                incident.latitude, incident.longitude,
                hosp.latitude, hosp.longitude
            )
            # Factor in current dynamic load
            temp_load = balancer.get_current_load(hosp)
            score = (
                time_to_incident * 0.40 +
                time_to_hosp * 0.35 +
                temp_load * 0.15
            )
            if score < best_score:
                best_score = score
                best_hospital = hosp
                best_time_to_hosp = time_to_hosp
                best_dist_to_hosp = dist_to_hosp

        if best_hospital is None:
            # All hospitals full — assign to least loaded
            best_hospital = min(eligible_hospitals, key=lambda h: balancer.get_current_load(h))
            best_time_to_hosp = get_travel_time(
                incident.latitude, incident.longitude,
                best_hospital.latitude, best_hospital.longitude
            )
            best_dist_to_hosp = haversine(
                incident.latitude, incident.longitude,
                best_hospital.latitude, best_hospital.longitude
            )

        balancer.assign_patient(best_hospital)

        deployments.append({
            "ambulance": {
                "id": amb.id,
                "name": amb.name,
                "equipment": amb.equipment,
                "travel_time_min": time_to_incident,
                "distance_km": dist_to_incident,
            },
            "hospital": {
                "id": best_hospital.id,
                "name": best_hospital.name,
                "trauma_level": best_hospital.trauma_level,
                "available_beds": best_hospital.available_beds,
                "travel_time_min": best_time_to_hosp,
                "distance_km": best_dist_to_hosp,
            }
        })

    # 8. Build summary
    hospitals_used = {}
    for d in deployments:
        hname = d["hospital"]["name"]
        hospitals_used[hname] = hospitals_used.get(hname, 0) + 1

    hospital_summary = ", ".join(
        f"{count} patient(s) → {name}" for name, count in hospitals_used.items()
    )

    explanation = (
        f"MASS CASUALTY DEPLOYMENT: {casualty_reasoning} "
        f"Dispatching {len(deployments)} ambulances. "
        f"Patient distribution: {hospital_summary}. "
        f"Load balanced across {len(hospitals_used)} hospital(s) to prevent overload."
    )

    return {
        "incident_id": incident_id,
        "incident": {
            "type": incident.type,
            "severity": incident.severity,
            "description": incident.description,
        },
        "ambulances_needed": ambulances_needed,
        "ambulances_dispatched": len(deployments),
        "deployments": deployments,
        "hospital_distribution": hospitals_used,
        "explanation": explanation,
        "warnings": rejected_ambulances,
        "rejected_hospitals": rejected_hospitals,
    }