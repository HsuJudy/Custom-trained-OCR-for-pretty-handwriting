#!/usr/bin/env python3
"""
Flask web application for the handwriting OCR system.
Provides web interfaces for data collection and model inference.
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import zipfile
import io
import base64
from PIL import Image
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import these only if needed for advanced features
try:
    from src.utils.image_processing import preprocess_image, segment_lines
    from src.data_preparation.prepare_data import DataPreparator
    ADVANCED_FEATURES = True
except ImportError:
    ADVANCED_FEATURES = False
    print("⚠️  Advanced features disabled - some dependencies may be missing")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['PROCESSED_FOLDER'] = 'data/processed'

# Ensure upload and processed directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main handwriting data collector interface."""
    return send_from_directory('.', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            logger.info(f"File uploaded: {filename}")
            return jsonify({
                'success': True,
                'filename': filename,
                'message': 'File uploaded successfully'
            })
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-dataset', methods=['POST'])
def process_dataset():
    """Process uploaded images and create a dataset for labeling."""
    try:
        data = request.get_json()
        if not data or 'dataset' not in data:
            return jsonify({'error': 'No dataset provided'}), 400
        
        dataset = data['dataset']
        if not dataset:
            return jsonify({'error': 'Empty dataset'}), 400
        
        # Create a timestamped directory for the dataset
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dataset_dir = os.path.join(app.config['PROCESSED_FOLDER'], f'temp_dataset_{timestamp}')
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Save cropped images and create metadata
        metadata = {
            'dataset_info': {
                'total_samples': len(dataset),
                'created_at': datetime.now().isoformat(),
                'source': 'web_interface',
                'version': '2.0'  # New version with improved UI
            },
            'samples': []
        }
        
        # Track unique labels for summary
        unique_labels = set()
        labels = []
        
        for i, item in enumerate(dataset):
            try:
                # Decode base64 image
                image_data = item['dataUrl'].split(',')[1]
                image_bytes = base64.b64decode(image_data)
                
                # Save image
                filename = f"{item['label']}_{i:04d}.png"
                image_path = os.path.join(dataset_dir, filename)
                
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Add to metadata
                sample_info = {
                    'id': f"sample_{i:04d}",
                    'filename': filename,
                    'label': item['label'],
                    'image_path': image_path,
                    'labeled': True
                }
                metadata['samples'].append(sample_info)
                
                # Track labels
                unique_labels.add(item['label'])
                labels.append(f"{filename},{item['label']}")
                
            except Exception as e:
                logger.error(f"Error processing item {i}: {e}")
                continue
        
        # Save metadata
        metadata_path = os.path.join(dataset_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save CSV file with labels
        csv_path = os.path.join(dataset_dir, 'labels.csv')
        with open(csv_path, 'w') as f:
            f.write('filename,label\n')
            f.write('\n'.join(labels))
        
        # Create a summary file
        summary_path = os.path.join(dataset_dir, 'summary.json')
        summary = {
            'total_samples': len(dataset),
            'unique_labels': len(unique_labels),
            'created_at': datetime.now().isoformat(),
            'labels': list(unique_labels),
            'dataset_path': dataset_dir
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Dataset processed: {len(dataset)} samples with {len(unique_labels)} unique labels")
        
        return jsonify({
            'success': True,
            'dataset_path': dataset_dir,
            'metadata_path': metadata_path,
            'total_samples': len(dataset),
            'unique_labels': len(unique_labels),
            'message': f'Dataset created with {len(dataset)} samples ({len(unique_labels)} unique labels)'
        })
        
    except Exception as e:
        logger.error(f"Dataset processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prepare-line-data', methods=['POST'])
def prepare_line_data():
    """Prepare uploaded images for line-level labeling."""
    if not ADVANCED_FEATURES:
        return jsonify({'error': 'Advanced features not available. Please install all dependencies.'}), 503
    
    try:
        data = request.get_json()
        if not data or 'input_dir' not in data:
            return jsonify({'error': 'No input directory specified'}), 400
        
        input_dir = data['input_dir']
        if not os.path.exists(input_dir):
            return jsonify({'error': 'Input directory does not exist'}), 400
        
        # Use the existing DataPreparator
        preparator = DataPreparator()
        metadata_path = preparator.create_labeling_dataset(input_dir)
        
        # Read the created metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"Line data prepared: {metadata['dataset_info']['total_lines']} lines")
        
        return jsonify({
            'success': True,
            'metadata_path': metadata_path,
            'total_lines': metadata['dataset_info']['total_lines'],
            'total_pages': metadata['dataset_info']['total_pages'],
            'message': f'Prepared {metadata["dataset_info"]["total_lines"]} lines for labeling'
        })
        
    except Exception as e:
        logger.error(f"Line data preparation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'handwriting-ocr-web',
        'version': '1.0.0'
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Run the Flask application."""
    port = int(os.environ.get('PORT', 8080))  # Changed default port to 8080
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting handwriting OCR web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
