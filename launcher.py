#!/usr/bin/env python3
"""
ResumePard Application Launcher
Simple Python script to start the Streamlit web application
"""

import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import plotly
        import pandas
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def start_streamlit():
    """Start the Streamlit application."""
    print("🚀 Starting ResumePard Web Application...")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ app.py not found! Please run this script from the ResumePard directory.")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependencies missing. Please install them first:")
        print("pip install streamlit plotly pandas")
        return False
    
    print("✅ Dependencies found")
    print("🌐 Starting Streamlit server...")
    print("📱 Application will open in your browser at: http://localhost:8501")
    print()
    print("🛑 To stop the application, press Ctrl+C")
    print("-" * 60)
    
    try:
        # Start Streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        return True
    
    return True

if __name__ == "__main__":
    try:
        success = start_streamlit()
        if not success:
            print("\n❌ Failed to start the application")
            print("Please try running manually:")
            print("streamlit run app.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    input("\nPress Enter to exit...")
