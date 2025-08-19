#!/usr/bin/env python3
"""
Quick start script for the handwriting OCR web interface.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    """Start the web interface and open it in the browser."""
    print("🚀 Starting Handwriting OCR Web Interface...")
    
    # Check if we're in the right directory
    if not Path("src/web_app/app.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   (where the README.md file is located)")
        sys.exit(1)
    
    # Check if key dependencies are installed
    missing_deps = []
    
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        missing_deps.append("flask")
    
    try:
        import cv2
        print("✅ OpenCV is installed")
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        from PIL import Image
        print("✅ Pillow is installed")
    except ImportError:
        missing_deps.append("pillow")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("📦 Installing missing dependencies...")
        for dep in missing_deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep])
        print("✅ Dependencies installed")
    
    # Create necessary directories
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    print("✅ Directories created")
    print("🌐 Starting web server...")
    print("📱 The interface will open automatically in your browser")
    print("🔗 Or visit: http://localhost:8080")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    # Start the Flask app
    try:
        # Change to the web_app directory
        os.chdir("src/web_app")
        
        # Start the Flask application
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
