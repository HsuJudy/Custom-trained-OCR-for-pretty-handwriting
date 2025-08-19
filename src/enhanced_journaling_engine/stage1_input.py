#!/usr/bin/env python3
"""
Stage 1: The Input Module (OCR & Metadata Capture)

This module handles the conversion of raw, physical journal pages into structured digital data.
Includes custom OCR, timestamp/date recognition, and color-coded sticker detection.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.image_processing import preprocess_image, segment_lines
from src.inference.ocr_model import OCRModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JournalEntry:
    """Represents a single journal entry with all metadata."""
    entry_id: str
    date: Optional[datetime]
    color_code: Optional[str]
    text_content: str
    page_number: Optional[int]
    confidence: float
    original_image_path: str
    enhanced_text: Optional[str] = None
    themes: List[str] = None
    characters: List[str] = None
    locations: List[str] = None
    sentiment: Optional[float] = None
    
    def __post_init__(self):
        if self.themes is None:
            self.themes = []
        if self.characters is None:
            self.characters = []
        if self.locations is None:
            self.locations = []


class ColorStickerDetector:
    """Detects and identifies color-coded stickers in journal pages."""
    
    def __init__(self):
        # Define common sticker colors and their RGB ranges
        self.color_ranges = {
            'red': ([0, 100, 100], [10, 255, 255]),      # HSV red range
            'blue': ([100, 100, 100], [130, 255, 255]),  # HSV blue range
            'green': ([40, 100, 100], [80, 255, 255]),   # HSV green range
            'yellow': ([20, 100, 100], [30, 255, 255]),  # HSV yellow range
            'purple': ([130, 100, 100], [160, 255, 255]), # HSV purple range
            'orange': ([10, 100, 100], [20, 255, 255]),  # HSV orange range
        }
        
        self.color_hex_codes = {
            'red': '#FF0000',
            'blue': '#0000FF', 
            'green': '#00FF00',
            'yellow': '#FFFF00',
            'purple': '#800080',
            'orange': '#FFA500'
        }
    
    def detect_stickers(self, image_path: str) -> List[Dict]:
        """
        Detect color-coded stickers in an image.
        
        Args:
            image_path: Path to the journal page image
            
        Returns:
            List of detected stickers with color and position information
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not load image: {image_path}")
            return []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        detected_stickers = []
        
        for color_name, (lower, upper) in self.color_ranges.items():
            # Create mask for this color
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter by area to avoid noise
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    detected_stickers.append({
                        'color': color_name,
                        'color_hex': self.color_hex_codes[color_name],
                        'position': (center_x, center_y),
                        'area': area,
                        'bbox': (x, y, w, h)
                    })
        
        logger.info(f"Detected {len(detected_stickers)} stickers in {image_path}")
        return detected_stickers


class DateRecognizer:
    """Recognizes and extracts dates from journal entries."""
    
    def __init__(self):
        # Common date patterns
        self.date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',
            r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b'
        ]
        
        self.month_mapping = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def extract_date(self, text: str) -> Optional[datetime]:
        """
        Extract date from text using multiple patterns.
        
        Args:
            text: Text to search for dates
            
        Returns:
            Parsed datetime object or None if no date found
        """
        text_lower = text.lower()
        
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Try to parse the first match
                    date_str = matches[0]
                    return self._parse_date_string(date_str)
                except Exception as e:
                    logger.warning(f"Failed to parse date '{matches[0]}': {e}")
                    continue
        
        return None
    
    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse a date string into a datetime object."""
        # Remove extra whitespace and normalize
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Handle various formats
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                month, day, year = map(int, parts)
                if year < 100:
                    year += 2000
                return datetime(year, month, day)
        
        elif '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                month, day, year = map(int, parts)
                if year < 100:
                    year += 2000
                return datetime(year, month, day)
        
        elif '.' in date_str:
            parts = date_str.split('.')
            if len(parts) == 3:
                month, day, year = map(int, parts)
                if year < 100:
                    year += 2000
                return datetime(year, month, day)
        
        else:
            # Handle text-based dates like "January 15, 2025"
            for month_name, month_num in self.month_mapping.items():
                if month_name in date_str.lower():
                    # Extract day and year
                    numbers = re.findall(r'\d+', date_str)
                    if len(numbers) >= 2:
                        day = int(numbers[0])
                        year = int(numbers[1])
                        return datetime(year, month_num, day)
        
        raise ValueError(f"Could not parse date string: {date_str}")


class InputModule:
    """Main input module that orchestrates OCR and metadata capture."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.ocr_model = OCRModel(model_path) if model_path else None
        self.sticker_detector = ColorStickerDetector()
        self.date_recognizer = DateRecognizer()
        self.entry_counter = 0
    
    def process_journal_page(self, image_path: str, page_number: int) -> List[JournalEntry]:
        """
        Process a single journal page and extract entries with metadata.
        
        Args:
            image_path: Path to the journal page image
            page_number: Page number for this image
            
        Returns:
            List of JournalEntry objects with full metadata
        """
        logger.info(f"Processing journal page: {image_path}")
        
        # Detect color stickers
        stickers = self.sticker_detector.detect_stickers(image_path)
        
        # Segment page into lines
        lines = self._segment_page(image_path)
        
        entries = []
        current_entry_text = []
        current_sticker = None
        
        for i, line_data in enumerate(lines):
            # Extract text from line
            if self.ocr_model:
                text, confidence = self.ocr_model.predict(line_data['image_path'])
            else:
                # Fallback to placeholder text
                text = f"[Line {i+1} - OCR not available]"
                confidence = 0.5
            
            # Check if line contains a date (new entry)
            detected_date = self.date_recognizer.extract_date(text)
            
            if detected_date or i == 0:
                # Save previous entry if exists
                if current_entry_text:
                    entry = self._create_entry(
                        text=' '.join(current_entry_text),
                        date=None,  # Will be set from first line with date
                        color_code=current_sticker,
                        page_number=page_number,
                        confidence=confidence,
                        image_path=image_path
                    )
                    entries.append(entry)
                
                # Start new entry
                current_entry_text = [text]
                current_sticker = self._get_sticker_for_line(line_data, stickers)
                
                # If this line has a date, use it
                if detected_date:
                    # Update the previous entry's date if it exists
                    if entries:
                        entries[-1].date = detected_date
            else:
                # Continue current entry
                current_entry_text.append(text)
        
        # Save final entry
        if current_entry_text:
            entry = self._create_entry(
                text=' '.join(current_entry_text),
                date=None,
                color_code=current_sticker,
                page_number=page_number,
                confidence=confidence,
                image_path=image_path
            )
            entries.append(entry)
        
        logger.info(f"Extracted {len(entries)} entries from page {page_number}")
        return entries
    
    def _segment_page(self, image_path: str) -> List[Dict]:
        """Segment a page into individual lines."""
        try:
            # Use existing segmentation logic
            lines = segment_lines(preprocess_image(cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)))
            
            # Convert to our format
            line_data = []
            for i, (line_img, bbox) in enumerate(lines):
                # Save line image
                line_path = f"{Path(image_path).stem}_line_{i+1:03d}.jpg"
                cv2.imwrite(line_path, line_img)
                
                line_data.append({
                    'image_path': line_path,
                    'bbox': bbox,
                    'line_number': i + 1
                })
            
            return line_data
        except Exception as e:
            logger.error(f"Error segmenting page {image_path}: {e}")
            return []
    
    def _get_sticker_for_line(self, line_data: Dict, stickers: List[Dict]) -> Optional[str]:
        """Determine which sticker (if any) applies to this line."""
        if not stickers:
            return None
        
        line_center_y = line_data['bbox'][1] + line_data['bbox'][3] // 2
        
        # Find the closest sticker to this line
        closest_sticker = None
        min_distance = float('inf')
        
        for sticker in stickers:
            sticker_y = sticker['position'][1]
            distance = abs(line_center_y - sticker_y)
            
            if distance < min_distance and distance < 100:  # Within 100 pixels
                min_distance = distance
                closest_sticker = sticker
        
        return closest_sticker['color_hex'] if closest_sticker else None
    
    def _create_entry(self, text: str, date: Optional[datetime], color_code: Optional[str],
                     page_number: int, confidence: float, image_path: str) -> JournalEntry:
        """Create a JournalEntry object."""
        self.entry_counter += 1
        
        return JournalEntry(
            entry_id=f"entry_{self.entry_counter:04d}",
            date=date,
            color_code=color_code,
            text_content=text,
            page_number=page_number,
            confidence=confidence,
            original_image_path=image_path
        )
    
    def process_journal_directory(self, input_dir: str) -> List[JournalEntry]:
        """
        Process all journal pages in a directory.
        
        Args:
            input_dir: Directory containing journal page images
            
        Returns:
            List of all JournalEntry objects
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"Input directory {input_dir} does not exist")
        
        # Get all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.tiff', '*.bmp']:
            image_files.extend(input_path.glob(ext))
        
        image_files.sort()  # Ensure chronological order
        
        all_entries = []
        
        for i, image_file in enumerate(image_files):
            try:
                entries = self.process_journal_page(str(image_file), i + 1)
                all_entries.extend(entries)
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
                continue
        
        logger.info(f"Processed {len(image_files)} pages, extracted {len(all_entries)} entries")
        return all_entries
    
    def save_entries(self, entries: List[JournalEntry], output_path: str):
        """Save entries to JSON file."""
        # Convert entries to serializable format
        serializable_entries = []
        for entry in entries:
            entry_dict = {
                'entry_id': entry.entry_id,
                'date': entry.date.isoformat() if entry.date else None,
                'color_code': entry.color_code,
                'text_content': entry.text_content,
                'page_number': entry.page_number,
                'confidence': entry.confidence,
                'original_image_path': entry.original_image_path,
                'enhanced_text': entry.enhanced_text,
                'themes': entry.themes,
                'characters': entry.characters,
                'locations': entry.locations,
                'sentiment': entry.sentiment
            }
            serializable_entries.append(entry_dict)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(serializable_entries, f, indent=2)
        
        logger.info(f"Saved {len(entries)} entries to {output_path}")


def main():
    """Example usage of the Input Module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process journal pages with OCR and metadata extraction')
    parser.add_argument('--input_dir', required=True, help='Directory containing journal page images')
    parser.add_argument('--output_file', required=True, help='Output JSON file for entries')
    parser.add_argument('--model_path', help='Path to custom OCR model')
    
    args = parser.parse_args()
    
    # Initialize input module
    input_module = InputModule(args.model_path)
    
    # Process journal pages
    entries = input_module.process_journal_directory(args.input_dir)
    
    # Save results
    input_module.save_entries(entries, args.output_file)
    
    print(f"✅ Processed {len(entries)} journal entries")
    print(f"📁 Results saved to: {args.output_file}")


if __name__ == "__main__":
    main()
