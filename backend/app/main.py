from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.glucose import router as glucose_router
from app.routers.fasting import router as fasting_router
from app.routers.habits import router as habits_router
from app.routers.alarms import router as alarms_router
from app.routers.meals import router as meals_router
from app.routers.notifications import router as notifications_router
from app.routers.ai import router as ai_router
from app.routers.meal_plan import router as meal_plan_router
from app.routers.fhir import router as fhir_router
from app.routers.medications import router as medications_router

app = FastAPI(
    title="Azúcar Control API",
    description="Backend API para la gestión privada de diabetes tipo 2 y estilo de vida",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None
)

# CORS configuration
ALLOWED_ORIGINS = [
    "https://azucar.aeisoftware.com",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include all endpoint routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(glucose_router, prefix="/api/v1/glucose", tags=["Glucosa"])
app.include_router(fasting_router, prefix="/api/v1/fasting", tags=["Ayuno"])
app.include_router(habits_router, prefix="/api/v1/habits", tags=["Hábitos"])
app.include_router(alarms_router, prefix="/api/v1/alarms", tags=["Alarmas"])
app.include_router(meals_router, prefix="/api/v1/meals", tags=["Comidas"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notificaciones"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["Asistente IA"])
app.include_router(meal_plan_router, prefix="/api/v1/meal-plan", tags=["Planificador IA"])
app.include_router(fhir_router, prefix="/api/v1/fhir", tags=["FHIR/HL7"])
app.include_router(medications_router, prefix="/api/v1/medications", tags=["Medicamentos"])

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Service health verification endpoint."""
    return {
        "status": "healthy",
        "service": "Azucar Control API"
    }
