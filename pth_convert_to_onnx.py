import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
import numpy as np
from torchvision import models
from collections import OrderedDict

# -----------------------------------
# Configuration
# -----------------------------------
PTH_PATH = "lettuce_npk.pth"
ONNX_PATH = "lettuce_npk.onnx"
NUM_CLASSES = 4 
OPSET_VERSION = 17 # Modern opset for better compatibility

# Force CPU for export to avoid "device mismatch" errors
device = torch.device("cpu")

def load_model():
    # 1. Recreate architecture
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Sequential(
        torch.nn.Linear(model.fc.in_features, 100),
        torch.nn.ReLU(),
        torch.nn.Linear(100, NUM_CLASSES),
        torch.nn.Softmax(dim=1) 
    )

    # 2. Load weights
    print(f"Loading weights from {PTH_PATH}...")
    # map_location=device ensures weights land on CPU even if saved on GPU
    checkpoint = torch.load(PTH_PATH, map_location=device)
    
    # 3. Handle 'module.' prefix from DataParallel
    new_state_dict = OrderedDict()
    for k, v in checkpoint.items():
        name = k[7:] if k.startswith('module.') else k 
        new_state_dict[name] = v
    
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()
    return model

def export_to_onnx():
    model = load_model()
    
    # Create dummy input strictly on CPU
    dummy_input = torch.randn(1, 3, 224, 224).to(device)

    print("Starting ONNX export (Legacy mode for stability)...")
    
    # We use the standard export to avoid the 'Dynamo' errors you saw earlier
    torch.onnx.export(
        model,
        dummy_input,
        ONNX_PATH,
        export_params=True,
        opset_version=OPSET_VERSION,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        # dynamic_axes allows for different batch sizes during inference
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )
    print(f"✅ Success! ONNX model saved: {ONNX_PATH}")

def verify_onnx():
    print("\nVerifying ONNX model with ONNX Runtime...")
    session = ort.InferenceSession(ONNX_PATH)
    
    # Test with a zero-array to confirm it runs
    test_input = np.zeros((1, 3, 224, 224), dtype=np.float32)
    outputs = session.run(None, {"input": test_input})
    
    print(f"Exported Input Name: {session.get_inputs()[0].name}")
    print(f"Model Output Shape: {outputs[0].shape}")
    print(f"Model Output (Probabilities): {outputs[0]}")
    print("✅ Verification Complete.")

if __name__ == "__main__":
    try:
        export_to_onnx()
        verify_onnx()
    except Exception as e:
        print(f"❌ Export failed: {e}")