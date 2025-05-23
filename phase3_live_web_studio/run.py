#!/usr/bin/env python3
"""
Launch script for WebWeaver - Live Web Development Studio
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['streamlit', 'watchdog']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ All packages installed!")

def main():
    print("🕸️ WebWeaver")
    print("Build websites in minutes with AI-powered agents")
    print("-" * 50)
    
    # Check and install dependencies
    check_dependencies()
    
    # Run the Streamlit app
    print("🚀 Starting WebWeaver...")
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])

if __name__ == "__main__":
    main() 