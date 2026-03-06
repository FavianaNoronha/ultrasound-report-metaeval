"""
Utility functions for medical image preprocessing
"""

import numpy as np
from PIL import Image
import pydicom
from typing import Tuple, Optional


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image to 0-255 range.
    
    Args:
        image: Input image array
        
    Returns:
        Normalized image
    """
    img_min = image.min()
    img_max = image.max()
    
    if img_max == img_min:
        return np.zeros_like(image)
    
    normalized = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    return normalized


def apply_windowing(
    image: np.ndarray,
    window_center: int,
    window_width: int
) -> np.ndarray:
    """
    Apply window/level adjustment for medical images.
    
    Args:
        image: Input image
        window_center: Center of the window
        window_width: Width of the window
        
    Returns:
        Windowed image
    """
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    
    windowed = np.clip(image, img_min, img_max)
    windowed = normalize_image(windowed)
    
    return windowed


def convert_to_rgb(image: np.ndarray) -> np.ndarray:
    """
    Convert grayscale image to RGB.
    
    Args:
        image: Grayscale image
        
    Returns:
        RGB image
    """
    if len(image.shape) == 2:
        return np.stack([image] * 3, axis=-1)
    return image


def resize_image(
    image: np.ndarray,
    target_size: Tuple[int, int] = (512, 512)
) -> np.ndarray:
    """
    Resize image to target size.
    
    Args:
        image: Input image
        target_size: Target (height, width)
        
    Returns:
        Resized image
    """
    pil_image = Image.fromarray(image)
    resized = pil_image.resize(target_size[::-1], Image.BILINEAR)
    return np.array(resized)


def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """
    Enhance image contrast using CLAHE.
    
    Args:
        image: Input image
        clip_limit: Contrast limit
        
    Returns:
        Enhanced image
    """
    try:
        import cv2
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        return clahe.apply(image)
    except ImportError:
        # Fallback: simple histogram equalization
        return normalize_image(image)


def preprocess_dicom(
    dicom_path: str,
    target_size: Tuple[int, int] = (512, 512)
) -> Tuple[np.ndarray, dict]:
    """
    Complete preprocessing pipeline for DICOM images.
    
    Args:
        dicom_path: Path to DICOM file
        target_size: Target size for resizing
        
    Returns:
        Tuple of (processed_image, metadata)
    """
    # Read DICOM
    dicom = pydicom.dcmread(dicom_path)
    image = dicom.pixel_array
    
    # Extract metadata
    metadata = {
        'patient_id': getattr(dicom, 'PatientID', 'Unknown'),
        'study_date': getattr(dicom, 'StudyDate', 'Unknown'),
        'modality': getattr(dicom, 'Modality', 'Unknown'),
        'body_part': getattr(dicom, 'BodyPartExamined', 'Unknown'),
    }
    
    # Apply windowing if available
    if hasattr(dicom, 'WindowCenter') and hasattr(dicom, 'WindowWidth'):
        window_center = dicom.WindowCenter
        window_width = dicom.WindowWidth
        
        if isinstance(window_center, (list, pydicom.multival.MultiValue)):
            window_center = window_center[0]
        if isinstance(window_width, (list, pydicom.multival.MultiValue)):
            window_width = window_width[0]
        
        image = apply_windowing(image, int(window_center), int(window_width))
    else:
        image = normalize_image(image)
    
    # Enhance contrast
    image = enhance_contrast(image)
    
    # Resize
    image = resize_image(image, target_size)
    
    # Convert to RGB
    image = convert_to_rgb(image)
    
    return image, metadata
