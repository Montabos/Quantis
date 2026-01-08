"""
Utilities for extracting metadata from Excel files
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import io
import re


def detect_total_rows(df: pd.DataFrame) -> List[int]:
    """
    Detects rows that appear to be total rows
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of row indices detected as totals
    """
    total_keywords = [
        'total', 'totals', 'subtotal', 'sub-total',
        'grand total', 'sum', 'grand total',
        'total general', 'total general'
    ]
    
    total_row_indices = []
    
    # Convert all columns to string for search
    df_str = df.astype(str)
    
    for idx, row in df_str.iterrows():
        # Check if any cell in the row contains a total keyword
        row_str = ' '.join(row.values).lower()
        
        # Check keywords
        for keyword in total_keywords:
            if keyword in row_str:
                total_row_indices.append(idx)
                break
        
        # Also check if all numeric values are very high (suspicious)
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            row_numeric = df.loc[idx, numeric_cols]
            if len(row_numeric) > 0 and row_numeric.notna().any():
                # If all numeric values are positive and very high
                if (row_numeric > 10000).sum() == len(row_numeric.dropna()):
                    # Check if it's really suspicious (not just normal large values)
                    if idx not in total_row_indices:
                        # Check if it's the last row (often a total)
                        if idx == len(df) - 1 or idx == len(df) - 2:
                            total_row_indices.append(idx)
    
    return sorted(list(set(total_row_indices)))


def get_file_info(file) -> Dict[str, Any]:
    """
    Extracts metadata from an uploaded Excel file
    
    Args:
        file: Uploaded file (Streamlit UploadedFile or path)
        
    Returns:
        Dict containing file metadata
    """
    try:
        # If it's a file object (Streamlit), read from bytes
        if hasattr(file, 'read'):
            file.seek(0)
            df = pd.read_excel(file, nrows=10, engine='openpyxl')
            file.seek(0)  # Reset for reuse
            file_size = len(file.getvalue()) if hasattr(file, 'getvalue') else None
        else:
            # If it's a file path
            df = pd.read_excel(file, nrows=10, engine='openpyxl')
            file_size = Path(file).stat().st_size if Path(file).exists() else None
        
        # Count total number of rows
        # Note: For Excel files, we must load the complete file
        # (read_excel doesn't support chunksize like read_csv)
        if hasattr(file, 'read'):
            file.seek(0)
            df_full = pd.read_excel(file, engine='openpyxl')
            total_rows = len(df_full)
            file.seek(0)
        else:
            df_full = pd.read_excel(file, engine='openpyxl')
            total_rows = len(df_full)
        
        # Detect total rows
        total_row_indices = detect_total_rows(df_full)
        has_totals = len(total_row_indices) > 0
        
        return {
            "filename": getattr(file, 'name', str(file)),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size else None,
            "columns": list(df.columns),
            "num_columns": len(df.columns),
            "num_rows": total_rows,
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample_data": df.head(5).to_dict(orient='records'),
            "has_total_rows": has_totals,
            "total_row_indices": total_row_indices,
            "total_rows_count": len(total_row_indices),
            "column_info": [
                {
                    "name": col,
                    "type": str(dtype),
                    "non_null_count": df[col].notna().sum(),
                    "null_count": df[col].isna().sum(),
                    "sample_values": df[col].dropna().head(3).tolist()
                }
                for col, dtype in df.dtypes.items()
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


def aggregate_file_metadata(files: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate metadata from multiple files
    
    Args:
        files: Dict of files {file_id: {file, name, info, ...}}
        
    Returns:
        Aggregated metadata dict
    """
    all_columns = []
    all_dtypes = {}
    total_rows = 0
    file_count = 0
    file_names = []
    
    for file_id, file_data in files.items():
        file_info = file_data.get("info", {})
        if "error" in file_info:
            continue
        
        file_count += 1
        file_names.append(file_data.get("name", "unknown"))
        all_columns.extend(file_info.get("columns", []))
        all_dtypes.update(file_info.get("dtypes", {}))
        total_rows += file_info.get("num_rows", 0)
    
    return {
        "file_count": file_count,
        "file_names": file_names,
        "total_columns": len(set(all_columns)),
        "all_columns": list(set(all_columns)),
        "all_dtypes": all_dtypes,
        "total_rows": total_rows
    }

