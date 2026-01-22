"""
Diagnose and Fix Biased PyTorch Model
This script will help identify why your model is biased to one class
"""

import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
import sys
from pathlib import Path


def create_model_with_softmax(num_classes=4):
    """Original model WITH softmax"""
    model = models.resnet18(weights=None)
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, 100),
        nn.ReLU(),
        nn.Linear(100, num_classes),
        nn.Softmax(dim=1)
    )
    return model


def create_model_without_softmax(num_classes=4):
    """Model WITHOUT softmax (for proper inference)"""
    model = models.resnet18(weights=None)
    model.fc = nn.Sequential(
        nn.Linear(model.fc.in_features, 100),
        nn.ReLU(),
        nn.Linear(100, num_classes)
    )
    return model


def diagnose_model(pth_path):
    """Comprehensive model diagnosis"""
    
    print("=" * 70)
    print("MODEL DIAGNOSIS - Finding Why Model is Biased")
    print("=" * 70)
    
    # Load checkpoint
    print(f"\n📥 Loading: {pth_path}")
    checkpoint = torch.load(pth_path, map_location='cpu')
    
    if isinstance(checkpoint, dict):
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
    else:
        state_dict = checkpoint
    
    # Load model WITH softmax (as it was trained)
    print("\n🔍 Testing with SOFTMAX (training architecture)...")
    model_softmax = create_model_with_softmax(num_classes=4)
    model_softmax.load_state_dict(state_dict)
    model_softmax.eval()
    
    # Load model WITHOUT softmax (for proper inference)
    print("🔍 Testing WITHOUT softmax (inference architecture)...")
    model_no_softmax = create_model_without_softmax(num_classes=4)
    
    # Copy weights manually
    model_no_softmax.fc[0].weight.data = model_softmax.fc[0].weight.data.clone()
    model_no_softmax.fc[0].bias.data = model_softmax.fc[0].bias.data.clone()
    model_no_softmax.fc[2].weight.data = model_softmax.fc[2].weight.data.clone()
    model_no_softmax.fc[2].bias.data = model_softmax.fc[2].bias.data.clone()
    
    for name, param in model_softmax.named_parameters():
        if not name.startswith('fc'):
            model_no_softmax.state_dict()[name].copy_(param.data)
    
    model_no_softmax.eval()
    
    # Test with diverse inputs
    print("\n" + "=" * 70)
    print("TEST 1: Model WITH Softmax (Current Architecture)")
    print("=" * 70)
    
    test_cases = {
        "All zeros": torch.zeros(1, 3, 224, 224),
        "All ones": torch.ones(1, 3, 224, 224),
        "Random (std=1)": torch.randn(1, 3, 224, 224),
        "Random (std=5)": torch.randn(1, 3, 224, 224) * 5,
        "Bright image": torch.ones(1, 3, 224, 224) * 0.8,
        "Dark image": torch.ones(1, 3, 224, 224) * 0.2,
    }
    
    predictions_with_softmax = []
    with torch.no_grad():
        for name, test_input in test_cases.items():
            output = model_softmax(test_input).numpy()[0]
            pred_class = np.argmax(output)
            predictions_with_softmax.append(pred_class)
            print(f"{name:20s} → Class {pred_class} | Probs: {output}")
    
    # Check diversity
    unique_softmax = len(set(predictions_with_softmax))
    print(f"\nUnique predictions: {unique_softmax}/6 test cases")
    
    if unique_softmax == 1:
        print("❌ PROBLEM: Model with softmax always predicts same class!")
        print("   This happens when using softmax during inference.")
    
    print("\n" + "=" * 70)
    print("TEST 2: Model WITHOUT Softmax (Correct Architecture)")
    print("=" * 70)
    
    predictions_no_softmax = []
    with torch.no_grad():
        for name, test_input in test_cases.items():
            logits = model_no_softmax(test_input).numpy()[0]
            
            # Apply softmax manually
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            
            pred_class = np.argmax(probs)
            predictions_no_softmax.append(pred_class)
            print(f"{name:20s} → Class {pred_class} | Logits: {logits}")
            print(f"{'':20s}             Probs:  {probs}")
    
    # Check diversity
    unique_no_softmax = len(set(predictions_no_softmax))
    print(f"\nUnique predictions: {unique_no_softmax}/6 test cases")
    
    if unique_no_softmax > 1:
        print("✅ GOOD: Model without softmax shows variation!")
    
    # Analyze final layer
    print("\n" + "=" * 70)
    print("FINAL LAYER ANALYSIS")
    print("=" * 70)
    
    fc_weight = model_no_softmax.fc[2].weight.data.numpy()
    fc_bias = model_no_softmax.fc[2].bias.data.numpy()
    
    print(f"\nWeight statistics:")
    print(f"  Mean: {fc_weight.mean():.6f}")
    print(f"  Std:  {fc_weight.std():.6f}")
    print(f"  Min:  {fc_weight.min():.6f}")
    print(f"  Max:  {fc_weight.max():.6f}")
    
    print(f"\nBias values:")
    for i, bias in enumerate(fc_bias):
        print(f"  Class {i}: {bias:.6f}")
    
    bias_range = fc_bias.max() - fc_bias.min()
    print(f"\nBias range: {bias_range:.6f}")
    
    if bias_range > 2.0:
        max_bias_class = np.argmax(fc_bias)
        print(f"⚠️  WARNING: Large bias toward Class {max_bias_class}")
        print(f"   This causes the model to prefer this class.")
    
    # DIAGNOSIS
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    
    if unique_softmax == 1 and unique_no_softmax > 1:
        print("\n✅ FOUND THE PROBLEM!")
        print("\nYour model architecture includes Softmax, which causes issues:")
        print("  1. During training with CrossEntropyLoss (which has built-in softmax),")
        print("     this creates 'double softmax' problem")
        print("  2. The model learned incorrectly due to this architecture issue")
        print("  3. During inference, softmax makes predictions extreme (close to 0 or 1)")
        
        print("\n🔧 SOLUTION:")
        print("  Option 1 (Recommended): Retrain the model WITHOUT softmax")
        print("    - Remove Softmax(dim=1) from your model architecture")
        print("    - Use CrossEntropyLoss (it applies softmax internally)")
        print("    - This will fix the learning process")
        
        print("\n  Option 2 (Temporary): Use model without softmax for inference")
        print("    - Convert to ONNX without the softmax layer")
        print("    - Apply softmax manually during inference")
        print("    - This may help but model is still poorly trained")
        
    elif unique_softmax == 1 and unique_no_softmax == 1:
        print("\n❌ SEVERE PROBLEM: Model did not learn properly!")
        print("\nPossible causes:")
        print("  1. Training data extremely imbalanced")
        print("  2. Learning rate too high/low")
        print("  3. Training stopped too early")
        print("  4. Loss function configuration issue")
        
        print("\n🔧 SOLUTION: Retrain the model")
        print("  - Check class distribution in training data")
        print("  - Use class weights in loss function")
        print("  - Train for more epochs")
        print("  - Monitor validation accuracy")
    else:
        print("\n✅ Model shows some learning ability")
        print("   Convert to ONNX without softmax and test with real images")
    
    print("=" * 70)
    
    return unique_no_softmax > 1


def export_fixed_onnx(pth_path, onnx_path):
    """Export ONNX without softmax"""
    print("\n" + "=" * 70)
    print("EXPORTING FIXED ONNX (Without Softmax)")
    print("=" * 70)
    
    # Load model
    checkpoint = torch.load(pth_path, map_location='cpu')
    
    if isinstance(checkpoint, dict):
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        elif 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
    else:
        state_dict = checkpoint
    
    # Load with softmax first
    model_softmax = create_model_with_softmax(num_classes=4)
    model_softmax.load_state_dict(state_dict)
    
    # Create without softmax
    model = create_model_without_softmax(num_classes=4)
    
    # Copy weights
    model.fc[0].weight.data = model_softmax.fc[0].weight.data.clone()
    model.fc[0].bias.data = model_softmax.fc[0].bias.data.clone()
    model.fc[2].weight.data = model_softmax.fc[2].weight.data.clone()
    model.fc[2].bias.data = model_softmax.fc[2].bias.data.clone()
    
    for name, param in model_softmax.named_parameters():
        if not name.startswith('fc'):
            model.state_dict()[name].copy_(param.data)
    
    model.eval()
    
    # Export
    dummy_input = torch.randn(1, 3, 224, 224)
    
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=['image'],
        output_names=['predictions'],
        dynamic_axes={
            'image': {0: 'batch_size'},
            'predictions': {0: 'batch_size'}
        }
    )
    
    print(f"✅ Exported to: {onnx_path}")
    print("   Note: This outputs logits. Apply softmax during inference.")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {sys.argv[0]} <model.pth> [output.onnx]")
        print("\nExample:")
        print(f"  python {sys.argv[0]} lettuce_npk.pth lettuce_npk_fixed.onnx")
        sys.exit(1)
    
    pth_path = sys.argv[1]
    onnx_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Diagnose
    model_ok = diagnose_model(pth_path)
    
    # Export if requested and model shows learning
    if onnx_path and model_ok:
        export_fixed_onnx(pth_path, onnx_path)
    elif onnx_path and not model_ok:
        print("\n⚠️  Model needs retraining. ONNX export skipped.")


if __name__ == "__main__":
    main()