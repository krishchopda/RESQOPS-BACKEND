from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/seed")
def seed_database(db: Session = Depends(get_db)):
    # Only seed if empty
    if db.query(Ambulance).count() > 0:
        return {"message": "Database already seeded"}

    hospitals = [
        Hospital(name="Bellevue Hospital Center", latitude=40.7390, longitude=-73.9757, total_beds=828, available_beds=180, trauma_level=1),
        Hospital(name="NYU Langone Medical Center", latitude=40.7421, longitude=-73.9739, total_beds=705, available_beds=150, trauma_level=1),
        Hospital(name="NewYork-Presbyterian/Weill Cornell", latitude=40.7655, longitude=-73.9542, total_beds=862, available_beds=200, trauma_level=1),
        Hospital(name="Mount Sinai Hospital", latitude=40.7900, longitude=-73.9526, total_beds=1134, available_beds=280, trauma_level=1),
        Hospital(name="Lenox Hill Hospital", latitude=40.7712, longitude=-73.9571, total_beds=652, available_beds=140, trauma_level=2),
        Hospital(name="Kings County Hospital", latitude=40.6559, longitude=-73.9442, total_beds=627, available_beds=130, trauma_level=1),
        Hospital(name="Elmhurst Hospital Center", latitude=40.7447, longitude=-73.8796, total_beds=545, available_beds=110, trauma_level=1),
        Hospital(name="Lincoln Medical Center", latitude=40.8165, longitude=-73.9253, total_beds=347, available_beds=75, trauma_level=1),
        Hospital(name="Jacobi Medical Center", latitude=40.8523, longitude=-73.8467, total_beds=457, available_beds=100, trauma_level=1),
        Hospital(name="Staten Island University Hospital", latitude=40.5986, longitude=-74.0831, total_beds=714, available_beds=150, trauma_level=2),
    ]

    ambulances = [
        Ambulance(name="EMS-M04A", status="available", latitude=40.7114, longitude=-73.9948, equipment="advanced"),
        Ambulance(name="EMS-M08A", status="available", latitude=40.7390, longitude=-73.9757, equipment="cardiac"),
        Ambulance(name="EMS-M08B", status="available", latitude=40.7390, longitude=-73.9757, equipment="advanced"),
        Ambulance(name="EMS-M10A", status="available", latitude=40.7894, longitude=-73.9441, equipment="advanced"),
        Ambulance(name="EMS-M13A", status="available", latitude=40.8433, longitude=-73.9390, equipment="advanced"),
        Ambulance(name="EMS-M16A", status="available", latitude=40.8117, longitude=-73.9398, equipment="cardiac"),
        Ambulance(name="EMS-B14A", status="available", latitude=40.8165, longitude=-73.9253, equipment="cardiac"),
        Ambulance(name="EMS-B20A", status="available", latitude=40.8523, longitude=-73.8467, equipment="advanced"),
        Ambulance(name="EMS-K31A", status="available", latitude=40.6942, longitude=-73.9742, equipment="advanced"),
        Ambulance(name="EMS-K38A", status="available", latitude=40.6559, longitude=-73.9442, equipment="cardiac"),
        Ambulance(name="EMS-Q45A", status="available", latitude=40.7447, longitude=-73.8796, equipment="cardiac"),
        Ambulance(name="EMS-Q46A", status="available", latitude=40.7282, longitude=-73.8265, equipment="advanced"),
        Ambulance(name="EMS-S22A", status="available", latitude=40.5986, longitude=-74.0831, equipment="advanced"),
    ]

    incidents = [
        Incident(type="cardiac", severity="critical", latitude=40.7489, longitude=-73.9680, description="Cardiac arrest - Midtown Manhattan", status="active"),
        Incident(type="accident", severity="high", latitude=40.6559, longitude=-73.9442, description="Multi-vehicle accident - Flatbush Avenue Brooklyn", status="active"),
        Incident(type="trauma", severity="high", latitude=40.8165, longitude=-73.9253, description="Stabbing - South Bronx", status="active"),
    ]

    db.add_all(hospitals)
    db.add_all(ambulances)
    db.add_all(incidents)
    db.commit()

    return {
        "message": "Database seeded successfully",
        "hospitals": len(hospitals),
        "ambulances": len(ambulances),
        "incidents": len(incidents)
    }