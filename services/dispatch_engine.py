import math
from sqlalchemy.orm import Session
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident


# ─────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in km between two GPS points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 3)


# ─────────────────────────────────────────────
# HARD CONSTRAINTS
# These eliminate candidates before scoring.
# A candidate that fails a hard constraint is
# never recommended, regardless of score.
# ─────────────────────────────────────────────

EQUIPMENT_HIERARCHY = {
    "basic":    1,
    "advanced": 2,
    "cardiac":  3,
}

SEVERITY_EQUIPMENT_REQUIREMENT = {
    "low":      1,  # basic is fine
    "medium":   1,  # basic is fine
    "high":     2,  # need advanced or better
    "critical": 3,  # must have cardiac
}

SEVERITY_TRAUMA_REQUIREMENT = {
    "low":      3,  # any hospital
    "medium":   3,  # any hospital
    "high":     2,  # trauma level 2 or better
    "critical": 1,  # must be trauma level 1
}

def ambulance_meets_requirements(ambulance: Ambulance, incident: Incident) -> tuple[bool, str]:
    """
    Returns (True, "") if ambulance can handle this incident.
    Returns (False, reason) if it cannot.
    """
    equipment_level = EQUIPMENT_HIERARCHY.get(ambulance.equipment, 1)
    required_level = SEVERITY_EQUIPMENT_REQUIREMENT.get(incident.severity, 1)

    if equipment_level < required_level:
        return False, f"{ambulance.name} has {ambulance.equipment} equipment — insufficient for {incident.severity} incident"

    return True, ""


def hospital_meets_requirements(hospital: Hospital, incident: Incident) -> tuple[bool, str]:
    """
    Returns (True, "") if hospital can receive this patient.
    Returns (False, reason) if it cannot.
    """
    if hospital.available_beds <= 0:
        return False, f"{hospital.name} has no available beds"

    required_trauma = SEVERITY_TRAUMA_REQUIREMENT.get(incident.severity, 3)
    if hospital.trauma_level > required_trauma:
        return False, f"{hospital.name} is Trauma Level {hospital.trauma_level} — insufficient for {incident.severity} incident"

    # Safety buffer: don't send to hospital over 95% capacity
    load = 1 - (hospital.available_beds / hospital.total_beds)
    if load > 0.95:
        return False, f"{hospital.name} is at {round(load*100)}% capacity — too full"

    return True, ""


# ─────────────────────────────────────────────
# SOFT SCORING
# Only runs on candidates that passed hard constraints.
# Lower score = better recommendation.
# ─────────────────────────────────────────────

def compute_score(
    ambulance: Ambulance,
    hospital: Hospital,
    incident: Incident,
    dist_amb_to_incident: float,
    dist_incident_to_hospital: float,
) -> float:
    """
    Weighted score — lower is better.

    Weights reflect real EMS priorities:
    - Getting ambulance to scene fast is most important (0.40)
    - Getting patient to hospital fast matters a lot (0.35)
    - Hospital load affects patient care quality (0.15)
    - Equipment match bonus rewards better-equipped units (0.10)
    """
    # Hospital load: 0.0 = empty, 1.0 = full
    hospital_load = 1 - (hospital.available_beds / hospital.total_beds)

    # Equipment bonus: reward over-qualified ambulances slightly
    equipment_level = EQUIPMENT_HIERARCHY.get(ambulance.equipment, 1)
    required_level = SEVERITY_EQUIPMENT_REQUIREMENT.get(incident.severity, 1)
    equipment_bonus = max(0, equipment_level - required_level) * 0.5  # small bonus, not penalty

    score = (
        dist_amb_to_incident   * 0.40 +
        dist_incident_to_hospital * 0.35 +
        hospital_load          * 0.15 -
        equipment_bonus        * 0.10   # subtract: better equipment = lower score = preferred
    )
    return round(score, 4)


# ─────────────────────────────────────────────
# MAIN RECOMMENDATION ENGINE
# ─────────────────────────────────────────────

def get_recommendation(incident_id: int, db: Session) -> dict:
    # 1. Fetch incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": f"Incident {incident_id} not found"}

    # 2. Fetch all active ambulances and open hospitals
    all_ambulances = db.query(Ambulance).filter(
        Ambulance.status == "available",
        Ambulance.is_active == True
    ).all()

    all_hospitals = db.query(Hospital).all()

    # 3. Apply hard constraints — filter to eligible candidates only
    eligible_ambulances = []
    rejected_ambulances = []
    for amb in all_ambulances:
        ok, reason = ambulance_meets_requirements(amb, incident)
        if ok:
            eligible_ambulances.append(amb)
        else:
            rejected_ambulances.append(reason)

    eligible_hospitals = []
    rejected_hospitals = []
    for hosp in all_hospitals:
        ok, reason = hospital_meets_requirements(hosp, incident)
        if ok:
            eligible_hospitals.append(hosp)
        else:
            rejected_hospitals.append(reason)

    # 4. Handle no eligible candidates
    if not eligible_ambulances:
        # Fallback: relax equipment constraint for critical situations
        if incident.severity == "critical":
            eligible_ambulances = all_ambulances  # send whatever we have
            rejected_ambulances.append("WARNING: No fully-equipped ambulances available. Dispatching best available.")
        else:
            return {
                "error": "No eligible ambulances",
                "rejected_reasons": rejected_ambulances
            }

    if not eligible_hospitals:
        return {
            "error": "No eligible hospitals",
            "rejected_reasons": rejected_hospitals
        }

    # 5. Score all eligible combinations
    best_score = float("inf")
    best_ambulance = None
    best_hospital = None

    for ambulance in eligible_ambulances:
        dist_amb = haversine(
            ambulance.latitude, ambulance.longitude,
            incident.latitude, incident.longitude
        )
        for hospital in eligible_hospitals:
            dist_hosp = haversine(
                incident.latitude, incident.longitude,
                hospital.latitude, hospital.longitude
            )
            score = compute_score(ambulance, hospital, incident, dist_amb, dist_hosp)
            if score < best_score:
                best_score = score
                best_ambulance = ambulance
                best_hospital = hospital

    # 6. Compute final distances for response
    final_dist_amb = haversine(
        best_ambulance.latitude, best_ambulance.longitude,
        incident.latitude, incident.longitude
    )
    final_dist_hosp = haversine(
        incident.latitude, incident.longitude,
        best_hospital.latitude, best_hospital.longitude
    )

    # 7. Confidence: based on how much better best score is vs worst
    # Normalize to 0-100 range
    all_scores = []
    for ambulance in eligible_ambulances:
        dist_amb = haversine(
            ambulance.latitude, ambulance.longitude,
            incident.latitude, incident.longitude
        )
        for hospital in eligible_hospitals:
            dist_hosp = haversine(
                incident.latitude, incident.longitude,
                hospital.latitude, hospital.longitude
            )
            all_scores.append(compute_score(ambulance, hospital, incident, dist_amb, dist_hosp))

    if len(all_scores) > 1:
        worst = max(all_scores)
        score_range = worst - best_score
        confidence = round(min(99, 60 + (score_range / worst) * 39), 1) if worst > 0 else 75.0
    else:
        confidence = 75.0  # only one option

    # 8. Build human-readable explanation
    explanation_parts = [
        f"Dispatching {best_ambulance.name} ({best_ambulance.equipment} equipment) — {final_dist_amb}km from incident.",
        f"Destination: {best_hospital.name} (Trauma Level {best_hospital.trauma_level}, {best_hospital.available_beds} beds available, {final_dist_hosp}km away).",
    ]
    if rejected_ambulances:
        explanation_parts.append(f"Excluded ambulances: {'; '.join(rejected_ambulances)}.")
    if rejected_hospitals:
        explanation_parts.append(f"Excluded hospitals: {'; '.join(rejected_hospitals)}.")

    return {
        "incident_id": incident_id,
        "incident": {
            "type": incident.type,
            "severity": incident.severity,
        },
        "ambulance": {
            "id": best_ambulance.id,
            "name": best_ambulance.name,
            "equipment": best_ambulance.equipment,
            "distance_km": final_dist_amb,
        },
        "hospital": {
            "id": best_hospital.id,
            "name": best_hospital.name,
            "trauma_level": best_hospital.trauma_level,
            "available_beds": best_hospital.available_beds,
            "distance_km": final_dist_hosp,
        },
        "score": best_score,
        "confidence": confidence,
        "explanation": " ".join(explanation_parts),
        "candidates_evaluated": len(eligible_ambulances) * len(eligible_hospitals),
        "rejected_ambulances": rejected_ambulances,
        "rejected_hospitals": rejected_hospitals,
    }