#!/usr/bin/env python3
"""
Simplified Flask app for Vercel deployment.
Optimized for serverless function size limits.
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import base64
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Use /tmp for Vercel
app.config['PROCESSED_FOLDER'] = '/tmp/processed'

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

@app.route('/dashboard')
def dashboard():
    """Serve the project dashboard."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'handwriting-ocr-web-vercel',
        'version': '2.0.0',
        'deployment': 'vercel'
    })

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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dataset_dir = os.path.join(app.config['PROCESSED_FOLDER'], f'temp_dataset_{timestamp}')
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Save cropped images and create metadata
        metadata = {
            'dataset_info': {
                'total_samples': len(dataset),
                'created_at': datetime.now().isoformat(),
                'source': 'web_interface',
                'version': '2.0',
                'deployment': 'vercel'
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
            'dataset_path': dataset_dir,
            'deployment': 'vercel'
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

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects for a user (simplified for Vercel)."""
    try:
        # Return mock data for now - in production, connect to database
        projects_data = [
            {
                'id': 'demo-project-1',
                'name': 'Demo Project',
                'description': 'Sample project for demonstration',
                'status': 'ACTIVE',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'image_count': 0,
                'entry_count': 0
            }
        ]
        
        return jsonify({
            'success': True,
            'projects': projects_data
        })
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project (simplified for Vercel)."""
    try:
        data = request.get_json()
        name = data.get('name', 'New Project')
        description = data.get('description', '')
        
        # Create mock project
        project = {
            'id': f'project-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'project': project
        })
            
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({'error': str(e)}), 500

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
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting handwriting OCR web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
