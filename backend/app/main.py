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

app = FastAPI(
    title="Azúcar Control API",
    description="Backend API para la gestión privada de diabetes tipo 2 y estilo de vida",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to match your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Service health verification endpoint."""
    return {
        "status": "healthy",
        "service": "Azucar Control API"
    }
