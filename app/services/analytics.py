import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple


def compute_historical_analytics(
    df: pd.DataFrame,
    metadata: dict,
    bucket_minutes: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    sensor_analytics_list = []
    alerts_list = []

    # Ensure datetime (IMPORTANT FIX)
    df = df.copy()
    df["created"] = pd.to_datetime(df["created"], errors="coerce")
    df = df.dropna(subset=["created"])

    # Clean bucket value
    bucket_minutes = int(bucket_minutes)
    freq = f"{bucket_minutes}min"   # FIX: replaces deprecated "T"

    # Process each sensor individually
    for sensor_id, group in df.groupby("sensor_id"):
        if sensor_id not in metadata:
            continue

        meta = metadata[sensor_id]
        error_val = meta.get("error_value", -99)
        safe_min = meta.get("safe_min")
        safe_max = meta.get("safe_max")

        # Sort by time
        group = group.sort_values("created").copy()

        # Quality marking
        group["quality"] = np.where(group["value"] == error_val, "error", "good")

        # Time index
        group_indexed = group.set_index("created").sort_index()

  
        resampled = (
            group_indexed
            .resample(freq)
            .agg({
                "value": "mean",
                "quality": lambda x: (
                    "good" if (x == "good").sum() > len(x) / 2 else "error"
                )
            })
            .dropna()
        )

        # Interpolation
        resampled["value_interp"] = resampled["value"]
        resampled.loc[resampled["quality"] == "error", "value_interp"] = np.nan
        resampled["value_interp"] = resampled["value_interp"].interpolate(
            method="linear",
            limit_direction="both"
        )

        # Time series
        time_series = [
            {
                "time": idx.to_pydatetime(),
                "value": row["value_interp"] if not pd.isna(row["value_interp"]) else row["value"],
                "quality": row["quality"]
            }
            for idx, row in resampled.iterrows()
        ]

        # Stats (good only)
        good_vals = group[group["quality"] == "good"]["value"]

        stats = {
            "min": float(good_vals.min()) if len(good_vals) else None,
            "max": float(good_vals.max()) if len(good_vals) else None,
            "avg": float(good_vals.mean()) if len(good_vals) else None,
            "std": float(good_vals.std()) if len(good_vals) else None,
            "count_good": int(len(good_vals)),
            "count_error": int(len(group) - len(good_vals))
        }

        data_quality = stats["count_good"] / len(group) if len(group) else 0.0

        # Trend
        if len(resampled) >= 3:
            x = np.arange(len(resampled))
            y = resampled["value_interp"].values

            mask = ~np.isnan(y)
            x_clean = x[mask]
            y_clean = y[mask]

            if len(y_clean) >= 3:
                slope = np.polyfit(x_clean, y_clean, 1)[0]
                direction = (
                    "rising" if slope > 0.02
                    else "falling" if slope < -0.02
                    else "stable"
                )
            else:
                slope, direction = 0.0, "insufficient_data"
        else:
            slope, direction = 0.0, "insufficient_data"

        # Anomalies
        anomalies = []
        if len(good_vals) >= 5:
            q1, q3 = np.percentile(good_vals, [25, 75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            anomaly_points = group[
                (group["value"] < lower) | (group["value"] > upper)
            ]

            for _, row in anomaly_points.iterrows():
                anomalies.append({
                    "time": row["created"],
                    "value": row["value"],
                    "reason": "outlier (IQR)"
                })

        # Latest
        latest = group.iloc[-1]

        latest_point = {
            "time": latest["created"],
            "value": latest["value"],
            "quality": latest["quality"]
        }

        # Status
        status = "normal"

        if latest["quality"] == "error":
            status = "disconnected"
        elif safe_min is not None and latest["value"] < safe_min:
            status = "warning_low"
        elif safe_max is not None and latest["value"] > safe_max:
            status = "warning_high"

        sensor_analytics_list.append({
            "sensor_id": sensor_id,
            "type": meta.get("type", "unknown"),
            "unit": meta.get("unit", ""),
            "name": meta.get("name", sensor_id),
            "latest": latest_point,
            "stats": stats,
            "trend": {"slope": slope, "direction": direction},
            "data_quality": data_quality,
            "status": status,
            "time_series": time_series,
            "anomalies": anomalies
        })

    # Cross-sensor alert (heat index)
    temp_sensor = next((s for s in sensor_analytics_list if s["type"] == "temperature"), None)
    hum_sensor = next((s for s in sensor_analytics_list if s["type"] == "humidity"), None)

    if temp_sensor and hum_sensor:
        t = temp_sensor["latest"]["value"]
        h = hum_sensor["latest"]["value"]

        heat_index = t + 0.1 * h

        if heat_index > 35:
            alerts_list.append({
                "type": "heat_index",
                "value": heat_index,
                "severity": "warning",
                "message": f"Heat index {heat_index:.1f}°C exceeds threshold"
            })

    return sensor_analytics_list, alerts_list