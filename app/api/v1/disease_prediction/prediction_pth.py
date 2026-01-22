from fastapi import APIRouter, UploadFile, File
import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
import time
from pathlib import Path
from app.utilities.utilities import preprocess_image

# -----------------------------------
# Configuration
# -----------------------------------
TOP_K = 5
NUM_CLASSES = 4  # desired number of classes in your API

# -----------------------------------
# Paths
# -----------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parents[2] / "model"

MODEL_FILES = {
    "lettuce_healthy_stressed": MODEL_DIR / "lettuce_healthystressed.pth",
    "lettuce_npk": MODEL_DIR / "lettuce_npk.pth"
}

# -----------------------------------
# Model Architecture Definition
# -----------------------------------
def create_model(num_classes=NUM_CLASSES):
    """
    Create ResNet18 model with Linear fc layer.
    fc layer output will be num_classes.
    """
    model = models.resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

# -----------------------------------
# Load PyTorch Models
# -----------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[INFO] Using device: {device}")

models_dict = {}
model_configs = {}

for name, path in MODEL_FILES.items():
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    # Create model
    model = create_model(num_classes=NUM_CLASSES)

    # Load checkpoint
    checkpoint = torch.load(str(path), map_location=device)

    # Extract state_dict from checkpoint if needed
    if isinstance(checkpoint, dict):
        if "model_state_dict" in checkpoint:
            checkpoint_dict = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            checkpoint_dict = checkpoint["state_dict"]
        else:
            checkpoint_dict = checkpoint
    else:
        checkpoint_dict = checkpoint

    # Handle fc size mismatch
    model_dict = model.state_dict()
    pretrained_dict = {}
    for k, v in checkpoint_dict.items():
        if k in model_dict and v.shape == model_dict[k].shape:
            pretrained_dict[k] = v
        elif k in model_dict:
            print(f"[WARN] Skipping '{k}' due to size mismatch: {v.shape} -> {model_dict[k].shape}")

    model_dict.update(pretrained_dict)
    model.load_state_dict(model_dict)

    model.eval()
    model.to(device)

    models_dict[name] = model
    model_configs[name] = {
        "input_shape": [1, 3, 224, 224],
        "num_classes": NUM_CLASSES
    }

    print(f"[INFO] Loaded model '{name}'")
    print(f"       Input shape: [1, 3, 224, 224]")
    print(f"       Device: {device}")
    print(f"       Classes: {NUM_CLASSES}")

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
    for name in models_dict.keys():
        status_info[name] = {
            "device": str(device),
            "input_shape": model_configs[name]["input_shape"],
            "num_classes": model_configs[name]["num_classes"],
            "framework": "PyTorch"
        }
    return {"status": "ok", "models": status_info}

# -----------------------------------
# Prediction Endpoint
# -----------------------------------
@app.post("/predict")
async def predict(file: UploadFile = File(...), model_name: str = "lettuce_npk"):
    if model_name not in models_dict:
        return {"error": f"Model '{model_name}' not found. Available models: {list(models_dict.keys())}"}

    start_time = time.time()
    try:
        # Preprocess image
        image_bytes = await file.read()
        input_tensor = preprocess_image(image_bytes).to(device)  # <- tensor already, no from_numpy

        # Inference
        model = models_dict[model_name]
        with torch.no_grad():
            outputs = model(input_tensor)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]

        # Top-K predictions
        top_indices = np.argsort(probs)[::-1][:TOP_K]
        predictions = [{"class_id": int(idx), "probability": float(probs[idx])} for idx in top_indices]

        latency = round((time.time() - start_time) * 1000, 2)
        print(predictions)

        return {
            "filename": file.filename,
            "model_used": model_name,
            "framework": "PyTorch",
            "device": str(device),
            "predictions": predictions,
            "latency_ms": latency
        }

    except Exception as e:
        return {"error": str(e), "filename": file.filename, "model_used": model_name}


# -----------------------------------
# Batch Prediction Endpoint
# -----------------------------------
@app.post("/predict_batch")
async def predict_batch(files: list[UploadFile] = File(...), model_name: str = "lettuce_npk"):
    if model_name not in models_dict:
        return {"error": f"Model '{model_name}' not found. Available models: {list(models_dict.keys())}"}

    start_time = time.time()
    results = []

    try:
        batch_tensors = []
        filenames = []
        for file in files:
            image_bytes = await file.read()
            tensor = preprocess_image(image_bytes).to(device)  # <- tensor directly
            batch_tensors.append(tensor)
            filenames.append(file.filename)

        batch = torch.cat(batch_tensors, dim=0)

        model = models_dict[model_name]
        with torch.no_grad():
            outputs = model(batch)
            probs_batch = torch.softmax(outputs, dim=1).cpu().numpy()

        for filename, probs in zip(filenames, probs_batch):
            top_indices = np.argsort(probs)[::-1][:TOP_K]
            predictions = [{"class_id": int(idx), "probability": float(probs[idx])} for idx in top_indices]
            results.append({"filename": filename, "predictions": predictions})

        latency = round((time.time() - start_time) * 1000, 2)

        return {
            "model_used": model_name,
            "framework": "PyTorch",
            "device": str(device),
            "total_images": len(files),
            "results": results,
            "total_latency_ms": latency,
            "avg_latency_ms": round(latency / len(files), 2)
        }

    except Exception as e:
        return {"error": str(e), "model_used": model_name, "files_count": len(files)}

# -----------------------------------
# Model Info Endpoint
# -----------------------------------
@app.get("/models/{model_name}/info")
def get_model_info(model_name: str):
    if model_name not in models_dict:
        return {"error": f"Model '{model_name}' not found. Available models: {list(models_dict.keys())}"}

    model = models_dict[model_name]
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    return {
        "model_name": model_name,
        "framework": "PyTorch",
        "architecture": "ResNet18 + Linear FC",
        "device": str(device),
        "input_shape": model_configs[model_name]["input_shape"],
        "num_classes": model_configs[model_name]["num_classes"],
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "model_size_mb": round(total_params * 4 / (1024*1024), 2)
    }
