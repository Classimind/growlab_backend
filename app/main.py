# main.py
from fastapi import FastAPI,Query,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.api.v1 import user
from app.db.clients import connect_db,close_db
from app.services.cache import connect_redis,close_redis
from app.api.v1 import plant_database,app_ws,sensors,register_sensors,actuator,api_key
from app.services.mqtt_service import mqtt_service
import asyncio
from app.services.user_service import UserService
from app.services.actuator_status_service import ActuatorStatusService
from app.services.sensor_service import CollectSensorValueService
from app.api.v1.disease_prediction import prediction
from app.api.v1 import photo_upload
from app.api.v1.disease_prediction import prediction_pth
from app.api.v1.farm import farm_router
from app.utilities.utilities import generate_token
import logging
import os 
loop = asyncio.get_running_loop()


from fastapi.staticfiles import StaticFiles

UPLOAD_FOLDER = "uploaded_photos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




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

app.mount("/images", StaticFiles(directory=UPLOAD_FOLDER), name="images")

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
app.include_router(app_ws.router,prefix="/ws",tags=['websocket'])
app.include_router(user.router,prefix="/users",tags=['users','register','login'])
app.include_router(farm_router,prefix='/labs',tags=['farm','lab'])
app.include_router(sensors.router,prefix="/sensors-history",tags=['sensors-history','data'])
app.include_router(register_sensors.router)
app.include_router(api_key.router)
app.include_router(actuator.router)
# app.include_router(prediction.app,prefix='/prediction',tags=['disease','predictions'])
app.include_router(prediction_pth.app,prefix='/torch')
app.include_router(photo_upload.app,prefix='/upload')
# Root endpoint

@app.get("/")
async def root():
    try:
        # Initialize your service classes
        sensor_service = CollectSensorValueService()
        actuator_service = ActuatorStatusService()

        # Fetch latest data
        latest_sensors = await sensor_service.get_recent_sensors_data()
        # print(latest_sensors)
        latest_actuators = await actuator_service.get_recent_actuators_data()
        # print(latest_sensors)
        return {
            "latest_sensors": latest_sensors,
            "latest_actuators": latest_actuators
        }

    except HTTPException as e:
        # Pass through HTTP errors
        raise e
    except Exception as e:
        print(e)
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Error fetching device data: {str(e)}")



@app.get("/token/")
def get_token(
    room_name: str = Query(..., description="Room to join"),
    name: str = Query("user", description="Identity name"),
    full_name: str = Query("Unknown user", description="Full display name"),
):
    jwt_token = generate_token(room_name, name, full_name)
    return {"token": jwt_token}




