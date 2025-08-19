#!/usr/bin/env python3
"""
Setup script for Vercel deployment and database initialization.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if pip is available
    if run_command("pip --version", "Checking pip"):
        print("✅ pip is available")
    else:
        print("❌ pip is not available")
        return False
    
    # Check if git is available
    if run_command("git --version", "Checking git"):
        print("✅ git is available")
    else:
        print("❌ git is not available")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install Prisma CLI
    if not run_command("pip install prisma", "Installing Prisma"):
        return False
    
    return True

def setup_database():
    """Set up the database schema."""
    print("🗄️ Setting up database...")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL before running this script")
        return False
    
    # Generate Prisma client
    if not run_command("prisma generate", "Generating Prisma client"):
        return False
    
    # Push database schema
    if not run_command("prisma db push", "Pushing database schema"):
        return False
    
    print("✅ Database setup completed")
    return True

def create_env_file():
    """Create .env file template."""
    env_template = """# Database Configuration
DATABASE_URL="postgresql://username:password@host:port/database"

# Gemini API (for Enhanced Journaling Engine)
GEMINI_API_KEY="your_gemini_api_key_here"

# Flask Configuration
FLASK_ENV="production"
SECRET_KEY="your-secret-key-here"

# Optional: Vercel Configuration
VERCEL_PROJECT_ID="your_vercel_project_id"
VERCEL_ORG_ID="your_vercel_org_id"
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("⚠️  Please update .env with your actual values")
    else:
        print("✅ .env file already exists")

def setup_vercel():
    """Set up Vercel deployment."""
    print("🚀 Setting up Vercel deployment...")
    
    # Check if Vercel CLI is installed
    if not run_command("vercel --version", "Checking Vercel CLI"):
        print("📥 Installing Vercel CLI...")
        if not run_command("npm install -g vercel", "Installing Vercel CLI"):
            print("❌ Failed to install Vercel CLI")
            print("Please install manually: npm install -g vercel")
            return False
    
    # Create vercel.json if it doesn't exist
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "src/web_app/app_enhanced.py",
                "use": "@vercel/python"
            }
        ],
        "routes": [
            {
                "src": "/(.*)",
                "dest": "src/web_app/app_enhanced.py"
            }
        ],
        "env": {
            "FLASK_ENV": "production"
        }
    }
    
    vercel_file = Path('vercel.json')
    if not vercel_file.exists():
        with open(vercel_file, 'w') as f:
            json.dump(vercel_config, f, indent=2)
        print("✅ Created vercel.json configuration")
    
    return True

def create_deployment_script():
    """Create deployment helper script."""
    deploy_script = """#!/bin/bash
# Deployment helper script

echo "🚀 Starting deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Load environment variables
source .env

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env"
    exit 1
fi

# Generate Prisma client
echo "🔄 Generating Prisma client..."
prisma generate

# Push database schema
echo "🔄 Pushing database schema..."
prisma db push

# Deploy to Vercel
echo "🔄 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment completed!"
echo "🌐 Your app should be available at: https://your-app.vercel.app"
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(deploy_script)
    
    # Make executable
    os.chmod('deploy.sh', 0o755)
    print("✅ Created deploy.sh script")

def main():
    """Main setup function."""
    print("🎯 Enhanced Journaling Engine - Deployment Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Setup Vercel
    if not setup_vercel():
        print("❌ Vercel setup failed")
        sys.exit(1)
    
    # Create deployment script
    create_deployment_script()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your actual values")
    print("2. Set up your PostgreSQL database")
    print("3. Run: ./deploy.sh")
    print("\n📚 For detailed instructions, see DEPLOYMENT.md")
    
    # Ask if user wants to set up database now
    if os.getenv('DATABASE_URL'):
        response = input("\n🤔 Do you want to set up the database now? (y/n): ")
        if response.lower() == 'y':
            if setup_database():
                print("✅ Database setup completed!")
            else:
                print("❌ Database setup failed")

if __name__ == "__main__":
    main()
