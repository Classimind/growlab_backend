# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from core.config import settings
from contextlib import asynccontextmanager
from db.clients import connect_db,close_db
from services.cache import connect_redis,close_redis
from api.v1 import plant_database,actuator_states,app_ws
from services.mqtt_service import mqtt_service
import asyncio



@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await connect_db()
    await connect_redis()
    print("Initalized the mongodb and redis ")
    await mqtt_service.start(loop)
    yield
    await close_db()
    await close_redis()
    mqtt_service.stop()
    print("Shutting down... Cleanup resources")

app = FastAPI(lifespan=lifespan,title="Hydroponics AI",description="Hydroponics AI",version="1.0.0")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (optional)
# app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Include Routers (API Versioning)
app.include_router(plant_database.router, prefix="/plants", tags=["plants"])
app.include_router(actuator_states.router,prefix="/actuator",tags=['actuators'])
app.include_router(app_ws.router,prefix="/ws",tags=['websocket'])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hydroponics AI"}



