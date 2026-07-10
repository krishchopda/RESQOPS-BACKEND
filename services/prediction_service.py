from sqlalchemy.orm import Session
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident


def get_hospital_alerts(db: Session) -> list:
    """Flag hospitals approaching capacity."""
    hospitals = db.query(Hospital).all()
    alerts = []

    for h in hospitals:
        load = round((1 - h.available_beds / h.total_beds) * 100)

        if load >= 90:
            alerts.append({
                "type": "critical",
                "hospital": h.name,
                "message": f"{h.name} is at {load}% capacity — critically overloaded. Divert all non-critical patients.",
                "load_percent": load,
                "available_beds": h.available_beds
            })
        elif load >= 75:
            alerts.append({
                "type": "warning",
                "hospital": h.name,
                "message": f"{h.name} is at {load}% capacity — approaching limit. Monitor closely.",
                "load_percent": load,
                "available_beds": h.available_beds
            })

    return sorted(alerts, key=lambda x: x["load_percent"], reverse=True)


def get_ambulance_alerts(db: Session) -> list:
    """Flag if available ambulance count drops too low."""
    ambulances = db.query(Ambulance).filter(Ambulance.is_active == True).all()
    available = [a for a in ambulances if a.status == "available"]
    alerts = []

    if len(available) == 0:
        alerts.append({
            "type": "critical",
            "message": "NO ambulances available — immediate resource request needed.",
            "available_count": 0
        })
    elif len(available) <= 1:
        alerts.append({
            "type": "warning",
            "message": f"Only {len(available)} ambulance available — low resource warning.",
            "available_count": len(available)
        })

    return alerts


def get_incident_hotspots(db: Session) -> list:
    """
    Find geographic clusters of incidents.
    Simple rule: if 2+ incidents are within ~5km of each other, flag as hotspot.
    """
    from services.dispatch_engine import haversine

    incidents = db.query(Incident).filter(Incident.status == "active").all()
    hotspots = []
    flagged = set()

    for i, inc1 in enumerate(incidents):
        if inc1.id in flagged:
            continue
        cluster = [inc1]
        for j, inc2 in enumerate(incidents):
            if i == j or inc2.id in flagged:
                continue
            dist = haversine(inc1.latitude, inc1.longitude, inc2.latitude, inc2.longitude)
            if dist <= 5.0:
                cluster.append(inc2)

        if len(cluster) >= 2:
            for inc in cluster:
                flagged.add(inc.id)
            avg_lat = round(sum(i.latitude for i in cluster) / len(cluster), 4)
            avg_lon = round(sum(i.longitude for i in cluster) / len(cluster), 4)
            severities = [i.severity for i in cluster]
            has_critical = "critical" in severities or "high" in severities

            hotspots.append({
                "type": "critical" if has_critical else "warning",
                "incident_count": len(cluster),
                "incident_ids": [i.id for i in cluster],
                "center": {"lat": avg_lat, "lon": avg_lon},
                "message": f"{len(cluster)} incidents clustered within 5km — possible mass casualty or multi-vehicle event.",
                "severities": severities
            })

    return hotspots


def get_all_predictions(db: Session) -> dict:
    hospital_alerts = get_hospital_alerts(db)
    ambulance_alerts = get_ambulance_alerts(db)
    hotspots = get_incident_hotspots(db)

    total_alerts = len(hospital_alerts) + len(ambulance_alerts) + len(hotspots)
    critical_count = sum(1 for a in hospital_alerts + ambulance_alerts + hotspots if a["type"] == "critical")

    return {
        "summary": {
            "total_alerts": total_alerts,
            "critical": critical_count,
            "warnings": total_alerts - critical_count
        },
        "hospital_alerts": hospital_alerts,
        "ambulance_alerts": ambulance_alerts,
        "hotspots": hotspots
    }