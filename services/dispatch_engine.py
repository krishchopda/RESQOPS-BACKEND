import math
import httpx
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


def get_travel_time(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Get real road travel time in minutes using OSRM.
    Falls back to Haversine estimate if OSRM is unavailable.
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
        params = {"overview": "false", "steps": "false"}
        response = httpx.get(url, params=params, timeout=3.0)
        data = response.json()
        if data.get("code") == "Ok":
            duration_seconds = data["routes"][0]["duration"]
            return round(duration_seconds / 60, 2)
    except Exception:
        pass
    # Fallback: estimate from distance assuming 40km/h average speed
    distance_km = haversine(lat1, lon1, lat2, lon2)
    return round((distance_km / 40) * 60, 2)


# ─────────────────────────────────────────────
# HARD CONSTRAINTS
# ─────────────────────────────────────────────

EQUIPMENT_HIERARCHY = {
    "basic":    1,
    "advanced": 2,
    "cardiac":  3,
}

SEVERITY_EQUIPMENT_REQUIREMENT = {
    "low":      1,
    "medium":   1,
    "high":     2,
    "critical": 3,
}

SEVERITY_TRAUMA_REQUIREMENT = {
    "low":      3,
    "medium":   3,
    "high":     2,
    "critical": 1,
}

def ambulance_meets_requirements(ambulance: Ambulance, incident: Incident) -> tuple[bool, str]:
    equipment_level = EQUIPMENT_HIERARCHY.get(ambulance.equipment, 1)
    required_level = SEVERITY_EQUIPMENT_REQUIREMENT.get(incident.severity, 1)
    if equipment_level < required_level:
        return False, f"{ambulance.name} has {ambulance.equipment} equipment — insufficient for {incident.severity} incident"
    return True, ""


def hospital_meets_requirements(hospital: Hospital, incident: Incident) -> tuple[bool, str]:
    if hospital.available_beds <= 0:
        return False, f"{hospital.name} has no available beds"
    required_trauma = SEVERITY_TRAUMA_REQUIREMENT.get(incident.severity, 3)
    if hospital.trauma_level > required_trauma:
        return False, f"{hospital.name} is Trauma Level {hospital.trauma_level} — insufficient for {incident.severity} incident"
    load = 1 - (hospital.available_beds / hospital.total_beds)
    if load > 0.95:
        return False, f"{hospital.name} is at {round(load*100)}% capacity — too full"
    return True, ""


# ─────────────────────────────────────────────
# SOFT SCORING
# ─────────────────────────────────────────────

def compute_score(
    ambulance: Ambulance,
    hospital: Hospital,
    incident: Incident,
    time_amb_to_incident: float,
    time_incident_to_hospital: float,
) -> float:
    """Lower score = better. Now uses travel time in minutes instead of distance."""
    hospital_load = 1 - (hospital.available_beds / hospital.total_beds)
    equipment_level = EQUIPMENT_HIERARCHY.get(ambulance.equipment, 1)
    required_level = SEVERITY_EQUIPMENT_REQUIREMENT.get(incident.severity, 1)
    equipment_bonus = max(0, equipment_level - required_level) * 0.5

    score = (
        time_amb_to_incident       * 0.40 +
        time_incident_to_hospital  * 0.35 +
        hospital_load              * 0.15 -
        equipment_bonus            * 0.10
    )
    return round(score, 4)


# ─────────────────────────────────────────────
# MAIN RECOMMENDATION ENGINE
# ─────────────────────────────────────────────

def get_recommendation(incident_id: int, db: Session) -> dict:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return {"error": f"Incident {incident_id} not found"}

    all_ambulances = db.query(Ambulance).filter(
        Ambulance.status == "available",
        Ambulance.is_active == True
    ).all()

    all_hospitals = db.query(Hospital).all()

    # Apply hard constraints
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

    if not eligible_ambulances:
        if incident.severity == "critical":
            eligible_ambulances = all_ambulances
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

    # Score all eligible combinations using real travel time
    best_score = float("inf")
    best_ambulance = None
    best_hospital = None

    for ambulance in eligible_ambulances:
        time_amb = get_travel_time(
            ambulance.latitude, ambulance.longitude,
            incident.latitude, incident.longitude
        )
        for hospital in eligible_hospitals:
            time_hosp = get_travel_time(
                incident.latitude, incident.longitude,
                hospital.latitude, hospital.longitude
            )
            score = compute_score(ambulance, hospital, incident, time_amb, time_hosp)
            if score < best_score:
                best_score = score
                best_ambulance = ambulance
                best_hospital = hospital

    # Final travel times for best combination
    final_time_amb = get_travel_time(
        best_ambulance.latitude, best_ambulance.longitude,
        incident.latitude, incident.longitude
    )
    final_time_hosp = get_travel_time(
        incident.latitude, incident.longitude,
        best_hospital.latitude, best_hospital.longitude
    )

    # Also get distances for display
    final_dist_amb = haversine(
        best_ambulance.latitude, best_ambulance.longitude,
        incident.latitude, incident.longitude
    )
    final_dist_hosp = haversine(
        incident.latitude, incident.longitude,
        best_hospital.latitude, best_hospital.longitude
    )

    # Confidence score
    all_scores = []
    for ambulance in eligible_ambulances:
        time_amb = get_travel_time(
            ambulance.latitude, ambulance.longitude,
            incident.latitude, incident.longitude
        )
        for hospital in eligible_hospitals:
            time_hosp = get_travel_time(
                incident.latitude, incident.longitude,
                hospital.latitude, hospital.longitude
            )
            all_scores.append(compute_score(ambulance, hospital, incident, time_amb, time_hosp))

    if len(all_scores) > 1:
        worst = max(all_scores)
        score_range = worst - best_score
        confidence = round(min(99, 60 + (score_range / worst) * 39), 1) if worst > 0 else 75.0
    else:
        confidence = 75.0

    # Human-readable explanation
    explanation_parts = [
        f"Dispatching {best_ambulance.name} ({best_ambulance.equipment} equipment) — "
        f"{final_time_amb} min travel time ({final_dist_amb}km) to incident.",
        f"Destination: {best_hospital.name} (Trauma Level {best_hospital.trauma_level}, "
        f"{best_hospital.available_beds} beds available, "
        f"{final_time_hosp} min travel time, {final_dist_hosp}km away).",
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
            "travel_time_min": final_time_amb,
        },
        "hospital": {
            "id": best_hospital.id,
            "name": best_hospital.name,
            "trauma_level": best_hospital.trauma_level,
            "available_beds": best_hospital.available_beds,
            "distance_km": final_dist_hosp,
            "travel_time_min": final_time_hosp,
        },
        "score": best_score,
        "confidence": confidence,
        "explanation": " ".join(explanation_parts),
        "candidates_evaluated": len(eligible_ambulances) * len(eligible_hospitals),
        "rejected_ambulances": rejected_ambulances,
        "rejected_hospitals": rejected_hospitals,
    }