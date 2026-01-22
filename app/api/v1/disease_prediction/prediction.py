from fastapi import APIRouter, UploadFile, File
from PIL import Image
import numpy as np
import onnxruntime as ort
import io
import time
from app.utilities.utilities import softmax, preprocess_image
from pathlib import Path

# -----------------------------------
# Configuration
# -----------------------------------
TOP_K = 5

# -----------------------------------
# Paths
# -----------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parents[2] / "model"


MODEL_FILES = {
    "lettuce_healthy_stressed": MODEL_DIR / "lettuce_healthystressed.onnx",
    "lettuce_npk": MODEL_DIR / "lettuce_npk.onnx"
}

# -----------------------------------
# Load ONNX Models
# -----------------------------------
providers = [
    ('CUDAExecutionProvider', {
        'device_id': 0,
        'arena_extend_strategy': 'kNextPowerOfTwo',
        'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
    }),
    'CPUExecutionProvider',
]

sessions = {}
model_io = {}

for name, path in MODEL_FILES.items():
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    
    sess = ort.InferenceSession(str(path), providers=providers)
    sessions[name] = sess
    model_io[name] = {
        "input": sess.get_inputs()[0].name,
        "output": sess.get_outputs()[0].name,
        "input_shape": sess.get_inputs()[0].shape
    }
    print(f"[INFO] Loaded model '{name}'")
    print(f"       Input shape: {sess.get_inputs()[0].shape}")
    print(f"       Providers: {sess.get_providers()}")

# -----------------------------------
# Router
# -----------------------------------
app = APIRouter()

# -----------------------------------
# Health Check
# -----------------------------------
@app.get("/health")
def health():
    status_info = {}
    for name, sess in sessions.items():
        status_info[name] = {
            "device": "GPU" if "CUDAExecutionProvider" in sess.get_providers() else "CPU",
            "input_shape": model_io[name]["input_shape"]
        }
    return {"status": "ok", "models": status_info}

# -----------------------------------
# Prediction Endpoint
# -----------------------------------
@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_name: str = "lettuce_npk"  # default model
):
    if model_name not in sessions:
        return {"error": f"Model '{model_name}' not found. Available models: {list(sessions.keys())}"}

    start_time = time.time()

    # Read and preprocess image
    image_bytes = await file.read()
    input_tensor = preprocess_image(image_bytes,input_shape=model_io[name]['input_shape'])

    # Run inference
    sess = sessions[model_name]
    input_name = model_io[model_name]["input"]
    output_name = model_io[model_name]["output"]

    outputs = sess.run([output_name], {input_name: input_tensor})
    logits = outputs[0][0]
    probs = softmax(logits)

    # Top-K predictions
    top_indices = np.argsort(probs)[::-1][:TOP_K]
    predictions = [
        {"class_id": int(idx), "probability": float(probs[idx])}
        for idx in top_indices
    ]

    latency = round((time.time() - start_time) * 1000, 2)

    return {
        "filename": file.filename,
        "model_used": model_name,
        "predictions": predictions,
        "latency_ms": latency
    }
