from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.health import router as health_router
from routes.ambulances import router as ambulances_router
from routes.hospitals import router as hospitals_router
from routes.incidents import router as incidents_router
from routes.dispatch import router as dispatch_router
from routes.ai import router as ai_router
from routes.predictions import router as predictions_router
from core.database import engine, Base
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident
from routes.admin import router as admin_router
from routes.multi_dispatch import router as multi_dispatch_router
from routes.assignments import router as assignments_router


# Create tables on startup
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="ResQOps API",
    description="AI Emergency Response Operating System",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
     allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "https://resqops-frontend-lfwqglhuk-krishchopda-6940s-projects.vercel.app",
    "https://*.vercel.app"
],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ambulances_router)
app.include_router(hospitals_router)
app.include_router(incidents_router)
app.include_router(dispatch_router)
app.include_router(ai_router)
app.include_router(predictions_router)
app.include_router(admin_router)
app.include_router(multi_dispatch_router)
app.include_router(assignments_router)