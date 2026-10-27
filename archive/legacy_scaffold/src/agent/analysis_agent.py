"""
Analysis Agent: Interprets visual features and identifies pathologies
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Finding:
    """Represents a medical finding."""
    condition: str
    confidence: float
    severity: str  # 'normal', 'mild', 'moderate', 'severe'
    location: str
    description: str


class AnalysisAgent:
    """
    Agent responsible for analyzing extracted features and 
    identifying medical conditions.
    """
    
    def __init__(
        self,
        num_classes: int = 14,  # Common chest X-ray diseases
        confidence_threshold: float = 0.5,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize the Analysis Agent.
        
        Args:
            num_classes: Number of disease classes to detect
            confidence_threshold: Minimum confidence for reporting findings
            device: Device to run inference on
        """
        self.num_classes = num_classes
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Disease labels (example for chest X-ray)
        self.disease_labels = [
            'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
            'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
            'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
            'Pleural_Thickening', 'Hernia'
        ]
        
        self.classifier = self._build_classifier()
        
    def _build_classifier(self) -> nn.Module:
        """Build multi-label disease classifier."""
        # Simple MLP classifier for demonstration
        # In production, this would be a trained model
        classifier = nn.Sequential(
            nn.Linear(2048, 1024),  # Assuming ResNet50 features
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, self.num_classes),
            nn.Sigmoid()  # Multi-label classification
        )
        return classifier.to(self.device)
    
    def load_trained_model(self, model_path: str):
        """Load a trained classifier model."""
        self.classifier.load_state_dict(torch.load(model_path, map_location=self.device))
        self.classifier.eval()
    
    def classify_diseases(self, features: np.ndarray) -> Dict[str, float]:
        """
        Classify diseases based on image features.
        
        Args:
            features: Feature vector from Vision Agent
            
        Returns:
            Dictionary mapping disease names to confidence scores
        """
        # Convert features to tensor
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        # Get predictions
        with torch.no_grad():
            predictions = self.classifier(features_tensor)
            predictions = predictions.squeeze().cpu().numpy()
        
        # Map to disease labels
        disease_probs = {
            label: float(prob) 
            for label, prob in zip(self.disease_labels, predictions)
        }
        
        return disease_probs
    
    def assess_severity(self, disease: str, confidence: float) -> str:
        """
        Assess severity of a finding.
        
        Args:
            disease: Name of the disease
            confidence: Confidence score
            
        Returns:
            Severity level
        """
        # Simple heuristic - in production, use specialized models
        if confidence < 0.3:
            return 'normal'
        elif confidence < 0.5:
            return 'mild'
        elif confidence < 0.7:
            return 'moderate'
        else:
            return 'severe'
    
    def extract_findings(
        self, 
        disease_probs: Dict[str, float],
        metadata: Dict = None
    ) -> List[Finding]:
        """
        Extract significant findings from disease probabilities.
        
        Args:
            disease_probs: Disease probability scores
            metadata: Additional context (optional)
            
        Returns:
            List of significant findings
        """
        findings = []
        
        for disease, confidence in disease_probs.items():
            if confidence >= self.confidence_threshold:
                severity = self.assess_severity(disease, confidence)
                
                finding = Finding(
                    condition=disease,
                    confidence=confidence,
                    severity=severity,
                    location=self._infer_location(disease, metadata),
                    description=self._generate_description(disease, confidence, severity)
                )
                findings.append(finding)
        
        # Sort by confidence (most confident first)
        findings.sort(key=lambda x: x.confidence, reverse=True)
        
        return findings
    
    def _infer_location(self, disease: str, metadata: Dict = None) -> str:
        """Infer anatomical location of finding."""
        # Simple heuristic mapping
        location_map = {
            'Cardiomegaly': 'Cardiac silhouette',
            'Pneumonia': 'Lung parenchyma',
            'Pneumothorax': 'Pleural space',
            'Effusion': 'Pleural cavity',
            'Atelectasis': 'Lung fields',
            'Mass': 'Lung fields',
            'Nodule': 'Lung parenchyma',
        }
        return location_map.get(disease, 'Chest')
    
    def _generate_description(
        self, 
        disease: str, 
        confidence: float, 
        severity: str
    ) -> str:
        """Generate textual description of finding."""
        descriptions = {
            'Atelectasis': f"Evidence of atelectasis with {severity} appearance",
            'Cardiomegaly': f"Enlarged cardiac silhouette suggesting {severity} cardiomegaly",
            'Effusion': f"{severity.capitalize()} pleural effusion observed",
            'Pneumonia': f"Findings consistent with {severity} pneumonia",
            'Pneumothorax': f"{severity.capitalize()} pneumothorax identified",
            'Mass': f"Mass lesion detected, {severity} characteristics",
            'Nodule': f"Pulmonary nodule visualized, {severity} features",
        }
        return descriptions.get(disease, f"{disease} detected with {severity} severity")
    
    def analyze(
        self, 
        features: np.ndarray, 
        metadata: Dict = None
    ) -> Dict:
        """
        Complete analysis of image features.
        
        Args:
            features: Feature vector from Vision Agent
            metadata: Image metadata
            
        Returns:
            Complete analysis results
        """
        # Classify diseases
        disease_probs = self.classify_diseases(features)
        
        # Extract significant findings
        findings = self.extract_findings(disease_probs, metadata)
        
        # Determine overall assessment
        if not findings:
            overall = "No significant abnormalities detected"
            risk_level = "low"
        elif any(f.severity == 'severe' for f in findings):
            overall = "Significant abnormalities requiring urgent attention"
            risk_level = "high"
        elif any(f.severity == 'moderate' for f in findings):
            overall = "Notable findings requiring follow-up"
            risk_level = "medium"
        else:
            overall = "Minor findings, clinical correlation recommended"
            risk_level = "low"
        
        return {
            'disease_probabilities': disease_probs,
            'findings': [
                {
                    'condition': f.condition,
                    'confidence': f.confidence,
                    'severity': f.severity,
                    'location': f.location,
                    'description': f.description
                }
                for f in findings
            ],
            'overall_assessment': overall,
            'risk_level': risk_level,
            'num_findings': len(findings)
        }


# Example usage
if __name__ == "__main__":
    agent = AnalysisAgent(confidence_threshold=0.3)
    
    # Example: Analyze dummy features
    dummy_features = np.random.randn(2048)
    results = agent.analyze(dummy_features)
    
    print(f"Analysis complete!")
    print(f"Findings: {results['num_findings']}")
    print(f"Risk level: {results['risk_level']}")
    print(f"Assessment: {results['overall_assessment']}")
