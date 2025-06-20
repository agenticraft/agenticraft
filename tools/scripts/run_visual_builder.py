#!/usr/bin/env python3
"""Run the AgentiCraft Visual Workflow Builder."""

import uvicorn
import webbrowser
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agenticraft.tools.builder.api import app

def main():
    """Run the visual builder server."""
    print("🎨 Starting AgentiCraft Visual Builder...")
    print("=" * 50)
    print("Server running at: http://localhost:8000")
    print("Visual Builder UI: http://localhost:8000/static/index.html")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    # Try to open browser automatically
    try:
        webbrowser.open("http://localhost:8000/static/index.html")
    except:
        pass
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
