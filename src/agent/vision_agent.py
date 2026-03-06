"""
Vision Agent: Analyzes medical images and extracts visual features
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
import pydicom


class VisionAgent:
    """
    Agent responsible for processing medical images and extracting features.
    Supports multiple medical imaging modalities (X-ray, CT, MRI).
    """
    
    def __init__(
        self, 
        model_name: str = "resnet50",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        pretrained: bool = True
    ):
        """
        Initialize the Vision Agent.
        
        Args:
            model_name: Name of the vision model to use
            device: Device to run inference on (cuda/cpu)
            pretrained: Whether to use pretrained weights
        """
        self.device = device
        self.model_name = model_name
        self.model = self._load_model(model_name, pretrained)
        self.transform = self._get_transform()
        
    def _load_model(self, model_name: str, pretrained: bool) -> nn.Module:
        """Load the vision model."""
        if model_name == "resnet50":
            model = models.resnet50(pretrained=pretrained)
            # Remove the final classification layer to get features
            model = nn.Sequential(*list(model.children())[:-1])
        elif model_name == "densenet121":
            model = models.densenet121(pretrained=pretrained)
            model = nn.Sequential(*list(model.children())[:-1])
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        
        model = model.to(self.device)
        model.eval()
        return model
    
    def _get_transform(self) -> transforms.Compose:
        """Get image preprocessing transforms."""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def load_dicom(self, dicom_path: str) -> Tuple[np.ndarray, Dict]:
        """
        Load and parse DICOM file.
        
        Args:
            dicom_path: Path to DICOM file
            
        Returns:
            Tuple of (pixel_array, metadata)
        """
        dicom = pydicom.dcmread(dicom_path)
        pixel_array = dicom.pixel_array
        
        metadata = {
            'patient_id': getattr(dicom, 'PatientID', 'Unknown'),
            'study_date': getattr(dicom, 'StudyDate', 'Unknown'),
            'modality': getattr(dicom, 'Modality', 'Unknown'),
            'body_part': getattr(dicom, 'BodyPartExamined', 'Unknown'),
            'rows': dicom.Rows,
            'columns': dicom.Columns,
        }
        
        return pixel_array, metadata
    
    def preprocess_image(self, image: np.ndarray) -> Image.Image:
        """
        Preprocess medical image for analysis.
        
        Args:
            image: Raw image array
            
        Returns:
            Preprocessed PIL Image
        """
        # Normalize to 0-255 range
        image = ((image - image.min()) / (image.max() - image.min()) * 255).astype(np.uint8)
        
        # Convert to RGB if grayscale
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)
        
        return Image.fromarray(image)
    
    def extract_features(self, image: Image.Image) -> np.ndarray:
        """
        Extract deep learning features from image.
        
        Args:
            image: PIL Image
            
        Returns:
            Feature vector
        """
        # Transform and prepare image
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Extract features
        with torch.no_grad():
            features = self.model(img_tensor)
            features = features.squeeze().cpu().numpy()
        
        return features
    
    def detect_regions_of_interest(
        self, 
        image: Image.Image
    ) -> List[Dict[str, any]]:
        """
        Detect regions of interest in the medical image.
        
        Args:
            image: PIL Image
            
        Returns:
            List of detected regions with bounding boxes and confidence
        """
        # Placeholder for ROI detection
        # In production, use object detection models like Faster R-CNN
        # or medical-specific models
        rois = []
        
        # TODO: Implement actual ROI detection
        # This would involve:
        # 1. Object detection model
        # 2. Segmentation model (U-Net, etc.)
        # 3. Anatomical landmark detection
        
        return rois
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Complete image analysis pipeline.
        
        Args:
            image_path: Path to image file (DICOM or standard format)
            
        Returns:
            Dictionary with analysis results
        """
        # Load image
        if image_path.endswith('.dcm'):
            pixel_array, metadata = self.load_dicom(image_path)
            image = self.preprocess_image(pixel_array)
        else:
            image = Image.open(image_path)
            metadata = {'format': 'standard'}
        
        # Extract features
        features = self.extract_features(image)
        
        # Detect ROIs
        rois = self.detect_regions_of_interest(image)
        
        return {
            'metadata': metadata,
            'features': features,
            'feature_shape': features.shape,
            'regions_of_interest': rois,
            'image_size': image.size
        }
    
    def batch_analyze(self, image_paths: List[str]) -> List[Dict]:
        """
        Analyze multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of analysis results
        """
        results = []
        for path in image_paths:
            try:
                result = self.analyze_image(path)
                results.append(result)
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
                results.append({'error': str(e)})
        
        return results


# Example usage
if __name__ == "__main__":
    # Initialize vision agent
    agent = VisionAgent(model_name="resnet50")
    
    # Example: Analyze a single image
    # result = agent.analyze_image("path/to/xray.dcm")
    # print(f"Features extracted: {result['feature_shape']}")
    # print(f"Metadata: {result['metadata']}")
    
    print("Vision Agent initialized successfully!")
    print(f"Running on: {agent.device}")
