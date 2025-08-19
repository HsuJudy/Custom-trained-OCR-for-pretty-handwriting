#!/usr/bin/env python3
"""
Enhanced Flask web application for the handwriting OCR system.
Integrates with database for project management and analytics.
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import zipfile
import io
import base64
from PIL import Image
import cv2
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import database service
from src.database.database import db_service

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

def run_async(coro):
    """Helper to run async functions in Flask."""
    return asyncio.run(coro)

@app.route('/')
def index():
    """Serve the main handwriting data collector interface."""
    return send_from_directory('.', 'index.html')

@app.route('/dashboard')
def dashboard():
    """Serve the project dashboard."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects for a user."""
    try:
        # For now, use a default user ID - in production, get from session/auth
        user_id = request.args.get('user_id', 'default_user')
        
        projects = run_async(db_service.get_user_projects(user_id))
        
        # Convert to serializable format
        projects_data = []
        for project in projects:
            projects_data.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status.value,
                'created_at': project.createdAt.isoformat(),
                'updated_at': project.updatedAt.isoformat(),
                'image_count': len(project.images),
                'entry_count': len(project.entries)
            })
        
        return jsonify({
            'success': True,
            'projects': projects_data
        })
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        user_id = data.get('user_id', 'default_user')
        
        if not name:
            return jsonify({'error': 'Project name is required'}), 400
        
        project = run_async(db_service.create_project(user_id, name, description))
        
        if project:
            return jsonify({
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'created_at': project.createdAt.isoformat()
                }
            })
        else:
            return jsonify({'error': 'Failed to create project'}), 500
            
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/analytics')
def get_project_analytics(project_id):
    """Get analytics for a project."""
    try:
        analytics = run_async(db_service.get_project_analytics(project_id))
        
        if analytics:
            return jsonify({
                'success': True,
                'analytics': analytics
            })
        else:
            return jsonify({'error': 'Project not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting project analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/export')
def export_project_data(project_id):
    """Export project data for OCR training."""
    try:
        export_data = run_async(db_service.export_project_data(project_id))
        
        if export_data:
            # Create a ZIP file with the exported data
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                # Add JSON export
                zf.writestr('export_data.json', json.dumps(export_data, indent=2))
                
                # Add CSV files
                if export_data.get('labels'):
                    csv_content = 'id,text,x,y,width,height,confidence,image_id\n'
                    for label in export_data['labels']:
                        csv_content += f"{label['id']},{label['text']},{label['x']},{label['y']},{label['width']},{label['height']},{label['confidence']},{label['image_id']}\n"
                    zf.writestr('labels.csv', csv_content)
                
                if export_data.get('entries'):
                    csv_content = 'id,entry_id,text_content,date,color_code,sentiment,image_id\n'
                    for entry in export_data['entries']:
                        csv_content += f"{entry['id']},{entry['entry_id']},{entry['text_content']},{entry['date']},{entry['color_code']},{entry['sentiment']},{entry['image_id']}\n"
                    zf.writestr('entries.csv', csv_content)
            
            memory_file.seek(0)
            
            return send_from_directory(
                io.BytesIO(memory_file.getvalue()),
                'project_export.zip',
                as_attachment=True,
                mimetype='application/zip'
            )
        else:
            return jsonify({'error': 'Project not found'}), 404
            
    except Exception as e:
        logger.error(f"Error exporting project data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        project_id = request.form.get('project_id')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Get image dimensions
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
            except:
                width, height = None, None
            
            # Create image record in database
            if project_id:
                image = run_async(db_service.create_image(
                    project_id=project_id,
                    filename=filename,
                    original_name=file.filename,
                    file_size=os.path.getsize(filepath),
                    mime_type=file.content_type,
                    width=width,
                    height=height
                ))
                
                if image:
                    logger.info(f"File uploaded and recorded: {filename}")
                    return jsonify({
                        'success': True,
                        'filename': filename,
                        'image_id': image.id,
                        'message': 'File uploaded successfully'
                    })
            
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
        project_id = data.get('project_id')
        user_id = data.get('user_id', 'default_user')
        
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
                'version': '2.0'
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
                
                # Save to database if project_id is provided
                if project_id and 'image_id' in item:
                    run_async(db_service.create_label(
                        image_id=item['image_id'],
                        user_id=user_id,
                        text=item['label'],
                        x=item.get('x', 0),
                        y=item.get('y', 0),
                        width=item.get('width', 0),
                        height=item.get('height', 0)
                    ))
                
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

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'handwriting-ocr-web-enhanced',
        'version': '2.0.0',
        'database': 'connected' if db_service.db else 'disconnected'
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
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting enhanced handwriting OCR web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
