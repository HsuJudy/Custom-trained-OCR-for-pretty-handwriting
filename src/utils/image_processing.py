"""
Image processing utilities for handwriting OCR preprocessing.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better handwriting recognition.
    
    Args:
        image: Input grayscale image
        
    Returns:
        Preprocessed image
    """
    # Ensure image is grayscale
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize image to standard size
    height, width = image.shape
    target_height = 224
    
    # Calculate new width maintaining aspect ratio
    aspect_ratio = width / height
    target_width = int(target_height * aspect_ratio)
    
    # Resize image
    resized = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(resized, (3, 3), 0)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Morphological operations to clean up the image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    return cleaned


def segment_lines(image: np.ndarray, min_line_height: int = 20, max_line_height: int = 100) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Segment image into individual lines of text.
    
    Args:
        image: Preprocessed binary image
        min_line_height: Minimum height for a line
        max_line_height: Maximum height for a line
        
    Returns:
        List of tuples (line_image, bbox)
    """
    # Find horizontal lines using morphological operations
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
    
    # Find contours
    contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by area and aspect ratio
    valid_contours = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter by height
        if min_line_height <= h <= max_line_height:
            # Filter by aspect ratio (lines should be wider than tall)
            aspect_ratio = w / h
            if aspect_ratio > 2.0:
                valid_contours.append((x, y, w, h))
    
    # Sort contours by y-coordinate (top to bottom)
    valid_contours.sort(key=lambda x: x[1])
    
    # Extract line images
    lines = []
    for x, y, w, h in valid_contours:
        # Add padding around the line
        padding = 10
        y_start = max(0, y - padding)
        y_end = min(image.shape[0], y + h + padding)
        x_start = max(0, x - padding)
        x_end = min(image.shape[1], x + w + padding)
        
        line_img = image[y_start:y_end, x_start:x_end]
        
        # Ensure minimum size
        if line_img.shape[0] > 0 and line_img.shape[1] > 0:
            lines.append((line_img, (x_start, y_start, x_end - x_start, y_end - y_start)))
    
    return lines


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance contrast of the image.
    
    Args:
        image: Input image
        
    Returns:
        Contrast enhanced image
    """
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    
    return enhanced


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    Remove noise from the image.
    
    Args:
        image: Input image
        
    Returns:
        Denoised image
    """
    # Apply bilateral filter to preserve edges while removing noise
    denoised = cv2.bilateralFilter(image, 9, 75, 75)
    
    return denoised


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew the image to correct slight rotations.
    
    Args:
        image: Input image
        
    Returns:
        Deskewed image
    """
    # Find contours
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image
    
    # Find the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Fit a rotated rectangle
    rect = cv2.minAreaRect(largest_contour)
    angle = rect[2]
    
    # Normalize angle
    if angle < -45:
        angle = 90 + angle
    
    # Rotate image
    if abs(angle) > 0.5:  # Only rotate if angle is significant
        height, width = image.shape
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height), 
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, 
                                borderValue=255)
        return rotated
    
    return image


def normalize_image(image: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Normalize image to target size with padding.
    
    Args:
        image: Input image
        target_size: Target size (height, width)
        
    Returns:
        Normalized image
    """
    target_height, target_width = target_size
    
    # Get current dimensions
    height, width = image.shape
    
    # Calculate scaling factor
    scale = min(target_height / height, target_width / width)
    
    # Resize image
    new_height = int(height * scale)
    new_width = int(width * scale)
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Create target image with white background
    normalized = np.ones((target_height, target_width), dtype=np.uint8) * 255
    
    # Calculate padding
    y_offset = (target_height - new_height) // 2
    x_offset = (target_width - new_width) // 2
    
    # Place resized image in center
    normalized[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
    
    return normalized
