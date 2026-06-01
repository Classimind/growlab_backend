# app/analytics_cache.py
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bson import ObjectId
from app.db.clients import get_db
from app.services.analytics import compute_historical_analytics  

# Default value that indicates a sensor error/disconnection
DEFAULT_ERROR_VALUE = -99


def prepare_metadata(meta_docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert raw metadata documents from 'sensor_metadata' collection
    to the format expected by compute_historical_analytics().

    Input document example:
    {
        "_id": ObjectId("69ee49fd1bddc049b32edebf"),
        "sensor_name": "pH Sensor",
        "lab_id": "69ec9766d347fe1781489e2e",
        "unit": "pH",
        "sensor_type": "analog",
        "range": [0, 14],          # may be null
        "created_by": "...",
        "created": "..."
    }

    Returns:
        dict: { sensor_id_str: { "type", "unit", "safe_min", "safe_max", "name", "error_value" } }
    """
    result = {}
    for doc in meta_docs:
        # Convert ObjectId to string for matching with sensor_id in readings
        sensor_id = str(doc["_id"])
        if not sensor_id:
            continue

        # Extract safe limits from 'range' field if present and not null
        safe_min = None
        safe_max = None
        range_field = doc.get("range")
        if range_field and isinstance(range_field, list) and len(range_field) == 2:
            safe_min = float(range_field[0])
            safe_max = float(range_field[1])

        result[sensor_id] = {
            "type": doc.get("sensor_type", "unknown"),
            "unit": doc.get("unit", ""),
            "safe_min": safe_min,
            "safe_max": safe_max,
            "name": doc.get("sensor_name", f"Sensor {sensor_id[:6]}"),
            "error_value": DEFAULT_ERROR_VALUE
        }
    return result


async def refresh_lab_analytics(
    lab_id: str,
    window_hours: int = 24,
    bucket_minutes: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Compute analytics for a specific lab over a rolling time window
    and store the result in the 'analytics_cache' collection.

    Args:
        lab_id: The lab identifier
        window_hours: Number of hours to look back (e.g., 24, 168)
        bucket_minutes: Resampling interval for time series (in minutes)

    Returns:
        The computed analytics dictionary (the 'data' part of cache document),
        or None if no data available.
    """
    db = get_db()
    to_time = datetime.now()
    from_time = to_time - timedelta(hours=window_hours)
   

    # 1. Fetch raw sensor readings within the time window
    readings_cursor = db["sensors_values"].find({
        "lab_id": lab_id,
        "created": {"$gte": from_time, "$lte": to_time}
    })
    readings = await readings_cursor.to_list(length=None)
    if not readings:
        print(f"No readings for lab {lab_id} in window {window_hours}h")
        return None

    # 2. Fetch metadata for all involved sensors
    #    sensor_id in readings is a string; we need to query _id as ObjectId
    sensor_ids = list({r["sensor_id"] for r in readings})
    object_ids = [ObjectId(sid) for sid in sensor_ids if ObjectId.is_valid(sid)]
    if not object_ids:
        print(f"No valid ObjectId found for sensors in lab {lab_id}")
        return None
    meta_cursor = db["sensors"].find({"_id": {"$in": object_ids}})
    meta_docs = await meta_cursor.to_list(length=None)
    metadata = prepare_metadata(meta_docs)
    # 3. Convert readings to pandas DataFrame
    df = pd.DataFrame(readings)
    df["created"] = pd.to_datetime(df["created"])
    df = df.sort_values(["sensor_id", "created"])
   
    # 4. Run advanced analytics
    #    Expects: compute_historical_analytics(df, metadata, bucket_minutes)
    sensor_analytics_list, alerts = compute_historical_analytics(
        df, metadata, bucket_minutes
    )


    # 5. Compute overall health as average data quality across sensors
    qualities = [s.get("data_quality", 0.0) for s in sensor_analytics_list]
    overall_health = sum(qualities) / len(qualities) if qualities else 0.0

    # 6. Build cache document
    cache_doc = {
        "lab_id": lab_id,
        "time_window": f"{window_hours}h",
        "bucket_minutes": bucket_minutes,
        "computed_at": datetime.now(),
        "from_time": from_time,
        "to_time": to_time,
        "data": {
            "overall_health": overall_health,
            "sensors": sensor_analytics_list,
            "alerts": alerts
        }
    }

    # 7. Upsert into analytics_cache collection
    await db["analytics_cache"].update_one(
        {"lab_id": lab_id, "time_window": f"{window_hours}h"},
        {"$set": cache_doc},
        upsert=True
    )
    print(f"Cached analytics for lab {lab_id}, window {window_hours}h at {datetime.now()}")
    return cache_doc["data"]


async def refresh_all_labs_analytics(windows_hours: List[int] = [24, 168]):
    """
    Refresh analytics for all labs and all specified time windows.
    Call this function from a background scheduler (e.g., every 5 minutes).
    """
    db = get_db()
    # Get all distinct lab IDs from the sensors_values collection
    lab_ids = await db["sensors_values"].distinct("lab_id")
    if not lab_ids:
        print("No labs found in sensors_values collection.")
        return

    for lab_id in lab_ids:
        for window in windows_hours:
            try:
                await refresh_lab_analytics(lab_id, window_hours=window)
            except Exception as e:
                print(f"Error refreshing lab {lab_id} window {window}h: {e}")

