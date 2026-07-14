from core.database import engine, Base
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident
from sqlalchemy.orm import Session

# Create all tables
Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    # Clear existing data
    db.query(Incident).delete()
    db.query(Ambulance).delete()
    db.query(Hospital).delete()
    db.commit()

    # ─────────────────────────────────────────────
    # REAL NYC HOSPITALS — real coordinates, real trauma levels
    # ─────────────────────────────────────────────
    hospitals = [
        # Manhattan — Trauma Level 1
        Hospital(name="Bellevue Hospital Center", latitude=40.7390, longitude=-73.9757, total_beds=828, available_beds=180, trauma_level=1),
        Hospital(name="NYU Langone Medical Center", latitude=40.7421, longitude=-73.9739, total_beds=705, available_beds=150, trauma_level=1),
        Hospital(name="NewYork-Presbyterian/Weill Cornell", latitude=40.7655, longitude=-73.9542, total_beds=862, available_beds=200, trauma_level=1),
        Hospital(name="Mount Sinai Hospital", latitude=40.7900, longitude=-73.9526, total_beds=1134, available_beds=280, trauma_level=1),
        Hospital(name="NewYork-Presbyterian/Columbia", latitude=40.8404, longitude=-73.9421, total_beds=750, available_beds=160, trauma_level=1),
        Hospital(name="Harlem Hospital Center", latitude=40.8116, longitude=-73.9401, total_beds=286, available_beds=60, trauma_level=1),

        # Manhattan — Trauma Level 2
        Hospital(name="Lenox Hill Hospital", latitude=40.7712, longitude=-73.9571, total_beds=652, available_beds=140, trauma_level=2),
        Hospital(name="Metropolitan Hospital Center", latitude=40.7936, longitude=-73.9451, total_beds=341, available_beds=70, trauma_level=2),
        Hospital(name="St. Luke's Roosevelt Hospital", latitude=40.7686, longitude=-73.9862, total_beds=432, available_beds=90, trauma_level=2),

        # Bronx
        Hospital(name="Lincoln Medical Center", latitude=40.8165, longitude=-73.9253, total_beds=347, available_beds=75, trauma_level=1),
        Hospital(name="Jacobi Medical Center", latitude=40.8523, longitude=-73.8467, total_beds=457, available_beds=100, trauma_level=1),
        Hospital(name="Montefiore Medical Center", latitude=40.8817, longitude=-73.8789, total_beds=1491, available_beds=320, trauma_level=2),
        Hospital(name="BronxCare Health System", latitude=40.8418, longitude=-73.9124, total_beds=372, available_beds=80, trauma_level=2),

        # Brooklyn
        Hospital(name="Kings County Hospital", latitude=40.6559, longitude=-73.9442, total_beds=627, available_beds=130, trauma_level=1),
        Hospital(name="NewYork-Presbyterian Brooklyn Methodist", latitude=40.6612, longitude=-73.9697, total_beds=591, available_beds=120, trauma_level=2),
        Hospital(name="Maimonides Medical Center", latitude=40.6349, longitude=-74.0098, total_beds=711, available_beds=150, trauma_level=2),
        Hospital(name="Woodhull Medical Center", latitude=40.6987, longitude=-73.9401, total_beds=335, available_beds=70, trauma_level=2),
        Hospital(name="Coney Island Hospital", latitude=40.5763, longitude=-73.9816, total_beds=371, available_beds=80, trauma_level=3),

        # Queens
        Hospital(name="Elmhurst Hospital Center", latitude=40.7447, longitude=-73.8796, total_beds=545, available_beds=110, trauma_level=1),
        Hospital(name="Jamaica Hospital Medical Center", latitude=40.6956, longitude=-73.8021, total_beds=431, available_beds=90, trauma_level=2),
        Hospital(name="NewYork-Presbyterian Queens", latitude=40.7282, longitude=-73.8265, total_beds=535, available_beds=115, trauma_level=2),
        Hospital(name="Long Island Jewish Medical Center", latitude=40.7548, longitude=-73.7076, total_beds=583, available_beds=120, trauma_level=2),

        # Staten Island
        Hospital(name="Staten Island University Hospital", latitude=40.5986, longitude=-74.0831, total_beds=714, available_beds=150, trauma_level=2),
        Hospital(name="Richmond University Medical Center", latitude=40.6282, longitude=-74.1068, total_beds=440, available_beds=90, trauma_level=3),
    ]

    # ─────────────────────────────────────────────
    # REAL FDNY EMS STATIONS — ambulances positioned at real station locations
    # ─────────────────────────────────────────────
    ambulances = [
        # Manhattan
        Ambulance(name="EMS-M04A", status="available", latitude=40.7114, longitude=-73.9948, equipment="advanced"),   # Station 4 - Lower East Side
        Ambulance(name="EMS-M04B", status="available", latitude=40.7114, longitude=-73.9948, equipment="cardiac"),    # Station 4 - Lower East Side
        Ambulance(name="EMS-M07A", status="available", latitude=40.7484, longitude=-74.0000, equipment="advanced"),   # Station 7 - Chelsea
        Ambulance(name="EMS-M07B", status="dispatched", latitude=40.7484, longitude=-74.0000, equipment="basic"),     # Station 7 - Chelsea
        Ambulance(name="EMS-M08A", status="available", latitude=40.7390, longitude=-73.9757, equipment="cardiac"),    # Station 8 - Bellevue
        Ambulance(name="EMS-M08B", status="available", latitude=40.7390, longitude=-73.9757, equipment="advanced"),   # Station 8 - Bellevue
        Ambulance(name="EMS-M10A", status="available", latitude=40.7894, longitude=-73.9441, equipment="advanced"),   # Station 10 - Upper East Side
        Ambulance(name="EMS-M10B", status="available", latitude=40.7894, longitude=-73.9441, equipment="basic"),      # Station 10 - Upper East Side
        Ambulance(name="EMS-M13A", status="available", latitude=40.8433, longitude=-73.9390, equipment="advanced"),   # Station 13 - Washington Heights
        Ambulance(name="EMS-M13B", status="dispatched", latitude=40.8433, longitude=-73.9390, equipment="cardiac"),   # Station 13 - Washington Heights
        Ambulance(name="EMS-M16A", status="available", latitude=40.8117, longitude=-73.9398, equipment="advanced"),   # Station 16 - Harlem
        Ambulance(name="EMS-M16B", status="available", latitude=40.8117, longitude=-73.9398, equipment="basic"),      # Station 16 - Harlem

        # Bronx
        Ambulance(name="EMS-B03A", status="available", latitude=40.8352, longitude=-73.8448, equipment="advanced"),   # Station 3 - Soundview
        Ambulance(name="EMS-B03B", status="available", latitude=40.8352, longitude=-73.8448, equipment="basic"),      # Station 3 - Soundview
        Ambulance(name="EMS-B14A", status="available", latitude=40.8165, longitude=-73.9253, equipment="cardiac"),    # Station 14 - South Bronx
        Ambulance(name="EMS-B14B", status="dispatched", latitude=40.8165, longitude=-73.9253, equipment="advanced"),  # Station 14 - South Bronx
        Ambulance(name="EMS-B17A", status="available", latitude=40.8434, longitude=-73.9201, equipment="advanced"),   # Station 17 - Highbridge
        Ambulance(name="EMS-B20A", status="available", latitude=40.8523, longitude=-73.8467, equipment="cardiac"),    # Station 20 - Jacobi

        # Brooklyn
        Ambulance(name="EMS-K31A", status="available", latitude=40.6942, longitude=-73.9742, equipment="advanced"),   # Station 31 - Cumberland
        Ambulance(name="EMS-K31B", status="available", latitude=40.6942, longitude=-73.9742, equipment="basic"),      # Station 31 - Cumberland
        Ambulance(name="EMS-K35A", status="available", latitude=40.7081, longitude=-73.9571, equipment="advanced"),   # Station 35 - Williamsburg
        Ambulance(name="EMS-K38A", status="available", latitude=40.6559, longitude=-73.9442, equipment="cardiac"),    # Station 38 - Kings County
        Ambulance(name="EMS-K38B", status="dispatched", latitude=40.6559, longitude=-73.9442, equipment="advanced"),  # Station 38 - Kings County
        Ambulance(name="EMS-K44A", status="available", latitude=40.6612, longitude=-73.9197, equipment="basic"),      # Station 44 - Brownsville
        Ambulance(name="EMS-K57A", status="available", latitude=40.6987, longitude=-73.9401, equipment="advanced"),   # Station 57 - Bed Stuy
        Ambulance(name="EMS-K58A", status="available", latitude=40.6282, longitude=-73.9398, equipment="basic"),      # Station 58 - Canarsie

        # Queens
        Ambulance(name="EMS-Q45A", status="available", latitude=40.7447, longitude=-73.8796, equipment="cardiac"),    # Station 45 - Elmhurst
        Ambulance(name="EMS-Q45B", status="available", latitude=40.7447, longitude=-73.8796, equipment="advanced"),   # Station 45 - Elmhurst
        Ambulance(name="EMS-Q46A", status="available", latitude=40.7282, longitude=-73.8265, equipment="advanced"),   # Station 46 - Queens
        Ambulance(name="EMS-Q49A", status="dispatched", latitude=40.6956, longitude=-73.8021, equipment="basic"),     # Station 49 - Jamaica
        Ambulance(name="EMS-Q52A", status="available", latitude=40.7548, longitude=-73.7076, equipment="advanced"),   # Station 52 - LIJ

        # Staten Island
        Ambulance(name="EMS-S22A", status="available", latitude=40.5986, longitude=-74.0831, equipment="advanced"),   # Station 22 - Willowbrook
        Ambulance(name="EMS-S23A", status="available", latitude=40.6282, longitude=-74.1068, equipment="basic"),      # Station 23 - Rossville
    ]

    # Sample active incidents across NYC
    incidents = [
        Incident(type="cardiac", severity="critical", latitude=40.7489, longitude=-73.9680, description="Cardiac arrest - Midtown Manhattan", status="active"),
        Incident(type="accident", severity="high", latitude=40.6559, longitude=-73.9442, description="Multi-vehicle accident - Flatbush Avenue Brooklyn", status="active"),
        Incident(type="trauma", severity="high", latitude=40.8165, longitude=-73.9253, description="Stabbing - South Bronx", status="active"),
        Incident(type="fire", severity="medium", latitude=40.7282, longitude=-73.8265, description="Building fire - Queens", status="active"),
    ]

    db.add_all(hospitals)
    db.add_all(ambulances)
    db.add_all(incidents)
    db.commit()
    print(f"✅ NYC seed complete: {len(hospitals)} hospitals, {len(ambulances)} ambulances, {len(incidents)} incidents")