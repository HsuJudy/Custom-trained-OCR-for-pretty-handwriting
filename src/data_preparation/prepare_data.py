#!/usr/bin/env python3
"""
Data preparation script for custom handwriting OCR training.
Processes journal pages and prepares them for efficient labeling and training.
"""

import os
import sys
import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
from PIL import Image
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.image_processing import preprocess_image, segment_lines
from src.utils.text_processing import clean_text, extract_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreparator:
    """Handles data preparation for handwriting OCR training."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.pdf'}
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            return {
                'image_height': 224,
                'image_width': 224,
                'max_text_length': 200,
                'min_line_height': 20,
                'max_line_height': 100,
                'output_dir': 'data/processed',
                'metadata_file': 'data/metadata.json'
            }
    
    def process_input_directory(self, input_dir: str) -> Dict[str, List[str]]:
        """
        Process all files in the input directory and organize them by type.
        
        Args:
            input_dir: Path to directory containing journal pages
            
        Returns:
            Dictionary mapping file types to lists of file paths
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory {input_dir} does not exist")
        
        files_by_type = {
            'images': [],
            'pdfs': [],
            'unsupported': []
        }
        
        for file_path in input_path.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}:
                    files_by_type['images'].append(str(file_path))
                elif suffix == '.pdf':
                    files_by_type['pdfs'].append(str(file_path))
                else:
                    files_by_type['unsupported'].append(str(file_path))
        
        logger.info(f"Found {len(files_by_type['images'])} images, "
                   f"{len(files_by_type['pdfs'])} PDFs, "
                   f"{len(files_by_type['unsupported'])} unsupported files")
        
        return files_by_type
    
    def extract_pages_from_pdf(self, pdf_path: str, output_dir: str) -> List[str]:
        """
        Extract pages from PDF and save as images.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save extracted images
            
        Returns:
            List of paths to extracted images
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        pdf_name = Path(pdf_path).stem
        extracted_images = []
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            for i, image in enumerate(images):
                image_path = output_path / f"{pdf_name}_page_{i+1:03d}.jpg"
                image.save(image_path, 'JPEG', quality=95)
                extracted_images.append(str(image_path))
                
            logger.info(f"Extracted {len(images)} pages from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error extracting pages from {pdf_path}: {e}")
        
        return extracted_images
    
    def segment_page_into_lines(self, image_path: str, output_dir: str) -> List[Dict]:
        """
        Segment a page image into individual lines for easier labeling.
        
        Args:
            image_path: Path to page image
            output_dir: Directory to save line segments
            
        Returns:
            List of dictionaries containing line information
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Load and preprocess image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not load image: {image_path}")
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing
        processed = preprocess_image(gray)
        
        # Segment lines
        lines = segment_lines(processed)
        
        page_name = Path(image_path).stem
        line_data = []
        
        for i, (line_img, bbox) in enumerate(lines):
            # Save line image
            line_filename = f"{page_name}_line_{i+1:03d}.jpg"
            line_path = output_path / line_filename
            cv2.imwrite(str(line_path), line_img)
            
            # Store metadata
            line_info = {
                'id': f"{page_name}_line_{i+1:03d}",
                'image_path': str(line_path),
                'source_page': image_path,
                'bbox': bbox,
                'line_number': i + 1,
                'text': '',  # To be filled during labeling
                'confidence': 0.0,  # To be filled during labeling
                'labeled': False
            }
            line_data.append(line_info)
        
        logger.info(f"Segmented {len(lines)} lines from {image_path}")
        return line_data
    
    def create_labeling_dataset(self, input_dir: str, output_dir: str = None) -> str:
        """
        Create a dataset ready for labeling from input directory.
        
        Args:
            input_dir: Directory containing journal pages
            output_dir: Directory to save processed data
            
        Returns:
            Path to metadata file
        """
        if output_dir is None:
            output_dir = self.config['output_dir']
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process input directory
        files_by_type = self.process_input_directory(input_dir)
        
        all_line_data = []
        
        # Process images
        for image_path in files_by_type['images']:
            lines_dir = output_path / 'lines' / Path(image_path).stem
            line_data = self.segment_page_into_lines(image_path, str(lines_dir))
            all_line_data.extend(line_data)
        
        # Process PDFs
        pdf_output_dir = output_path / 'pdf_extracts'
        for pdf_path in files_by_type['pdfs']:
            # Extract pages from PDF
            extracted_images = self.extract_pages_from_pdf(pdf_path, str(pdf_output_dir))
            
            # Process each extracted page
            for image_path in extracted_images:
                lines_dir = output_path / 'lines' / Path(image_path).stem
                line_data = self.segment_page_into_lines(image_path, str(lines_dir))
                all_line_data.extend(line_data)
        
        # Save metadata
        metadata = {
            'dataset_info': {
                'total_lines': len(all_line_data),
                'total_pages': len(files_by_type['images']) + len(files_by_type['pdfs']),
                'created_at': str(Path().cwd()),
                'config': self.config
            },
            'lines': all_line_data
        }
        
        metadata_path = output_path / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Created dataset with {len(all_line_data)} lines")
        logger.info(f"Metadata saved to: {metadata_path}")
        
        return str(metadata_path)
    
    def generate_character_set(self, metadata_path: str) -> str:
        """
        Generate character set from labeled data.
        
        Args:
            metadata_path: Path to metadata file
            
        Returns:
            String containing all unique characters
        """
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        all_chars = set()
        labeled_lines = [line for line in metadata['lines'] if line.get('text', '').strip()]
        
        for line in labeled_lines:
            text = line.get('text', '')
            all_chars.update(text)
        
        charset = ''.join(sorted(all_chars))
        
        # Save character set
        charset_path = Path(metadata_path).parent / 'charset.txt'
        with open(charset_path, 'w') as f:
            f.write(charset)
        
        logger.info(f"Generated character set with {len(charset)} characters")
        logger.info(f"Character set saved to: {charset_path}")
        
        return charset


def main():
    parser = argparse.ArgumentParser(description='Prepare data for handwriting OCR training')
    parser.add_argument('--input_dir', required=True, help='Directory containing journal pages')
    parser.add_argument('--output_dir', help='Output directory for processed data')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--generate_charset', action='store_true', 
                       help='Generate character set from labeled data')
    
    args = parser.parse_args()
    
    # Initialize data preparator
    preparator = DataPreparator(args.config)
    
    # Create dataset
    metadata_path = preparator.create_labeling_dataset(args.input_dir, args.output_dir)
    
    # Generate character set if requested
    if args.generate_charset:
        preparator.generate_character_set(metadata_path)
    
    print(f"\n✅ Data preparation complete!")
    print(f"📁 Processed data saved to: {Path(metadata_path).parent}")
    print(f"📄 Metadata file: {metadata_path}")
    print(f"\nNext steps:")
    print(f"1. Run the labeling tool: python src/data_preparation/labeling_tool.py")
    print(f"2. Train the model: python src/training/train_ocr.py")


if __name__ == "__main__":
    main()
