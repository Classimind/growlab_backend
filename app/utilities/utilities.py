# import numpy as np 
# from PIL import Image
# import io
# from typing import Any


# def preprocess_image(image_bytes: bytes,input_shape:Any):
#     """
#     Supports dynamic and fixed input shapes
#     """
#     img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#     # Resize only if model input is fixed
#     if isinstance(input_shape[2], int) and isinstance(input_shape[3], int):
#         h = input_shape[2]
#         w = input_shape[3]
#         img = img.resize((w, h))

#     img = np.array(img).astype(np.float32)  / 255.0

#     # Normalize (ImageNet)
#     mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
#     std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
#     img = (img - mean) / std

#     # HWC → CHW
#     img = np.transpose(img, (2, 0, 1))

#     # Add batch dimension
#     img = np.expand_dims(img, axis=0)

#     return img



# def softmax(x, axis=None):
#     """
#     Safe softmax for 1D or 2D arrays
#     """
#     x = np.array(x)
    
#     # If x is 1D, use axis=0
#     if x.ndim == 1 and (axis is None):
#         axis = 0
#     elif axis is None:
#         axis = 1
    
#     x = x - np.max(x, axis=axis, keepdims=True)
#     e = np.exp(x)
#     return e / np.sum(e, axis=axis, keepdims=True)


import numpy as np 
from PIL import Image
import io
from typing import Any, Union, Tuple
import io
from PIL import Image
import torch
from torchvision import transforms
import os
from livekit import api
from app.core.config import settings

def preprocess_image(image_bytes: bytes, normalize: bool = False,
                     mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)) -> torch.Tensor:
    """
    Preprocess image bytes to match training transform:
    Resize(shorter side=255) → CenterCrop(224) → ToTensor → Optional Normalize
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    transform_list = [
        transforms.Resize(255, antialias=True),
        transforms.CenterCrop(224),
        transforms.ToTensor()
    ]

    if normalize:
        transform_list.append(transforms.Normalize(mean=mean, std=std))

    preprocess = transforms.Compose(transform_list)

    img_tensor = preprocess(img)

    # Add batch dimension: (C,H,W) -> (1,C,H,W)
    img_tensor = img_tensor.unsqueeze(0)
    
    return img_tensor




# def preprocess_image(
#     image_bytes: bytes, 
#     input_shape: Tuple[int, int, int, int],
#     normalize: bool = True,
#     mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
#     std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
# ) -> np.ndarray:
#     """
#     Preprocess image bytes for ONNX model inference.
#     Supports both dynamic and fixed input shapes.
    
#     Args:
#         image_bytes: Raw image bytes
#         input_shape: Model input shape (batch, channels, height, width)
#         normalize: Whether to apply ImageNet normalization
#         mean: Mean values for normalization (RGB order)
#         std: Standard deviation values for normalization (RGB order)
    
#     Returns:
#         Preprocessed image as numpy array ready for ONNX inference
#     """
#     # Load image and convert to RGB
#     img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#     # Resize only if model input is fixed (not dynamic)
#     if isinstance(input_shape[2], int) and isinstance(input_shape[3], int):
#         h = input_shape[2]
#         w = input_shape[3]
#         img = img.resize((w, h), Image.BILINEAR)

#     # Convert to numpy array and normalize to [0, 1]
#     img = np.array(img, dtype=np.float32) / 255.0

#     # Apply normalization (ImageNet default)
#     if normalize:
#         mean_array = np.array(mean, dtype=np.float32)
#         std_array = np.array(std, dtype=np.float32)
#         img = (img - mean_array) / std_array

#     # Convert from HWC (Height, Width, Channels) to CHW (Channels, Height, Width)
#     img = np.transpose(img, (2, 0, 1))

#     # Add batch dimension: (C, H, W) → (1, C, H, W)
#     img = np.expand_dims(img, axis=0)

#     return img


def softmax(x: np.ndarray, axis: Union[int, None] = None) -> np.ndarray:
    """
    Compute softmax values for array x.
    Safe implementation that prevents overflow.
    
    Args:
        x: Input array (1D or 2D)
        axis: Axis along which to compute softmax
              If None, will default to 0 for 1D arrays and 1 for 2D arrays
    
    Returns:
        Softmax probabilities with the same shape as input
    """
    x = np.array(x, dtype=np.float32)
    
    # Auto-detect axis if not specified
    if axis is None:
        if x.ndim == 1:
            axis = 0
        else:
            axis = 1
    
    # Subtract max for numerical stability (prevents overflow)
    x_max = np.max(x, axis=axis, keepdims=True)
    x_shifted = x - x_max
    
    # Compute exponentials
    exp_x = np.exp(x_shifted)
    
    # Normalize to get probabilities
    sum_exp = np.sum(exp_x, axis=axis, keepdims=True)
    
    return exp_x / sum_exp


def postprocess_output(
    logits: np.ndarray,
    class_names: Union[list, None] = None,
    top_k: int = 1
) -> dict:
    """
    Postprocess model output logits to get predictions.
    
    Args:
        logits: Raw model output (shape: [1, num_classes] or [num_classes])
        class_names: Optional list of class names
        top_k: Number of top predictions to return
    
    Returns:
        Dictionary with prediction results
    """
    # Flatten if needed
    if logits.ndim == 2:
        logits = logits[0]
    
    # Compute probabilities
    probabilities = softmax(logits)
    
    # Get top-k predictions
    top_indices = np.argsort(probabilities)[-top_k:][::-1]
    
    results = {
        'predicted_class': int(top_indices[0]),
        'confidence': float(probabilities[top_indices[0]]),
        'all_probabilities': probabilities.tolist(),
        'top_predictions': []
    }
    
    for idx in top_indices:
        pred = {
            'class_index': int(idx),
            'probability': float(probabilities[idx])
        }
        if class_names:
            pred['class_name'] = class_names[idx]
        results['top_predictions'].append(pred)
    
    return results





def generate_token(room_name: str,name="user",full_name="Unknown user"):
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(name)
        .with_name(full_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    return token
