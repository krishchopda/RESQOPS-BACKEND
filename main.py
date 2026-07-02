from fastapi import FastAPI
from routes.health import router as health_router
from routes.ambulances import router as ambulances_router
from routes.hospitals import router as hospitals_router
from routes.incidents import router as incidents_router

app = FastAPI(
    title="ResQOps API",
    description="AI Emergency Response Operating System",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(ambulances_router)
app.include_router(hospitals_router)
app.include_router(incidents_router)