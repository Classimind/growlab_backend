# app/routers/dashboard.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from datetime import datetime
from typing import Optional
from app.db.clients import get_db
from app.services.analytics_cache import refresh_lab_analytics
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Response models (optional but good for documentation)
class DataPoint(BaseModel):
    time: datetime
    value: float
    quality: str

class SensorAnalyticsResponse(BaseModel):
    sensor_id: str
    type: str
    unit: str
    name: str
    latest: DataPoint
    stats: Dict[str, Any]
    trend: Dict[str, Any]
    data_quality: float
    status: str
    time_series: List[DataPoint]
    anomalies: List[Dict[str, Any]]

class DashboardResponse(BaseModel):
    overall_health: float
    sensors: List[SensorAnalyticsResponse]
    alerts: List[Dict[str, Any]]


@router.get("/{lab_id}", response_model=DashboardResponse)
async def get_dashboard_data(
    lab_id: str,
    window_hours: int = Query(24, ge=1, le=720, description="Time window in hours (1 to 720)"),
    bucket_minutes: int = Query(5, ge=1, le=60, description="Resampling interval in minutes")
):
    """
    Get precomputed sensor analytics for a lab dashboard.
    Data is served from the analytics_cache collection (refreshed every 5 minutes in background).
    If cache is missing, it triggers an on-demand refresh and waits for result.
    """
    db = get_db()
    cache_key = f"{window_hours}h"
    
    # Try to fetch from cache
    cache_doc = await db["analytics_cache"].find_one({
        "lab_id": lab_id,
        "time_window": cache_key
    })
    
    # If cache missing or outdated (optional: check computed_at), refresh on-demand
    if not cache_doc:
        print(f"Cache miss for lab {lab_id}, window {cache_key}. Triggering on-demand refresh...")
        # Trigger refresh (this may take a few seconds)
        await refresh_lab_analytics(lab_id, window_hours=window_hours, bucket_minutes=bucket_minutes)
        # Fetch again
        cache_doc = await db["analytics_cache"].find_one({
            "lab_id": lab_id,
            "time_window": cache_key
        })
        if not cache_doc:
            raise HTTPException(status_code=404, detail="No data available for this lab and time window")
    
    # Return only the 'data' part (excluding metadata like computed_at)
    return cache_doc["data"]
