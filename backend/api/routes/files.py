"""
File upload and processing routes
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging

# Add code_interpreter to path
code_interpreter_path = Path(__file__).parent.parent.parent.parent / "code_interpreter"
sys.path.insert(0, str(code_interpreter_path))

try:
    from services.file_utils import get_file_info
    from services.gemini_service import GeminiCodeExecutionService
except ImportError as e:
    logging.error(f"Error importing code_interpreter services: {e}")
    raise

router = APIRouter()

# Upload directory - relative to project root
# Path structure: backend/api/routes/files.py -> backend/api/routes -> backend/api -> backend -> project_root
project_root = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = project_root / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/process")
async def process_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Process uploaded file: extract metadata, detect document type, convert Excel to CSV
    """
    try:
        # Validate file type
        file_name = file.filename.lower()
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls') or file_name.endswith('.csv')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only .xlsx, .xls, and .csv files are allowed."
            )

        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Extract metadata - handle CSV and Excel differently
            import pandas as pd
            
            if suffix.lower() == '.csv':
                # Handle CSV files
                df = pd.read_csv(tmp_path, nrows=10, encoding='utf-8')
                df_full = pd.read_csv(tmp_path, encoding='utf-8')
                file_size = Path(tmp_path).stat().st_size
                
                # Detect total rows
                from services.file_utils import detect_total_rows
                total_row_indices = detect_total_rows(df_full)
                
                file_info = {
                    "filename": file.filename,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "columns": list(df.columns),
                    "num_columns": len(df.columns),
                    "num_rows": len(df_full),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "has_total_rows": len(total_row_indices) > 0,
                    "total_row_indices": total_row_indices,
                    "total_rows_count": len(total_row_indices),
                }
            else:
                # Handle Excel files using file_utils
                file_info = get_file_info(tmp_path)
                
                if "error" in file_info:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error processing file: {file_info.get('error', 'Unknown error')}"
                    )

            # Detect document type and convert Excel to CSV if needed
            detected_document_type = None
            csv_path = None
            
            try:
                gemini_service = GeminiCodeExecutionService()
                detected_document_type = gemini_service._detect_document_type(file_info)
                
                # Convert Excel to CSV if needed and save to uploads directory
                if suffix.lower() in ['.xlsx', '.xls']:
                    csv_path = gemini_service._convert_to_csv(tmp_path, file.filename)
                    # Move CSV to uploads directory
                    final_csv_path = UPLOAD_DIR / Path(csv_path).name
                    import shutil
                    if Path(csv_path).exists():
                        shutil.move(csv_path, final_csv_path)
                        csv_path = str(final_csv_path)
            except Exception as e:
                logging.warning(f"Could not detect document type or convert file: {e}")
                # Continue without document type detection and CSV conversion

            # Prepare response
            metadata = {
                "columns": file_info.get("columns", []),
                "numRows": file_info.get("num_rows", 0),
                "numColumns": file_info.get("num_columns", 0),
                "fileType": detected_document_type,
                "detectedDocumentType": detected_document_type,
                "hasTotalRows": file_info.get("has_total_rows", False),
                "totalRowsCount": file_info.get("total_rows_count", 0),
            }

            return {
                "metadata": metadata,
                "num_rows": file_info.get("num_rows", 0),
                "num_columns": file_info.get("num_columns", 0),
                "columns": file_info.get("columns", []),
                "file_type": detected_document_type,
                "detected_document_type": detected_document_type,
                "csv_path": csv_path,
            }
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception as e:
                logging.warning(f"Could not delete temporary file: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.delete("/{file_id}")
async def delete_file(file_id: str) -> Dict[str, Any]:
    """
    Delete a file by ID
    """
    try:
        file_path = UPLOAD_DIR / file_id
        
        # Also check for CSV version
        csv_path = UPLOAD_DIR / f"{Path(file_id).stem}.csv"
        
        deleted = False
        if file_path.exists():
            os.unlink(file_path)
            deleted = True
        
        if csv_path.exists():
            os.unlink(csv_path)
            deleted = True

        if not deleted:
            raise HTTPException(status_code=404, detail="File not found")

        return {"success": True, "message": "File deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )

@router.get("/list")
async def list_files() -> Dict[str, Any]:
    """
    List all uploaded files
    """
    try:
        files = []
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "id": file_path.name,
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                })
        
        return {"files": files}
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing files: {str(e)}"
        )

