# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.api.v1 import user
from app.db.clients import connect_db,close_db
from app.services.cache import connect_redis,close_redis
from app.api.v1 import plant_database,actuator_states,app_ws,sensors
from app.services.mqtt_service import mqtt_service
import asyncio
from app.services.user_service import UserService
import logging
loop = asyncio.get_running_loop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # logger for the debugging
    logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("aihydroponics.log"), 
        logging.StreamHandler()                   
    ]
)
    
    await connect_db()
    await connect_redis()
    print("Initalized the mongodb and redis ")
    await mqtt_service.start(loop)

    # Create the indexes
    user_services = UserService()
    await user_services.init_indexes()
    print("Created indexes")
    
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
app.include_router(user.router,prefix="/users",tags=['users','register','login'])
app.include_router(sensors.router,prefix="/sensors",tags=['sensors','data'])
# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hydroponics AI"}



