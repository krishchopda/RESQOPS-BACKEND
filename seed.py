from core.database import engine, Base
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident
from sqlalchemy.orm import Session

# Create all tables
Base.metadata.create_all(bind=engine)

# Seed fake data
with Session(engine) as db:
    # Add ambulances
    ambulances = [
        Ambulance(name="AMB-01", status="available", latitude=40.7128, longitude=-74.0060, equipment="advanced"),
        Ambulance(name="AMB-02", status="available", latitude=40.7580, longitude=-73.9855, equipment="cardiac"),
        Ambulance(name="AMB-03", status="dispatched", latitude=40.7282, longitude=-73.7949, equipment="basic"),
        Ambulance(name="AMB-04", status="available", latitude=40.6892, longitude=-74.0445, equipment="advanced"),
        Ambulance(name="AMB-05", status="available", latitude=40.7489, longitude=-73.9680, equipment="basic"),
    ]

    hospitals = [
        Hospital(name="NYC General", latitude=40.7614, longitude=-73.9776, total_beds=200, available_beds=45, trauma_level=1),
        Hospital(name="Brooklyn Medical", latitude=40.6501, longitude=-73.9496, total_beds=150, available_beds=80, trauma_level=2),
        Hospital(name="Queens Hospital", latitude=40.7282, longitude=-73.7949, total_beds=120, available_beds=20, trauma_level=3),
    ]

    incidents = [
        Incident(type="accident", severity="high", latitude=40.7200, longitude=-74.0100, description="Multi-car accident on highway"),
        Incident(type="cardiac", severity="critical", latitude=40.7500, longitude=-73.9800, description="Cardiac arrest reported"),
        Incident(type="fire", severity="medium", latitude=40.7000, longitude=-73.9900, description="Building fire, 3rd floor"),
    ]

    db.add_all(ambulances)
    db.add_all(hospitals)
    db.add_all(incidents)
    db.commit()
    print("Tables created and seed data inserted successfully!")