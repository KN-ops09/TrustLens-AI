#!/usr/bin/env python
"""
Simple script to run the FastAPI server
"""
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", "--port", "8000"
    ])
