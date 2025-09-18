# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from app.db.clients import connect_db,close_db
from app.services.cache import connect_redis,close_redis
from app.api.v1 import plant_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await connect_redis()
    print("Initalized the mongodb and redis ")
    yield
    await close_db()
    await close_redis()
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

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hydroponics AI"}



