#!/usr/bin/env python3
"""
Enhanced Journaling Engine - Main Orchestrator

This script orchestrates all four stages of the Enhanced Journaling Engine:
1. Input Module (OCR & Metadata Capture)
2. Analysis Module (Thread Identification) 
3. Enhancement Module (Creative Enhancement)
4. Output Module (Document Generation)
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.enhanced_journaling_engine.stage1_input import InputModule, JournalEntry
from src.enhanced_journaling_engine.stage2_analysis import AnalysisModule, AnalysisResult
from src.enhanced_journaling_engine.stage3_enhancement import EnhancementModule, EnhancedEntry
from src.enhanced_journaling_engine.stage4_output import OutputModule, PublicationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedJournalingEngine:
    """Main orchestrator for the Enhanced Journaling Engine."""
    
    def __init__(self, config: Dict):
        """Initialize the engine with configuration."""
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize modules
        self.input_module = InputModule(config.get('model_path'))
        self.analysis_module = AnalysisModule(config['gemini_api_key'])
        self.enhancement_module = EnhancementModule(config['gemini_api_key'])
        
        # Publication config
        self.publication_config = PublicationConfig(
            title=config.get('title', 'My Enhanced Journal'),
            author=config.get('author', 'Unknown Author'),
            subtitle=config.get('subtitle'),
            include_original=config.get('include_original', True),
            include_analysis=config.get('include_analysis', True),
            color_coding=config.get('color_coding', True),
            theme_organization=config.get('theme_organization', True)
        )
        
        self.output_module = OutputModule(self.publication_config)
        
        # Data storage
        self.entries: List[JournalEntry] = []
        self.analyses: List[AnalysisResult] = []
        self.enhanced_entries: List[EnhancedEntry] = []
    
    def run_stage1_input(self, input_dir: str) -> List[JournalEntry]:
        """Run Stage 1: Input Module (OCR & Metadata Capture)."""
        logger.info("🚀 Starting Stage 1: Input Module")
        
        # Process journal pages
        entries = self.input_module.process_journal_directory(input_dir)
        
        # Save raw entries
        entries_file = self.output_dir / 'stage1_entries.json'
        self.input_module.save_entries(entries, str(entries_file))
        
        self.entries = entries
        logger.info(f"✅ Stage 1 Complete: Processed {len(entries)} entries")
        return entries
    
    def run_stage2_analysis(self, entries: List[JournalEntry]) -> List[AnalysisResult]:
        """Run Stage 2: Analysis Module (Thread Identification)."""
        logger.info("🧠 Starting Stage 2: Analysis Module")
        
        # Analyze entries
        analyses = self.analysis_module.analyze_entries(entries)
        
        # Generate summary and threads
        summary = self.analysis_module.generate_theme_summary(analyses)
        threads = self.analysis_module.identify_narrative_threads(analyses)
        
        # Save analysis results
        analysis_file = self.output_dir / 'stage2_analysis.json'
        summary_file = self.output_dir / 'stage2_summary.json'
        
        self.analysis_module.save_analysis_results(analyses, str(analysis_file))
        self.analysis_module.save_analysis_summary(summary, threads, str(summary_file))
        
        self.analyses = analyses
        logger.info(f"✅ Stage 2 Complete: Analyzed {len(analyses)} entries")
        logger.info(f"📊 Found {len(summary['theme_frequency'])} unique themes")
        logger.info(f"🧵 Identified {len(threads)} narrative threads")
        return analyses
    
    def run_stage3_enhancement(self, entries: List[JournalEntry], 
                              analyses: List[AnalysisResult]) -> List[EnhancedEntry]:
        """Run Stage 3: Enhancement Module (Creative Enhancement)."""
        logger.info("✨ Starting Stage 3: Enhancement Module")
        
        # Apply batch enhancement
        enhancement_strategy = self.config.get('enhancement_strategy', 'default')
        enhanced_entries = self.enhancement_module.batch_enhance(
            entries, analyses, enhancement_strategy
        )
        
        # Generate enhancement report
        report = self.enhancement_module.generate_enhancement_report(enhanced_entries)
        
        # Save enhanced entries and report
        enhanced_file = self.output_dir / 'stage3_enhanced.json'
        report_file = self.output_dir / 'stage3_report.json'
        
        self.enhancement_module.save_enhanced_entries(enhanced_entries, str(enhanced_file))
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.enhanced_entries = enhanced_entries
        logger.info(f"✅ Stage 3 Complete: Enhanced {len(enhanced_entries)} entries")
        logger.info(f"📈 Added {report['total_words_added']} words "
                   f"({report['average_enhancement_ratio']:.1f}x enhancement)")
        return enhanced_entries
    
    def run_stage4_output(self, enhanced_entries: List[EnhancedEntry],
                         analysis_summary: Dict) -> Dict[str, str]:
        """Run Stage 4: Output Module (Document Generation)."""
        logger.info("📄 Starting Stage 4: Output Module")
        
        # Generate documents
        output_formats = self.config.get('output_formats', ['markdown', 'html'])
        documents = self.output_module.generate_document(
            enhanced_entries, analysis_summary, output_formats
        )
        
        # Save documents
        documents_dir = self.output_dir / 'documents'
        saved_files = self.output_module.save_documents(documents, str(documents_dir))
        
        # Generate publication report
        report = self.output_module.generate_publication_report(enhanced_entries, analysis_summary)
        report_file = documents_dir / 'publication_report.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Stage 4 Complete: Generated {len(output_formats)} document formats")
        logger.info(f"📄 Saved {len(saved_files)} files to {documents_dir}")
        return documents
    
    def run_full_pipeline(self, input_dir: str) -> Dict:
        """Run the complete Enhanced Journaling Engine pipeline."""
        logger.info("🎯 Starting Enhanced Journaling Engine Pipeline")
        logger.info(f"📁 Input directory: {input_dir}")
        logger.info(f"📁 Output directory: {self.output_dir}")
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Input
            entries = self.run_stage1_input(input_dir)
            
            # Stage 2: Analysis
            analyses = self.run_stage2_analysis(entries)
            
            # Load analysis summary for Stage 4
            summary_file = self.output_dir / 'stage2_summary.json'
            with open(summary_file, 'r') as f:
                analysis_summary = json.load(f)
            
            # Stage 3: Enhancement
            enhanced_entries = self.run_stage3_enhancement(entries, analyses)
            
            # Stage 4: Output
            documents = self.run_stage4_output(enhanced_entries, analysis_summary)
            
            # Calculate total time
            end_time = datetime.now()
            total_time = end_time - start_time
            
            # Generate final summary
            pipeline_summary = {
                'pipeline_info': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'total_time_seconds': total_time.total_seconds(),
                    'input_directory': input_dir,
                    'output_directory': str(self.output_dir)
                },
                'results': {
                    'total_entries': len(entries),
                    'total_themes': len(analysis_summary['summary']['theme_frequency']),
                    'total_narrative_threads': len(analysis_summary['narrative_threads']),
                    'enhancement_ratio': analysis_summary['summary']['average_sentiment'],
                    'output_formats': list(documents.keys())
                },
                'files_generated': {
                    'stage1_entries': str(self.output_dir / 'stage1_entries.json'),
                    'stage2_analysis': str(self.output_dir / 'stage2_analysis.json'),
                    'stage2_summary': str(self.output_dir / 'stage2_summary.json'),
                    'stage3_enhanced': str(self.output_dir / 'stage3_enhanced.json'),
                    'stage3_report': str(self.output_dir / 'stage3_report.json'),
                    'documents': str(self.output_dir / 'documents')
                }
            }
            
            # Save pipeline summary
            summary_file = self.output_dir / 'pipeline_summary.json'
            with open(summary_file, 'w') as f:
                json.dump(pipeline_summary, f, indent=2)
            
            logger.info("🎉 Enhanced Journaling Engine Pipeline Complete!")
            logger.info(f"⏱️  Total time: {total_time.total_seconds():.1f} seconds")
            logger.info(f"📊 Processed {len(entries)} entries")
            logger.info(f"📁 All files saved to: {self.output_dir}")
            
            return pipeline_summary
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
    
    def run_single_stage(self, stage: str, input_dir: str = None):
        """Run a single stage of the pipeline."""
        if stage == 'input' and input_dir:
            return self.run_stage1_input(input_dir)
        elif stage == 'analysis' and self.entries:
            return self.run_stage2_analysis(self.entries)
        elif stage == 'enhancement' and self.entries and self.analyses:
            return self.run_stage3_enhancement(self.entries, self.analyses)
        elif stage == 'output' and self.enhanced_entries:
            # Load analysis summary
            summary_file = self.output_dir / 'stage2_summary.json'
            with open(summary_file, 'r') as f:
                analysis_summary = json.load(f)
            return self.run_stage4_output(self.enhanced_entries, analysis_summary)
        else:
            raise ValueError(f"Cannot run stage '{stage}' - missing dependencies")


def create_config_from_args(args) -> Dict:
    """Create configuration dictionary from command line arguments."""
    config = {
        'gemini_api_key': args.gemini_api_key,
        'output_dir': args.output_dir,
        'title': args.title,
        'author': args.author,
        'subtitle': args.subtitle,
        'enhancement_strategy': args.enhancement_strategy,
        'output_formats': args.output_formats,
        'include_original': args.include_original,
        'include_analysis': args.include_analysis,
        'color_coding': args.color_coding,
        'theme_organization': args.theme_organization
    }
    
    if args.model_path:
        config['model_path'] = args.model_path
    
    return config


def main():
    """Main entry point for the Enhanced Journaling Engine."""
    parser = argparse.ArgumentParser(
        description='Enhanced Journaling Engine - Transform handwritten journals into published editions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python main.py --input_dir journal_pages/ --gemini_api_key YOUR_KEY --title "My Journal" --author "John Doe"
  
  # Run with custom enhancement strategy
  python main.py --input_dir journal_pages/ --gemini_api_key YOUR_KEY --enhancement_strategy extensive
  
  # Run single stage
  python main.py --input_dir journal_pages/ --gemini_api_key YOUR_KEY --stage input
        """
    )
    
    # Required arguments
    parser.add_argument('--input_dir', required=True, help='Directory containing journal page images')
    parser.add_argument('--gemini_api_key', required=True, help='Gemini API key for analysis and enhancement')
    parser.add_argument('--title', required=True, help='Document title')
    parser.add_argument('--author', required=True, help='Document author')
    
    # Optional arguments
    parser.add_argument('--output_dir', default='output', help='Output directory for all files')
    parser.add_argument('--subtitle', help='Document subtitle')
    parser.add_argument('--model_path', help='Path to custom OCR model')
    parser.add_argument('--enhancement_strategy', default='default',
                       choices=['default', 'minimal', 'extensive'],
                       help='Enhancement strategy to apply')
    parser.add_argument('--output_formats', nargs='+', default=['markdown', 'html'],
                       choices=['markdown', 'html', 'json'],
                       help='Output formats to generate')
    
    # Configuration flags
    parser.add_argument('--include_original', action='store_true', default=True,
                       help='Include original text in output')
    parser.add_argument('--include_analysis', action='store_true', default=True,
                       help='Include analysis metadata in output')
    parser.add_argument('--color_coding', action='store_true', default=True,
                       help='Apply color coding to entries')
    parser.add_argument('--theme_organization', action='store_true', default=True,
                       help='Organize by themes')
    
    # Stage selection
    parser.add_argument('--stage', choices=['input', 'analysis', 'enhancement', 'output'],
                       help='Run only a specific stage (requires previous stages to be completed)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Initialize engine
    engine = EnhancedJournalingEngine(config)
    
    try:
        if args.stage:
            # Run single stage
            logger.info(f"Running single stage: {args.stage}")
            result = engine.run_single_stage(args.stage, args.input_dir)
            logger.info(f"✅ Stage {args.stage} complete")
        else:
            # Run full pipeline
            result = engine.run_full_pipeline(args.input_dir)
            
            # Print summary
            print("\n" + "="*60)
            print("🎉 ENHANCED JOURNALING ENGINE COMPLETE!")
            print("="*60)
            print(f"📊 Processed {result['results']['total_entries']} entries")
            print(f"🎨 Found {result['results']['total_themes']} unique themes")
            print(f"🧵 Identified {result['results']['total_narrative_threads']} narrative threads")
            print(f"⏱️  Total time: {result['pipeline_info']['total_time_seconds']:.1f} seconds")
            print(f"📁 Output directory: {result['pipeline_info']['output_directory']}")
            print("="*60)
            
    except Exception as e:
        logger.error(f"❌ Engine failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
