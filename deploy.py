#!/usr/bin/env python3
"""
MRFI Standalone Deployment Script
Creates a standalone deployment that can run without VS Code
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_python():
    """Check if Python is installed"""
    try:
        import sys
        print(f"✅ Python {sys.version.split()[0]} found")
        return True
    except:
        print("❌ Python not found")
        return False

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'flask', 'sqlalchemy', 'flask-migrate', 'flask-cors',
        'numpy', 'scikit-learn', 'requests', 'bcrypt', 'pyjwt',
        'websockets'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ All dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=mrfi-production-secret-key-change-this-in-production
JWT_SECRET=mrfi-jwt-secret-key-change-this-in-production
DATABASE_URL=sqlite:///mrfi.db
WEBSOCKET_HOST=127.0.0.1
WEBSOCKET_PORT=8765
AUTO_INIT_DB=true
DEBUG=false
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    return True

def initialize_database():
    """Initialize the database with sample data"""
    try:
        print("🗄️ Initializing database...")
        from run import create_app
        
        app = create_app()
        with app.app_context():
            from models import db
            db.create_all()
            print("✅ Database initialized")
            
            # Check if sample data exists
            from models import User
            if User.query.count() == 0:
                print("📊 Creating sample data...")
                subprocess.check_call([sys.executable, 'generate_sample_data.py'])
                print("✅ Sample data created")
            else:
                print("✅ Sample data already exists")
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_startup_script():
    """Create a startup script for easy deployment"""
    startup_script = """@echo off
echo Starting MRFI - Metabolic Resonance Field Intelligence...
echo.
echo Please wait while the application starts...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Start the application
echo Starting MRFI application...
python run.py

pause
"""
    
    with open('start_mrfi.bat', 'w') as f:
        f.write(startup_script)
    
    # Also create a Linux/Mac version
    linux_script = """#!/bin/bash
echo "Starting MRFI - Metabolic Resonance Field Intelligence..."
echo
echo "Please wait while the application starts..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python first."
    exit 1
fi

# Start the application
echo "Starting MRFI application..."
python3 run.py
"""
    
    with open('start_mrfi.sh', 'w') as f:
        f.write(linux_script)
    
    # Make Linux script executable
    os.chmod('start_mrfi.sh', 0o755)
    
    print("✅ Startup scripts created:")
    print("   • start_mrfi.bat (Windows)")
    print("   • start_mrfi.sh (Linux/Mac)")

def get_local_ip():
    """Get the local IP address for network access"""
    import socket
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def deploy_standalone():
    """Deploy the application as standalone"""
    print("🚀 MRFI Standalone Deployment")
    print("=" * 50)
    
    # Check requirements
    if not check_python():
        return False
    
    if not check_dependencies():
        return False
    
    if not setup_environment():
        return False
    
    if not initialize_database():
        return False
    
    create_startup_script()
    
    # Get network information
    local_ip = get_local_ip()
    
    print("\n" + "=" * 50)
    print("✅ MRFI Deployment Complete!")
    print("=" * 50)
    
    print("\n📱 How to Run MRFI:")
    print("1. Double-click 'start_mrfi.bat' (Windows)")
    print("2. Or run: python run.py")
    print("3. Or run: python3 run.py (Linux/Mac)")
    
    print(f"\n🌐 Access MRFI:")
    print(f"• Local: http://localhost:5000")
    print(f"• Network: http://{local_ip}:5000")
    
    print(f"\n📱 Mobile Access:")
    print(f"• Connect to the same WiFi/network")
    print(f"• Open browser and go to: http://{local_ip}:5000")
    
    print("\n👤 Test Users:")
    print("• sarah.j@example.com / password123")
    print("• raj.p@example.com / password123")
    print("• maria.g@example.com / password123")
    print("• james.c@example.com / password123")
    print("• amanda.w@example.com / password123")
    
    print("\n🎯 Features:")
    print("• ✅ Mobile-responsive design")
    print("• ✅ Touch-friendly interface")
    print("• ✅ Real-time resonance field analysis")
    print("• ✅ Standalone deployment")
    print("• ✅ No VS Code required")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy_standalone()
        if success:
            # Ask user if they want to start the application
            try:
                choice = input("\n🚀 Start MRFI now? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    print("\n🌟 Starting MRFI...")
                    webbrowser.open('http://localhost:5000')
                    subprocess.run([sys.executable, 'run.py'])
            except KeyboardInterrupt:
                print("\n👋 Deployment complete. Run 'start_mrfi.bat' to start later.")
        else:
            print("\n❌ Deployment failed. Please check the errors above.")
    except KeyboardInterrupt:
        print("\n👋 Deployment cancelled.")
