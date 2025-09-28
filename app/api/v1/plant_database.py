from fastapi import APIRouter, HTTPException
from typing import List
from models.plant import Plant
from db.clients import mongodb
from services.cache import get_cache,set_cache
import json

router = APIRouter()

# -------------------------------
# GET all plants
# -------------------------------
@router.get("/", response_model=List[Plant])
async def get_plants():
    """
    Retrieve all plants from MongoDB or Redis cache.
    Returns a list of Plant objects.
    """
    cache_key = "all_plants"
    cached = await get_cache(cache_key)
    if cached:
        # Deserialize JSON to list of Plant objects
        plants_data = json.loads(cached)
        return  [Plant(**json.loads(p)) for p in plants_data]

    
    plants_cursor = mongodb.db["plants"].find({})
    plants: List[Plant] = []

    async for plant in plants_cursor:
        plants.append(Plant(**plant))
    await set_cache(cache_key, json.dumps([p.model_dump_json() for p in plants]), expire=300)

    return plants

# -------------------------------
# GET a single plant by name
# -------------------------------
@router.get("/{plant_name}", response_model=Plant)
async def get_plant(plant_name: str):
    """
    Retrieve a single plant by its name.
    Raises 404 if the plant does not exist.
    """
    cached = await get_cache(plant_name)
    if cached:
        # Deserialize JSON to list of Plant objects
        plant_data = json.loads(cached)
        return Plant(**plant_data)

    plant = await mongodb.db["plants"].find_one({"plant_name": plant_name})
    
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    # Convert ObjectId to string
    plant["_id"] = str(plant["_id"])
    await set_cache(plant_name, json.dumps(plant), expire=300)
    
    return Plant(**plant)

# -------------------------------
# POST a new plant
# -------------------------------
@router.post("/", response_model=Plant)
async def add_plant(plant: Plant):
    """
    Add a new plant to the MongoDB 'plants' collection.
    Raises 400 if the plant already exists.
    """
    existing = await mongodb.db["plants"].find_one({"plant_name": plant.plant_name})
    
    if existing:
        raise HTTPException(status_code=400, detail="Plant already exists")
    
    await mongodb.db["plants"].insert_one(plant.dict())
    return plant



@router.post("/all")
async def add_plants(plants: List[Plant]):
    """
    Add a list of plants to the MongoDB 'plants' collection.
    Checks if each plant already exists by name.
    Returns a summary of inserted and skipped plants.
    """
    inserted_plants = []
    skipped_plants = []

    for plant in plants:
        existing = await mongodb.db["plants"].find_one({"plant_name": plant.plant_name})
        if existing:
            skipped_plants.append(plant.plant_name)
        else:
            await mongodb.db["plants"].insert_one(plant.dict())
            inserted_plants.append(plant.plant_name)

    return {
        "inserted": inserted_plants,
        "skipped": skipped_plants,
        "total": len(plants)
    }