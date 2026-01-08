"""
Dashboard data routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import sys
from pathlib import Path
import logging

# Add code_interpreter to path
code_interpreter_path = Path(__file__).parent.parent.parent.parent / "code_interpreter"
sys.path.insert(0, str(code_interpreter_path))

router = APIRouter()

# Upload directory - relative to project root
project_root = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = project_root / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@router.get("/data")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get dashboard data from available files
    """
    try:
        # List all CSV files
        csv_files = list(UPLOAD_DIR.glob("*.csv"))
        
        if not csv_files:
            return {
                "hasFiles": False,
                "filesCount": 0,
                "data": {},
                "message": "No files available"
            }

        # TODO: Use Gemini to analyze files and generate dashboard insights
        # For now, return basic info
        return {
            "hasFiles": True,
            "filesCount": len(csv_files),
            "files": [f.name for f in csv_files],
            "data": {
                "message": "Files available - dashboard analysis coming soon"
            }
        }

    except Exception as e:
        logging.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dashboard data: {str(e)}"
        )

