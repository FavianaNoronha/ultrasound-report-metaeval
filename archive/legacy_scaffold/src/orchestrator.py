"""
Medical Imaging AI Orchestrator
Coordinates all agents to produce complete radiology reports
"""

from typing import Dict, Optional
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.vision_agent import VisionAgent
from agent.analysis_agent import AnalysisAgent
from agent.report_agent import ReportAgent


class MedicalImagingOrchestrator:
    """
    Main orchestrator that coordinates all agents to analyze
    medical images and generate reports.
    """
    
    def __init__(
        self,
        vision_model: str = "resnet50",
        confidence_threshold: float = 0.5,
        use_llm_reports: bool = False,
        llm_api_key: Optional[str] = None,
        device: str = "auto"
    ):
        """
        Initialize the orchestrator with all agents.
        
        Args:
            vision_model: Vision model to use
            confidence_threshold: Minimum confidence for findings
            use_llm_reports: Whether to use LLM for report generation
            llm_api_key: API key for LLM service
            device: Device to use (auto/cuda/cpu)
        """
        # Determine device
        if device == "auto":
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"🚀 Initializing Medical Imaging AI System...")
        print(f"   Device: {device}")
        
        # Initialize agents
        print("   Loading Vision Agent...")
        self.vision_agent = VisionAgent(
            model_name=vision_model,
            device=device
        )
        
        print("   Loading Analysis Agent...")
        self.analysis_agent = AnalysisAgent(
            confidence_threshold=confidence_threshold,
            device=device
        )
        
        print("   Loading Report Agent...")
        self.report_agent = ReportAgent(
            use_llm=use_llm_reports,
            llm_api_key=llm_api_key
        )
        
        print("✅ System initialized successfully!\n")
    
    def process_image(
        self,
        image_path: str,
        output_dir: Optional[str] = None,
        save_report: bool = True,
        report_format: str = 'text'
    ) -> Dict:
        """
        Complete pipeline: analyze image and generate report.
        
        Args:
            image_path: Path to medical image
            output_dir: Directory to save report
            save_report: Whether to save report to file
            report_format: Format of report (text/llm/json)
            
        Returns:
            Dictionary containing all results
        """
        print(f"📁 Processing: {os.path.basename(image_path)}")
        
        # Step 1: Vision Analysis
        print("   👁️  Running vision analysis...")
        vision_results = self.vision_agent.analyze_image(image_path)
        features = vision_results['features']
        metadata = vision_results['metadata']
        
        # Step 2: Medical Analysis
        print("   🔬 Analyzing medical findings...")
        analysis_results = self.analysis_agent.analyze(features, metadata)
        
        # Step 3: Report Generation
        print("   📝 Generating radiology report...")
        report = self.report_agent.generate_report(
            analysis_results,
            metadata,
            output_format=report_format
        )
        
        # Save report if requested
        if save_report and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            extension = 'json' if report_format == 'json' else 'txt'
            report_path = os.path.join(output_dir, f"{base_name}_report.{extension}")
            
            self.report_agent.save_report(report, report_path)
            print(f"   💾 Report saved to: {report_path}")
        
        print("   ✅ Processing complete!\n")
        
        return {
            'image_path': image_path,
            'vision_results': vision_results,
            'analysis_results': analysis_results,
            'report': report,
            'risk_level': analysis_results['risk_level'],
            'num_findings': analysis_results['num_findings']
        }
    
    def process_batch(
        self,
        image_paths: list,
        output_dir: str = "output/reports",
        report_format: str = 'text'
    ) -> list:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of image paths
            output_dir: Output directory for reports
            report_format: Format of reports
            
        Returns:
            List of results for each image
        """
        print(f"🔄 Starting batch processing of {len(image_paths)} images...")
        print("=" * 60)
        
        results = []
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}]")
            try:
                result = self.process_image(
                    image_path,
                    output_dir=output_dir,
                    save_report=True,
                    report_format=report_format
                )
                results.append(result)
            except Exception as e:
                print(f"   ❌ Error processing {image_path}: {str(e)}")
                results.append({'error': str(e), 'image_path': image_path})
        
        print("=" * 60)
        print(f"✅ Batch processing complete!")
        print(f"   Processed: {len([r for r in results if 'error' not in r])}/{len(image_paths)}")
        print(f"   Failed: {len([r for r in results if 'error' in r])}/{len(image_paths)}")
        
        return results
    
    def get_summary_statistics(self, results: list) -> Dict:
        """
        Get summary statistics from batch processing results.
        
        Args:
            results: List of processing results
            
        Returns:
            Summary statistics
        """
        successful = [r for r in results if 'error' not in r]
        
        if not successful:
            return {'error': 'No successful analyses'}
        
        # Count findings by risk level
        risk_counts = {
            'high': len([r for r in successful if r['risk_level'] == 'high']),
            'medium': len([r for r in successful if r['risk_level'] == 'medium']),
            'low': len([r for r in successful if r['risk_level'] == 'low'])
        }
        
        # Average number of findings
        avg_findings = sum(r['num_findings'] for r in successful) / len(successful)
        
        return {
            'total_processed': len(results),
            'successful': len(successful),
            'failed': len(results) - len(successful),
            'risk_distribution': risk_counts,
            'average_findings_per_image': round(avg_findings, 2),
            'high_risk_cases': risk_counts['high']
        }


def main():
    """Example usage of the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Medical Imaging AI System')
    parser.add_argument('--image', type=str, help='Path to single image')
    parser.add_argument('--batch', type=str, help='Path to directory of images')
    parser.add_argument('--output', type=str, default='output/reports', 
                       help='Output directory for reports')
    parser.add_argument('--format', type=str, default='text',
                       choices=['text', 'json', 'llm'],
                       help='Report format')
    parser.add_argument('--llm-key', type=str, help='API key for LLM')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = MedicalImagingOrchestrator(
        use_llm_reports=(args.format == 'llm'),
        llm_api_key=args.llm_key
    )
    
    # Process image(s)
    if args.image:
        result = orchestrator.process_image(
            args.image,
            output_dir=args.output,
            report_format=args.format
        )
        print("\n" + "=" * 60)
        print("REPORT:")
        print("=" * 60)
        print(result['report'])
        
    elif args.batch:
        # Get all images in directory
        import glob
        image_extensions = ['*.dcm', '*.jpg', '*.jpeg', '*.png']
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(glob.glob(os.path.join(args.batch, ext)))
        
        if not image_paths:
            print(f"❌ No images found in {args.batch}")
            return
        
        results = orchestrator.process_batch(
            image_paths,
            output_dir=args.output,
            report_format=args.format
        )
        
        # Print summary
        summary = orchestrator.get_summary_statistics(results)
        print("\n" + "=" * 60)
        print("BATCH SUMMARY:")
        print("=" * 60)
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    else:
        print("❌ Please provide either --image or --batch argument")
        parser.print_help()


if __name__ == "__main__":
    # Example without command line args
    print("Medical Imaging AI Orchestrator")
    print("For usage, run: python orchestrator.py --help")
    print("\nExample initialization:")
    
    orchestrator = MedicalImagingOrchestrator()
    print("\n✨ Ready to process medical images!")
