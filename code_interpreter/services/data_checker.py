"""
Service for checking data availability against requirements
"""
import logging
from typing import Dict, List, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DataChecker:
    """
    Checks if data requirements can be fulfilled by uploaded files
    """
    
    def __init__(self):
        pass
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_matching_columns(self, required_columns: List[str], file_columns: List[str], threshold: float = 0.6) -> Dict[str, Any]:
        """
        Find matching columns using fuzzy matching
        
        Args:
            required_columns: List of required column names
            file_columns: List of available column names
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            Dict with matched columns and scores
        """
        matches = {}
        unmatched_required = []
        
        for req_col in required_columns:
            best_match = None
            best_score = 0
            
            for file_col in file_columns:
                score = self.similarity(req_col, file_col)
                # Also check if required column name is contained in file column
                if req_col.lower() in file_col.lower():
                    score = max(score, 0.8)
                
                if score > best_score:
                    best_score = score
                    best_match = file_col
            
            if best_score >= threshold:
                matches[req_col] = {
                    "matched_column": best_match,
                    "score": best_score
                }
            else:
                unmatched_required.append(req_col)
        
        return {
            "matched": matches,
            "unmatched": unmatched_required,
            "match_rate": len(matches) / len(required_columns) if required_columns else 0
        }
    
    def check_requirement_availability(self, requirement: Dict[str, Any], files: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a single requirement can be fulfilled by available files
        
        Args:
            requirement: Requirement dict with requirement_id, data_type, columns_needed, etc.
            files: Dict of uploaded files {file_id: {file, name, info}}
            
        Returns:
            Availability status dict
        """
        req_id = requirement.get("requirement_id", "unknown")
        data_type = requirement.get("data_type", "").lower()
        columns_needed = requirement.get("columns_needed", [])
        
        # Also get description and where_found for better reporting
        description = requirement.get("description", "")
        where_found = requirement.get("where_found", "")
        
        # Check each file
        matches = []
        best_match = None
        best_score = 0
        
        for file_id, file_data in files.items():
            file_info = file_data.get("info", {})
            if "error" in file_info:
                continue
            
            file_columns = file_info.get("columns", [])
            
            # Check data type match (fuzzy match on document type)
            # This would need document type detection from file_utils
            # For now, check column matches
            
            # Find matching columns
            column_match = self.find_matching_columns(columns_needed, file_columns)
            
            match_score = column_match["match_rate"]
            
            if match_score > best_score:
                best_score = match_score
                best_match = {
                    "file_id": file_id,
                    "file_name": file_data.get("name", "unknown"),
                    "match_score": match_score,
                    "matched_columns": column_match["matched"],
                    "unmatched_columns": column_match["unmatched"]
                }
            
            matches.append({
                "file_id": file_id,
                "file_name": file_data.get("name", "unknown"),
                "match_score": match_score,
                "matched_columns": column_match["matched"],
                "unmatched_columns": column_match["unmatched"]
            })
        
        # Determine availability status
        if best_match and best_score >= 0.8:
            availability = "available"
        elif best_match and best_score >= 0.5:
            availability = "partial"
        else:
            availability = "missing"
        
        return {
            "requirement_id": req_id,
            "data_type": data_type,
            "description": description,
            "where_found": where_found,
            "columns_needed": columns_needed,
            "availability": availability,
            "match_score": best_score,
            "best_match": best_match,
            "all_matches": matches,
            "critical": requirement.get("critical", False)
        }
    
    def check_data_availability(self, requirements: List[Dict[str, Any]], files: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check availability of all requirements against uploaded files
        
        Args:
            requirements: List of requirement dicts
            files: Dict of uploaded files
            
        Returns:
            Availability summary dict
        """
        if not requirements:
            return {
                "available": [],
                "missing": [],
                "partial": [],
                "can_analyze": False,
                "analysis_type": "advisory_only"
            }
        
        if not files:
            # Convert requirements to missing availability results
            missing_results = []
            for req in requirements:
                missing_results.append({
                    "requirement_id": req.get("requirement_id", "unknown"),
                    "data_type": req.get("data_type", ""),
                    "description": req.get("description", ""),
                    "where_found": req.get("where_found", ""),
                    "columns_needed": req.get("columns_needed", []),
                    "availability": "missing",
                    "match_score": 0,
                    "best_match": None,
                    "all_matches": [],
                    "critical": req.get("critical", False)
                })
            
            return {
                "available": [],
                "missing": missing_results,
                "partial": [],
                "can_analyze": False,
                "analysis_type": "advisory_only"
            }
        
        available = []
        partial = []
        missing = []
        
        for req in requirements:
            availability_result = self.check_requirement_availability(req, files)
            
            if availability_result["availability"] == "available":
                available.append(availability_result)
            elif availability_result["availability"] == "partial":
                partial.append(availability_result)
            else:
                missing.append(availability_result)
        
        # Determine if we can do analysis
        critical_missing = [r for r in missing if r.get("critical", False)]
        
        if not critical_missing and len(available) > 0:
            can_analyze = True
            analysis_type = "full"
        elif not critical_missing and len(partial) > 0:
            can_analyze = True
            analysis_type = "partial"
        elif len(available) + len(partial) > 0:
            can_analyze = True
            analysis_type = "partial"
        else:
            can_analyze = False
            analysis_type = "advisory_only"
        
        return {
            "available": available,
            "missing": missing,
            "partial": partial,
            "can_analyze": can_analyze,
            "analysis_type": analysis_type,
            "critical_missing": critical_missing
        }
    
    def check_step_requirements(
        self, 
        step_name: str, 
        requirements: List[Dict[str, Any]], 
        files: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check availability of requirements for a specific analysis step
        
        Args:
            step_name: Name of the analysis step (current_context, impacts, scenarios, recommendations)
            requirements: List of all requirement dicts
            files: Dict of uploaded files
            
        Returns:
            Dict with available/partial/missing requirements for this step
        """
        # Map step names to required data types
        step_requirements_map = {
            "current_context": ["cash_flow", "balance_sheet", "income_statement"],
            "impacts": ["cash_flow", "payroll", "expenses"],
            "scenarios": ["cash_flow", "revenue", "expenses"],
            "recommendations": []  # Can proceed with any available data
        }
        
        needed_types = step_requirements_map.get(step_name, [])
        
        # If recommendations step, return all available (can proceed with anything)
        if step_name == "recommendations":
            return {
                "available": self.check_data_availability(requirements, files).get("available", []),
                "partial": self.check_data_availability(requirements, files).get("partial", []),
                "missing": [],
                "can_proceed": True
            }
        
        # Filter requirements needed for this step
        needed_reqs = [
            req for req in requirements 
            if req.get("data_type", "").lower() in needed_types
        ]
        
        if not needed_reqs:
            # No specific requirements for this step, can proceed
            return {
                "available": [],
                "partial": [],
                "missing": [],
                "can_proceed": True
            }
        
        # Check availability of needed requirements
        step_availability = self.check_data_availability(needed_reqs, files)
        
        available = step_availability.get("available", [])
        partial = step_availability.get("partial", [])
        missing = step_availability.get("missing", [])
        
        # Can proceed if we have at least some available data or if no critical missing
        critical_missing = [r for r in missing if r.get("critical", False)]
        can_proceed = len(available) > 0 or (len(partial) > 0 and len(critical_missing) == 0)
        
        return {
            "available": available,
            "partial": partial,
            "missing": missing,
            "can_proceed": can_proceed,
            "critical_missing": critical_missing
        }
    
    def aggregate_file_metadata(self, files: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine metadata from all uploaded files
        
        Args:
            files: Dict of uploaded files
            
        Returns:
            Aggregated metadata dict
        """
        all_columns = []
        all_dtypes = {}
        total_rows = 0
        file_count = 0
        
        for file_id, file_data in files.items():
            file_info = file_data.get("info", {})
            if "error" in file_info:
                continue
            
            file_count += 1
            all_columns.extend(file_info.get("columns", []))
            all_dtypes.update(file_info.get("dtypes", {}))
            total_rows += file_info.get("num_rows", 0)
        
        return {
            "file_count": file_count,
            "total_columns": len(set(all_columns)),
            "all_columns": list(set(all_columns)),
            "all_dtypes": all_dtypes,
            "total_rows": total_rows
        }

