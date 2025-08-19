"""
Text processing utilities for handwriting OCR.
"""

import re
import string
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize transcribed text.
    
    Args:
        text: Raw transcribed text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalize quotes and apostrophes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Normalize dashes
    text = re.sub(r'[–—]', '-', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text


def extract_metadata(text: str) -> Dict[str, any]:
    """
    Extract metadata from text (dates, signatures, etc.).
    
    Args:
        text: Input text
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {
        'has_date': False,
        'has_signature': False,
        'word_count': 0,
        'char_count': 0,
        'line_count': 0
    }
    
    if not text:
        return metadata
    
    # Count basic statistics
    metadata['char_count'] = len(text)
    metadata['word_count'] = len(text.split())
    metadata['line_count'] = len(text.split('\n'))
    
    # Check for dates (various formats)
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'      # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            metadata['has_date'] = True
            break
    
    # Check for signatures (common patterns)
    signature_patterns = [
        r'\b(?:sincerely|yours truly|best regards|love|cheers|thanks|thank you)\b',
        r'\b(?:signed|signature|sign)\b',
        r'[A-Z][a-z]+ [A-Z][a-z]+',  # Name pattern
        r'[A-Z]\.[A-Z]\.',  # Initials
    ]
    
    for pattern in signature_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            metadata['has_signature'] = True
            break
    
    return metadata


def generate_character_set(texts: List[str]) -> str:
    """
    Generate character set from a list of texts.
    
    Args:
        texts: List of text strings
        
    Returns:
        String containing all unique characters
    """
    all_chars = set()
    
    for text in texts:
        if text:
            all_chars.update(text)
    
    # Sort characters
    charset = ''.join(sorted(all_chars))
    
    return charset


def create_vocabulary(texts: List[str], min_freq: int = 2) -> Dict[str, int]:
    """
    Create vocabulary from texts with frequency counts.
    
    Args:
        texts: List of text strings
        min_freq: Minimum frequency for a word to be included
        
    Returns:
        Dictionary mapping words to their frequencies
    """
    word_freq = {}
    
    for text in texts:
        if not text:
            continue
        
        # Split into words and count
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Filter by minimum frequency
    vocabulary = {word: freq for word, freq in word_freq.items() if freq >= min_freq}
    
    return vocabulary


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def remove_special_characters(text: str, keep_chars: str = "") -> str:
    """
    Remove special characters from text.
    
    Args:
        text: Input text
        keep_chars: Characters to keep (in addition to alphanumeric and space)
        
    Returns:
        Text with special characters removed
    """
    # Define characters to keep
    allowed_chars = string.ascii_letters + string.digits + string.whitespace + keep_chars
    
    # Filter text
    filtered_text = ''.join(char for char in text if char in allowed_chars)
    
    return filtered_text


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting (can be improved with NLP libraries)
    sentences = re.split(r'[.!?]+', text)
    
    # Clean up sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using character-level comparison.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to sets of characters
    chars1 = set(text1.lower())
    chars2 = set(text2.lower())
    
    # Calculate Jaccard similarity
    intersection = len(chars1.intersection(chars2))
    union = len(chars1.union(chars2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """
    Extract keywords from text based on frequency.
    
    Args:
        text: Input text
        top_k: Number of top keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Split into words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        if len(word) > 2:  # Skip very short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top k
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:top_k]]
    
    return keywords


def validate_text_quality(text: str) -> Dict[str, any]:
    """
    Validate the quality of transcribed text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary containing quality metrics
    """
    quality_metrics = {
        'is_empty': False,
        'is_too_short': False,
        'is_too_long': False,
        'has_repeated_chars': False,
        'has_mixed_case': False,
        'confidence_score': 1.0
    }
    
    if not text:
        quality_metrics['is_empty'] = True
        quality_metrics['confidence_score'] = 0.0
        return quality_metrics
    
    # Check length
    if len(text) < 3:
        quality_metrics['is_too_short'] = True
        quality_metrics['confidence_score'] *= 0.5
    
    if len(text) > 500:
        quality_metrics['is_too_long'] = True
        quality_metrics['confidence_score'] *= 0.8
    
    # Check for repeated characters (common OCR error)
    repeated_pattern = re.search(r'(.)\1{3,}', text)
    if repeated_pattern:
        quality_metrics['has_repeated_chars'] = True
        quality_metrics['confidence_score'] *= 0.7
    
    # Check for mixed case (might indicate OCR issues)
    has_upper = any(c.isupper() for c in text)
    has_lower = any(c.islower() for c in text)
    if has_upper and has_lower:
        quality_metrics['has_mixed_case'] = True
        # This might be normal for handwriting, so don't penalize too much
        quality_metrics['confidence_score'] *= 0.9
    
    return quality_metrics
