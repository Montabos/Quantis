"""
Decision analysis service for financial decision questions
"""
import logging
import json
import re
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from services.gemini_service import GeminiCodeExecutionService
from services.data_checker import DataChecker
from templates.decision_prompts import (
    FILE_CONTENT_ANALYSIS_PROMPT,
    QUESTION_ANALYSIS_PROMPT,
    CURRENT_CONTEXT_PROMPT,
    IMPACT_CALCULATION_PROMPT,
    SCENARIO_PROJECTION_PROMPT,
    RECOMMENDATIONS_PROMPT,
    ADVISORY_ONLY_PROMPT,
    COMPREHENSIVE_ANALYSIS_PROMPT,
    STRUCTURE_DEFINITION_PROMPT,
    STRUCTURE_ADAPTATION_PROMPT,
    FINAL_REPORT_GENERATION_PROMPT,
    COMBINED_STRUCTURE_PROMPT
)

logger = logging.getLogger(__name__)


class DecisionAnalyzer:
    """
    Analyzes financial decisions using Gemini Code Execution
    """
    
    def __init__(self, gemini_service: GeminiCodeExecutionService):
        self.gemini_service = gemini_service
        self.data_checker = DataChecker()
    
    async def analyze_question_structure(self, question: str) -> Dict[str, Any]:
        """
        Step 1: Analyze question to define expected analysis structure
        
        Args:
            question: User's decision question
            
        Returns:
            Dict with decision summary and expected structure template
        """
        logger.info(f"Analyzing question structure: {question[:100]}...")
        
        prompt = STRUCTURE_DEFINITION_PROMPT.format(question=question)
        
        try:
            # Call Gemini without Code Execution (just text analysis)
            response = self.gemini_service.model.generate_content(prompt)
            
            # Extract JSON from response
            text_content = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content += part.text
            
            # Try to extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_content, re.DOTALL)
            if json_match:
                structure = json.loads(json_match.group(1))
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
                if json_match:
                    try:
                        structure = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        json_str = json_match.group()
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        structure = json.loads(json_str)
                else:
                    # Fallback: create basic structure
                    logger.warning("Could not parse JSON from structure response, using fallback")
                    structure = {
                        "decision_summary": {
                            "question": question,
                            "description": text_content[:200] + "...",
                            "importance": "Analysis needed",
                            "decision_type": "other"
                        },
                        "expected_structure": {
                            "sections": [],
                            "charts_required": [],
                            "data_needs": []
                        }
                    }
            
            logger.info(f"Defined structure with {len(structure.get('expected_structure', {}).get('sections', []))} sections")
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing question structure: {e}")
            # Return basic structure if parsing fails
            return {
                "decision_summary": {
                    "question": question,
                    "description": "Unable to parse structure",
                    "importance": "Unknown",
                    "decision_type": "other"
                },
                "expected_structure": {
                    "sections": [],
                    "charts_required": [],
                    "data_needs": []
                }
            }
    
    async def analyze_question_requirements(self, question: str) -> Dict[str, Any]:
        """
        Step 1: Understand question and identify data needs
        
        Args:
            question: User's decision question
            
        Returns:
            Dict with decision summary and data requirements
        """
        logger.info(f"Analyzing question requirements: {question[:100]}...")
        
        prompt = QUESTION_ANALYSIS_PROMPT.format(question=question)
        
        try:
            # Call Gemini without files (just text analysis)
            response = self.gemini_service.model.generate_content(prompt)
            
            # Extract JSON from response
            text_content = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content += part.text
            
            # Try to extract JSON from response
            # Look for JSON block (may be wrapped in markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_content, re.DOTALL)
            if json_match:
                requirements = json.loads(json_match.group(1))
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
                if json_match:
                    try:
                        requirements = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        json_str = json_match.group()
                        # Remove trailing commas
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        requirements = json.loads(json_str)
                else:
                    # Fallback: try to parse the whole text as JSON
                    try:
                        requirements = json.loads(text_content)
                    except json.JSONDecodeError:
                        # Last resort: create basic structure
                        logger.warning("Could not parse JSON from response, using fallback structure")
                        requirements = {
                            "decision_summary": {
                                "question": question,
                                "description": text_content[:200] + "...",
                                "importance": "Analysis needed"
                            },
                            "data_requirements": [],
                            "analysis_steps": []
                        }
            
            logger.info(f"Extracted {len(requirements.get('data_requirements', []))} data requirements")
            return requirements
            
        except Exception as e:
            logger.error(f"Error analyzing question requirements: {e}")
            # Return basic structure if parsing fails
            return {
                "decision_summary": {
                    "question": question,
                    "description": "Unable to parse requirements",
                    "importance": "Unknown"
                },
                "data_requirements": [],
                "analysis_steps": []
            }
    
    async def analyze_question_and_adapt_structure(
        self,
        question: str,
        files: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combined Step 1+2: Analyze question AND adapt structure to available data in one pass
        Uses Gemini normal (no Code Execution) - optimized for speed
        
        Args:
            question: User's decision question
            files: Dict of uploaded files (already converted to CSV)
            
        Returns:
            Dict with decision summary, final adapted structure, and file analysis
        """
        logger.info(f"Combined analysis: question + structure adaptation for: {question[:100]}...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        has_files = len(file_list) > 0
        
        # Build prompt with or without file analysis instructions
        if has_files:
            # Extract file metadata to help Gemini understand faster
            file_metadata = {}
            for file_id, file_data in files.items():
                file_info = file_data.get("info", {})
                file_metadata[file_data.get("name", "unknown")] = {
                    "columns": file_info.get("columns", []),
                    "dtypes": list(file_info.get("dtypes", {}).values()) if file_info.get("dtypes") else [],
                    "num_rows": file_info.get("num_rows", 0),
                    "has_total_rows": file_info.get("has_total_rows", False)
                }
            metadata_json = json.dumps(file_metadata, indent=2, ensure_ascii=False)
            
            file_analysis_instructions = """
            Read and analyze ALL uploaded CSV files to understand what data is actually available:
            - What columns are present?
            - What data types (dates, amounts, categories)?
            - What time periods are covered?
            - What financial metrics can be extracted?
            - What patterns or trends are visible?
            
            Use the file metadata provided below to understand structure quickly, but also read the actual files to confirm and get more details.
            """
            file_metadata_section = f"""
            
            FILE METADATA (already extracted to help you understand faster):
            {metadata_json}
            
            Use this metadata to understand the file structure quickly, but also read the actual files to confirm and get more details.
            """
            data_availability_analysis = """
            For each section and metric, determine:
            - Can we do it with available data? → Mark as "available"
            - Can we estimate it intelligently based on available data? → Mark as "estimated" with assumptions
            - Is it missing but critical? → Mark as "needs_data" (but only if truly critical)
            - Is it missing but not critical? → Mark as "simplified"
            
            For MVP context: Be flexible and creative. If data is missing but you can make reasonable estimates based on:
            - Available data patterns
            - Industry standards
            - Question parameters
            Then mark as "estimated" rather than "needs_data"
            """
        else:
            file_analysis_instructions = """
            No files uploaded - design structure based on question only.
            Mark sections as "estimated" or "needs_data" appropriately.
            Be creative and design a structure that would be valuable even without data.
            """
            file_metadata_section = ""
            data_availability_analysis = """
            Since no files are available, mark all sections as "estimated" or "needs_data".
            Focus on designing a structure that would be valuable for this decision type.
            """
        
        prompt = COMBINED_STRUCTURE_PROMPT.format(
            question=question,
            file_analysis_instructions=file_analysis_instructions,
            file_metadata_section=file_metadata_section,
            data_availability_analysis=data_availability_analysis
        )
        
        try:
            if has_files:
                # Use analyze_files_structure which reads files
                response = await self.gemini_service.analyze_files_structure(
                    prompt=prompt,
                    files=file_list
                )
                text_content = response.get("analysis_text", "")
            else:
                # Just text analysis, no files
                response = self.gemini_service.model_normal.generate_content(prompt)
                text_content = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text
            
            # Extract JSON from response
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Try to find JSON object directly
                json_match = re.search(r'(\{.*\})', text_content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        json_str = json_match.group(1)
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        try:
                            result = json.loads(json_str)
                        except json.JSONDecodeError:
                            logger.warning("Could not parse JSON, using fallback")
                            result = self._create_fallback_combined_structure(question, has_files)
                else:
                    logger.warning("No JSON found in response, using fallback")
                    result = self._create_fallback_combined_structure(question, has_files)
            
            logger.info(f"Combined analysis completed: {len(result.get('final_structure', {}).get('sections', []))} sections")
            return result
            
        except Exception as e:
            logger.error(f"Error in combined analysis: {e}")
            return self._create_fallback_combined_structure(question, has_files)
    
    def _create_fallback_combined_structure(self, question: str, has_files: bool) -> Dict[str, Any]:
        """Create fallback structure when JSON parsing fails"""
        return {
            "decision_summary": {
                "question": question,
                "description": "Unable to parse structure",
                "importance": "Analysis needed",
                "decision_type": "other"
            },
            "final_structure": {
                "sections": [
                    {
                        "section_name": "Key Metrics",
                        "status": "estimated",
                        "required": True,
                        "description": "Key financial metrics",
                        "metrics": []
                    },
                    {
                        "section_name": "Critical Factors",
                        "status": "estimated",
                        "required": True,
                        "description": "Critical factors to consider"
                    },
                    {
                        "section_name": "Current Financial Context",
                        "status": "estimated" if has_files else "needs_data",
                        "required": True,
                        "description": "Current financial situation"
                    },
                    {
                        "section_name": "Scenarios",
                        "status": "estimated",
                        "required": False,
                        "description": "Financial projections"
                    },
                    {
                        "section_name": "Recommendations",
                        "status": "estimated",
                        "required": True,
                        "description": "Actionable recommendations"
                    }
                ],
                "charts": [],
                "missing_data_requests": [],
                "estimation_notes": ["Using fallback structure"]
            },
            "file_analysis": {
                "files_analyzed": [],
                "available_data_types": [],
                "columns_found": {},
                "time_periods": {},
                "data_quality": "none" if not has_files else "unknown",
                "possible_analyses": []
            }
        }
    
    async def adapt_structure_to_data(
        self,
        expected_structure: Dict[str, Any],
        files: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 2: Adapt expected structure based on available data
        Uses Gemini normal (no Code Execution needed) - optimized for speed
        
        Args:
            expected_structure: Structure from analyze_question_structure
            files: Dict of uploaded files (already converted to CSV)
            
        Returns:
            Adapted structure with status for each section/metric
        """
        logger.info("Adapting structure to available data (using Gemini normal)...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        
        if not file_list:
            # No files - return structure with all marked as "needs_data" or "estimated"
            logger.warning("No files available, marking structure as estimated")
            adapted = {
                "final_structure": {
                    "sections": [],
                    "charts": [],
                    "missing_data_requests": [],
                    "estimation_notes": ["No data files available - will use estimations"]
                },
                "file_analysis": {
                    "files_analyzed": [],
                    "available_data_types": [],
                    "columns_found": {},
                    "time_periods": {},
                    "data_quality": "none",
                    "possible_analyses": []
                }
            }
            return adapted
        
        try:
            # Build prompt with expected structure
            structure_json = json.dumps(expected_structure.get("expected_structure", {}), indent=2, ensure_ascii=False)
            
            # Enrich prompt with file metadata already extracted (helps Gemini understand faster)
            file_metadata = {}
            for file_id, file_data in files.items():
                file_info = file_data.get("info", {})
                file_metadata[file_data.get("name", "unknown")] = {
                    "columns": file_info.get("columns", []),
                    "dtypes": list(file_info.get("dtypes", {}).values()) if file_info.get("dtypes") else [],
                    "num_rows": file_info.get("num_rows", 0),
                    "has_total_rows": file_info.get("has_total_rows", False)
                }
            
            metadata_json = json.dumps(file_metadata, indent=2, ensure_ascii=False)
            
            # Build enhanced prompt with metadata
            prompt = STRUCTURE_ADAPTATION_PROMPT.format(expected_structure=structure_json)
            prompt += f"\n\nFILE METADATA (already extracted to help you understand faster):\n{metadata_json}\n\nUse this metadata to understand the file structure quickly, but also read the actual files to confirm and get more details."
            
            # Use Gemini normal (no Code Execution) - much faster!
            response = await self.gemini_service.analyze_files_structure(
                prompt=prompt,
                files=file_list
            )
            
            # Extract JSON from text response (no code execution results)
            text_content = response.get("analysis_text", "")
            
            # Try to extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text_content, re.DOTALL)
            if json_match:
                adapted = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
                if json_match:
                    try:
                        adapted = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        json_str = json_match.group()
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        adapted = json.loads(json_str)
                else:
                    logger.warning("Could not parse adaptation JSON, using fallback")
                    adapted = {
                        "final_structure": {
                            "sections": expected_structure.get("expected_structure", {}).get("sections", []),
                            "charts": expected_structure.get("expected_structure", {}).get("charts_required", []),
                            "missing_data_requests": [],
                            "estimation_notes": ["Using expected structure as-is"]
                        },
                        "file_analysis": {
                            "files_analyzed": [f.get("name", "unknown") for f in files.values()],
                            "available_data_types": [],
                            "columns_found": {},
                            "time_periods": {},
                            "data_quality": "unknown"
                        }
                    }
            
            logger.info(f"Adapted structure: {len(adapted.get('final_structure', {}).get('sections', []))} sections")
            return adapted
            
        except Exception as e:
            logger.error(f"Error adapting structure to data: {e}")
            # Fallback: return expected structure marked as estimated
            return {
                "final_structure": {
                    "sections": expected_structure.get("expected_structure", {}).get("sections", []),
                    "charts": expected_structure.get("expected_structure", {}).get("charts_required", []),
                    "missing_data_requests": [],
                    "estimation_notes": [f"Error analyzing files: {str(e)} - will proceed with estimations"]
                },
                "file_analysis": {
                    "files_analyzed": [f.get("name", "unknown") for f in files.values()],
                    "available_data_types": [],
                    "columns_found": {},
                    "time_periods": {},
                    "data_quality": "unknown",
                    "error": str(e)
                }
            }
    
    async def check_data_availability(self, requirements: Dict[str, Any], files: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Compare requirements with available files
        
        Args:
            requirements: Requirements dict from analyze_question_requirements
            files: Dict of uploaded files
            
        Returns:
            Availability status dict
        """
        logger.info("Checking data availability...")
        
        data_reqs = requirements.get("data_requirements", [])
        # Note: check_data_availability is synchronous but we keep this async for API consistency
        availability = self.data_checker.check_data_availability(data_reqs, files)
        
        logger.info(f"Availability: {availability['analysis_type']} - "
                   f"{len(availability['available'])} available, "
                   f"{len(availability['partial'])} partial, "
                   f"{len(availability['missing'])} missing")
        
        return availability
    
    def _identify_step_requirements(
        self, 
        step_name: str, 
        requirements: Dict[str, Any],
        availability: Dict[str, Any],
        has_files: bool = True
    ) -> Dict[str, Any]:
        """
        Identify what requirements are needed for a specific analysis step
        
        Args:
            step_name: Name of the analysis step
            requirements: Requirements dict
            availability: Availability status dict
            has_files: Whether files are available (if True, always try to proceed)
            
        Returns:
            Dict with can_proceed flag and missing requirements list
        """
        data_reqs = requirements.get("data_requirements", [])
        
        # Map step names to required data types (preferred, but not mandatory)
        step_requirements_map = {
            "current_context": ["cash_flow", "balance_sheet", "income_statement"],
            "impacts": ["cash_flow", "payroll", "expenses"],
            "scenarios": ["cash_flow", "revenue", "expenses"],
            "recommendations": []  # Can proceed with any available data
        }
        
        needed_types = step_requirements_map.get(step_name, [])
        
        # If recommendations, can always proceed
        if step_name == "recommendations":
            return {
                "can_proceed": True,
                "missing": [],
                "needed": []
            }
        
        # Filter requirements needed for this step
        needed_reqs = [
            req for req in data_reqs 
            if req.get("data_type", "").lower() in needed_types
        ]
        
        if not needed_reqs:
            # No specific requirements for this step - can proceed if files available
            return {
                "can_proceed": has_files,
                "missing": [],
                "needed": []
            }
        
        # Check which of these are available/missing using availability results
        available_req_ids = {r.get("requirement_id") for r in availability.get("available", [])}
        partial_req_ids = {r.get("requirement_id") for r in availability.get("partial", [])}
        
        missing_reqs = [
            req for req in needed_reqs 
            if req.get("requirement_id") not in available_req_ids 
            and req.get("requirement_id") not in partial_req_ids
        ]
        
        # FLEXIBLE LOGIC: Always proceed if we have files, even if requirements don't match exactly
        # The AI will analyze what's available and adapt
        critical_missing = [r for r in missing_reqs if r.get("critical", False)]
        
        # Can proceed if:
        # 1. We have some available/partial data, OR
        # 2. We have files (even if they don't match requirements exactly) - AI will adapt
        can_proceed = (
            len(available_req_ids) > 0 or 
            len(partial_req_ids) > 0 or 
            (has_files and len(critical_missing) == 0)  # If files exist and no critical missing, try anyway
        )
        
        return {
            "can_proceed": can_proceed,
            "missing": missing_reqs,
            "needed": needed_reqs
        }
    
    async def analyze_decision_full(self, question: str, files: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3-4: Full analysis with multiple passes
        
        Args:
            question: User's decision question
            files: Dict of uploaded files
            requirements: Requirements dict
            
        Returns:
            Complete analysis results
        """
        logger.info("Starting full decision analysis...")
        
        # Prepare file list for Gemini
        file_list = [file_data["file"] for file_data in files.values()]
        
        # Execute multi-pass analysis
        results = {}
        
        try:
            # Pass 1: Current financial context
            logger.info("Pass 1: Analyzing current context...")
            context_result = await self.gemini_service.analyze_decision_pass(
                prompt=CURRENT_CONTEXT_PROMPT,
                files=file_list
            )
            results["current_context"] = context_result
            
            # Pass 2: Impact calculations
            logger.info("Pass 2: Calculating impacts...")
            impact_result = await self.gemini_service.analyze_decision_pass(
                prompt=IMPACT_CALCULATION_PROMPT.format(question=question),
                files=file_list,
                previous_results=context_result
            )
            results["impacts"] = impact_result
            
            # Pass 3: Scenario projections
            logger.info("Pass 3: Generating scenarios...")
            scenario_result = await self.gemini_service.analyze_decision_pass(
                prompt=SCENARIO_PROJECTION_PROMPT.format(question=question),
                files=file_list,
                previous_results={**context_result, **impact_result}
            )
            results["scenarios"] = scenario_result
            
            # Pass 4: Recommendations
            logger.info("Pass 4: Generating recommendations...")
            recommendations_result = await self.gemini_service.analyze_decision_pass(
                prompt=RECOMMENDATIONS_PROMPT.format(question=question),
                files=file_list,
                previous_results=results
            )
            results["recommendations"] = recommendations_result
            
            # Format results
            formatted_results = self.format_analysis_results(question, results, requirements)
            
            logger.info("Full analysis completed")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in full analysis: {e}", exc_info=True)
            raise
    
    async def analyze_decision_partial(self, question: str, files: Dict[str, Any], requirements: Dict[str, Any], availability: Dict[str, Any]) -> Dict[str, Any]:
        """
        Partial analysis with available data
        
        Args:
            question: User's decision question
            files: Dict of uploaded files
            requirements: Requirements dict
            availability: Availability status
            
        Returns:
            Partial analysis results
        """
        logger.info("Starting partial decision analysis...")
        
        # Use available data for analysis
        file_list = [file_data["file"] for file_data in files.values()]
        
        # Do what we can with available data
        results = {}
        
        try:
            # Try to get current context if possible
            if availability["available"] or availability["partial"]:
                context_result = await self.gemini_service.analyze_decision_pass(
                    prompt=CURRENT_CONTEXT_PROMPT,
                    files=file_list
                )
                results["current_context"] = context_result
                
                # Try impact calculation with available data
                impact_result = await self.gemini_service.analyze_decision_pass(
                    prompt=IMPACT_CALCULATION_PROMPT.format(question=question) + "\n\nNote: Some data may be missing. Work with what's available.",
                    files=file_list,
                    previous_results=context_result
                )
                results["impacts"] = impact_result
            
            # Add missing data warnings
            results["missing_data"] = {
                "missing_requirements": availability["missing"],
                "partial_requirements": availability["partial"],
                "limitations": "Analysis is limited due to missing data"
            }
            
            formatted_results = self.format_analysis_results(question, results, requirements)
            formatted_results["analysis_type"] = "partial"
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in partial analysis: {e}", exc_info=True)
            raise
    
    async def analyze_file_contents(self, files: Dict[str, Any], converted_files_cache: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze uploaded files to understand what data is actually available
        
        Args:
            files: Dict of uploaded files
            converted_files_cache: Optional cache of pre-converted CSV files
            
        Returns:
            Dict with analysis of available data and possible analyses
        """
        logger.info("Analyzing file contents to understand available data...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        
        if not file_list:
            return {
                "files_analyzed": [],
                "available_data_types": [],
                "columns_found": {},
                "possible_analyses": [],
                "data_quality": "none"
            }
        
        try:
            # Use Gemini to analyze file contents
            response = await self.gemini_service.analyze_decision_pass(
                prompt=FILE_CONTENT_ANALYSIS_PROMPT,
                files=file_list,
                converted_files_cache=converted_files_cache
            )
            
            # Extract JSON from response
            text_content = response.get("analysis_text", "")
            
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', text_content, re.DOTALL)
            if json_match:
                try:
                    file_analysis = json.loads(json_match.group())
                    logger.info(f"File content analysis completed: {len(file_analysis.get('files_analyzed', []))} files")
                    return file_analysis
                except json.JSONDecodeError:
                    logger.warning("Could not parse file analysis JSON, using fallback")
            
            # Fallback: extract from text
            return {
                "files_analyzed": [f.get("name", "unknown") for f in files.values()],
                "available_data_types": [],
                "columns_found": {},
                "possible_analyses": ["General financial analysis"],
                "data_quality": "unknown",
                "raw_analysis": text_content
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file contents: {e}")
            return {
                "files_analyzed": [f.get("name", "unknown") for f in files.values()],
                "available_data_types": [],
                "columns_found": {},
                "possible_analyses": ["General financial analysis"],
                "data_quality": "unknown",
                "error": str(e)
            }
    
    async def generate_final_report(
        self,
        question: str,
        adapted_structure: Dict[str, Any],
        files: Dict[str, Any],
        decision_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 3: Generate final report using adapted structure
        
        Args:
            question: User's decision question
            adapted_structure: Adapted structure from adapt_structure_to_data
            files: Dict of uploaded files (CSV)
            decision_summary: Decision summary from Step 1
            
        Returns:
            Complete analysis results
        """
        logger.info("Generating final report with adapted structure...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        has_files = len(file_list) > 0
        
        if not has_files:
            # No files - use advisory only
            return await self.analyze_decision_advisory(question)
        
        try:
            # Build prompt with adapted structure
            final_structure = adapted_structure.get("final_structure", {})
            file_analysis = adapted_structure.get("file_analysis", {})
            
            structure_json = json.dumps(final_structure, indent=2, ensure_ascii=False)
            file_analysis_json = json.dumps(file_analysis, indent=2, ensure_ascii=False)
            
            prompt = FINAL_REPORT_GENERATION_PROMPT.format(
                question=question,
                adapted_structure=structure_json,
                file_analysis=file_analysis_json
            )
            
            # Execute single Code Execution call
            comprehensive_result = await self.gemini_service.analyze_decision_pass(
                prompt=prompt,
                files=file_list
            )
            
            # Format results
            formatted_results = await self._format_comprehensive_results(
                question,
                comprehensive_result,
                {"decision_summary": decision_summary},
                {"available": [], "partial": [], "missing": []}
            )
            
            # Add structure information
            formatted_results["structure_info"] = {
                "expected_structure": decision_summary,
                "adapted_structure": final_structure,
                "file_analysis": file_analysis
            }
            
            logger.info("Final report generated successfully")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            raise
    
    async def analyze_decision_fast(
        self,
        question: str,
        files: Dict[str, Any],
        requirements: Dict[str, Any],
        availability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fast single-pass comprehensive analysis - generates complete report in one call
        
        Args:
            question: User's decision question
            files: Dict of uploaded files
            requirements: Requirements dict
            availability: Availability status
            
        Returns:
            Complete analysis results
        """
        logger.info("Starting fast comprehensive analysis (single pass)...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        has_files = len(file_list) > 0
        
        if not has_files:
            # No files - use advisory only
            return await self.analyze_decision_advisory(question)
        
        # Convert files to CSV once (optimization)
        logger.info("Converting files to CSV (one-time conversion)...")
        converted_files_cache = {}
        temp_excel_files = []
        
        for file_data in files.values():
            file = file_data["file"]
            if hasattr(file, 'read'):
                file.seek(0)
                original_name = getattr(file, 'name', 'file.xlsx')
                suffix = Path(original_name).suffix or '.xlsx'
                
                if suffix.lower() in ['.xlsx', '.xls']:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(file.read())
                        temp_file_path = tmp.name
                        temp_excel_files.append(temp_file_path)
                    
                    csv_path = self.gemini_service._convert_to_csv(temp_file_path, original_name)
                    display_name = Path(original_name).stem + '.csv'
                    converted_files_cache[file] = (csv_path, display_name)
                    logger.info(f"Cached CSV conversion: {original_name} -> {display_name}")
                else:
                    converted_files_cache[file] = (None, original_name)
                
                file.seek(0)
        
        try:
            # Single comprehensive analysis pass
            logger.info("Running comprehensive analysis (single pass)...")
            
            comprehensive_prompt = COMPREHENSIVE_ANALYSIS_PROMPT.format(question=question)
            
            # Execute single comprehensive pass
            comprehensive_result = await self.gemini_service.analyze_decision_pass(
                prompt=comprehensive_prompt,
                files=file_list,
                converted_files_cache=converted_files_cache
            )
            
            # Format results from single comprehensive response
            formatted_results = await self._format_comprehensive_results(
                question,
                comprehensive_result,
                requirements,
                availability
            )
            
            logger.info("Fast comprehensive analysis completed")
            return formatted_results
            
        finally:
            # Cleanup cached CSV files and temp Excel files
            for file, (csv_path, _) in converted_files_cache.items():
                if csv_path and os.path.exists(csv_path):
                    try:
                        os.unlink(csv_path)
                    except Exception as e:
                        logger.warning(f"Error cleaning up cached CSV {csv_path}: {e}")
            
            for temp_excel in temp_excel_files:
                if os.path.exists(temp_excel):
                    try:
                        os.unlink(temp_excel)
                    except Exception as e:
                        logger.warning(f"Error cleaning up temp Excel {temp_excel}: {e}")
    
    async def analyze_decision_progressive(
        self, 
        question: str, 
        files: Dict[str, Any], 
        requirements: Dict[str, Any],
        availability: Dict[str, Any],
        file_content_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Progressive analysis that requests missing data during the process
        (Kept for backward compatibility, but fast() is preferred)
        
        Args:
            question: User's decision question
            files: Dict of uploaded files
            requirements: Requirements dict
            availability: Availability status
            file_content_analysis: Optional pre-analysis of file contents
            
        Returns:
            Analysis results with missing data requests embedded
        """
        logger.info("Starting progressive decision analysis...")
        
        file_list = [file_data["file"] for file_data in files.values()]
        results = {}
        missing_data_requests = []  # Track what data is needed at each step
        
        # Convert files to CSV once (optimization - avoid reconverting for each pass)
        logger.info("Converting files to CSV (one-time conversion)...")
        converted_files_cache = {}  # Cache: original_file -> (csv_path, display_name)
        temp_excel_files = []  # Track temp Excel files for cleanup
        
        for file_data in files.values():
            file = file_data["file"]
            if hasattr(file, 'read'):
                file.seek(0)
                original_name = getattr(file, 'name', 'file.xlsx')
                suffix = Path(original_name).suffix or '.xlsx'
                
                # Only convert Excel files, cache CSV files
                if suffix.lower() in ['.xlsx', '.xls']:
                    # Save to temp file first
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(file.read())
                        temp_file_path = tmp.name
                        temp_excel_files.append(temp_file_path)
                    
                    # Convert to CSV
                    csv_path = self.gemini_service._convert_to_csv(temp_file_path, original_name)
                    display_name = Path(original_name).stem + '.csv'
                    converted_files_cache[file] = (csv_path, display_name)
                    logger.info(f"Cached CSV conversion: {original_name} -> {display_name}")
                else:
                    # CSV file - use as is
                    converted_files_cache[file] = (None, original_name)  # Will be handled in analyze_decision_pass
                
                file.seek(0)
        
        # If file content analysis not provided, do it now (with cache)
        if file_content_analysis is None:
            file_content_analysis = await self.analyze_file_contents(files, converted_files_cache)
        
        # Store file content analysis in results
        results["file_content_analysis"] = file_content_analysis
        
        # Step explanations for missing data requests
        step_explanations = {
            "current_context": {
                "step_name": "Current Financial Context Analysis",
                "why_important": "To understand the current financial situation before analyzing the decision impact",
                "can_skip": False
            },
            "impacts": {
                "step_name": "Impact Calculations",
                "why_important": "To calculate the direct financial impact of your decision (costs, cash flow changes)",
                "can_skip": False
            },
            "scenarios": {
                "step_name": "Scenario Projections",
                "why_important": "To project future cash flow and financial scenarios over 12 months",
                "can_skip": True  # Scenarios can be skipped
            },
            "recommendations": {
                "step_name": "Recommendations",
                "why_important": "To provide actionable recommendations based on the analysis",
                "can_skip": False
            }
        }
        
        # Build enhanced prompts with file content analysis
        available_analyses = file_content_analysis.get("possible_analyses", [])
        available_data_types = file_content_analysis.get("available_data_types", [])
        data_quality = file_content_analysis.get("data_quality", "unknown")
        columns_found = file_content_analysis.get("columns_found", {})
        time_periods = file_content_analysis.get("time_periods", {})
        
        # Enhanced context prompt with file analysis info
        enhanced_context_prompt = CURRENT_CONTEXT_PROMPT
        if available_analyses or available_data_types:
            enhanced_context_prompt += f"""

CONTEXT FROM FILE CONTENT ANALYSIS:
- Available data types detected: {', '.join(available_data_types) if available_data_types else 'General financial data'}
- Possible analyses identified: {', '.join(available_analyses) if available_analyses else 'General analysis'}
- Data quality: {data_quality}
- Columns found in files: {json.dumps(columns_found, indent=2) if columns_found else 'Analyzing structure...'}

Use this information to focus your analysis on what's actually available in the files.
Read the files first to confirm the structure, then adapt your analysis accordingly.
"""
        
        enhanced_impact_prompt = IMPACT_CALCULATION_PROMPT.format(question=question)
        if available_data_types or columns_found:
            enhanced_impact_prompt += f"""

CONTEXT FROM FILE CONTENT ANALYSIS:
- Available data types: {', '.join(available_data_types) if available_data_types else 'General financial data'}
- Columns found: {json.dumps(columns_found, indent=2) if columns_found else 'Various financial columns'}
- Use the actual data structure found in files to calculate impacts accurately.
- Look for cost/expense columns, cash columns, revenue columns - whatever is actually present.
"""
        
        enhanced_scenario_prompt = SCENARIO_PROJECTION_PROMPT.format(question=question)
        if available_data_types or time_periods:
            enhanced_scenario_prompt += f"""

CONTEXT FROM FILE CONTENT ANALYSIS:
- Available data types: {', '.join(available_data_types) if available_data_types else 'General financial data'}
- Time periods available: {json.dumps(time_periods, indent=2) if time_periods else 'Check files for date ranges'}
- Use historical patterns from files to create realistic projections.
- If historical data exists, use it to inform your scenarios.
"""
        
        try:
            # FLEXIBLE APPROACH: Always try to analyze with available files
            # Use file content analysis to adapt prompts and focus on what's actually available
            
            # Light logic: Request data if significantly missing (simple threshold)
            missing_count = len(availability.get("missing", []))
            critical_missing_count = len([r for r in availability.get("missing", []) if r.get("critical", False)])
            
            # Simple rule: request if many missing OR critical missing
            should_request_data = missing_count >= 3 or critical_missing_count >= 2
            
            logger.info(f"Missing data: {missing_count} total, {critical_missing_count} critical. Request: {should_request_data}")
            
            # Pass 1: Current financial context
            logger.info("Pass 1: Analyzing current context with file content analysis...")
            
            has_files = len(file_list) > 0
            context_needs = self._identify_step_requirements("current_context", requirements, availability, has_files)
            
            # Always try to analyze if we have files - AI will adapt to available data
            if has_files:
                context_result = await self.gemini_service.analyze_decision_pass(
                    prompt=enhanced_context_prompt,
                    files=file_list,
                    converted_files_cache=converted_files_cache
                )
                results["current_context"] = context_result
                
                # Only request missing data if threshold is met (for realistic MVP demo)
                if context_needs["missing"] and should_request_data:
                    explanation = step_explanations["current_context"]
                    missing_data_requests.append({
                        "step": "current_context",
                        "step_name": explanation["step_name"],
                        "missing_requirements": context_needs["missing"],
                        "why_important": explanation["why_important"],
                        "can_skip": explanation["can_skip"],
                        "note": f"Analysis performed with available data ({', '.join(available_data_types) if available_data_types else 'general data'}), but some ideal requirements are missing",
                        "request_priority": "high" if critical_missing_count >= 2 else "medium"
                    })
                # If we don't request, silently estimate (for MVP - shows tool is smart)
                elif context_needs["missing"]:
                    logger.info(f"Missing requirements detected but proceeding with estimation (threshold not met)")
            else:
                # No files at all
                explanation = step_explanations["current_context"]
                missing_data_requests.append({
                    "step": "current_context",
                    "step_name": explanation["step_name"],
                    "missing_requirements": context_needs["missing"],
                    "why_important": explanation["why_important"],
                    "can_skip": explanation["can_skip"]
                })
                results["current_context"] = {
                    "status": "missing_data",
                    "missing_requirements": context_needs["missing"]
                }
            
            # Pass 2: Impact calculations
            logger.info("Pass 2: Calculating impacts with file content analysis...")
            
            impact_needs = self._identify_step_requirements("impacts", requirements, availability, has_files)
            
            # Always try to analyze if we have files
            if has_files:
                impact_result = await self.gemini_service.analyze_decision_pass(
                    prompt=enhanced_impact_prompt,
                    files=file_list,
                    previous_results=results.get("current_context", {}),
                    converted_files_cache=converted_files_cache
                )
                results["impacts"] = impact_result
                
                # Only request missing data if threshold is met
                if impact_needs["missing"] and should_request_data:
                    explanation = step_explanations["impacts"]
                    missing_data_requests.append({
                        "step": "impacts",
                        "step_name": explanation["step_name"],
                        "missing_requirements": impact_needs["missing"],
                        "why_important": explanation["why_important"],
                        "can_skip": explanation["can_skip"],
                        "note": f"Analysis performed with available data ({', '.join(available_data_types) if available_data_types else 'general data'}), but some ideal requirements are missing",
                        "request_priority": "high" if critical_missing_count >= 2 else "medium"
                    })
                elif impact_needs["missing"]:
                    logger.info(f"Missing impact requirements but proceeding with estimation")
            else:
                explanation = step_explanations["impacts"]
                missing_data_requests.append({
                    "step": "impacts",
                    "step_name": explanation["step_name"],
                    "missing_requirements": impact_needs["missing"],
                    "why_important": explanation["why_important"],
                    "can_skip": explanation["can_skip"]
                })
                results["impacts"] = {
                    "status": "missing_data",
                    "missing_requirements": impact_needs["missing"]
                }
            
            # Pass 3: Scenario projections
            logger.info("Pass 3: Generating scenarios with file content analysis...")
            
            scenario_needs = self._identify_step_requirements("scenarios", requirements, availability, has_files)
            
            # Always try to analyze if we have files
            if has_files:
                scenario_result = await self.gemini_service.analyze_decision_pass(
                    prompt=enhanced_scenario_prompt,
                    files=file_list,
                    previous_results={**results.get("current_context", {}), **results.get("impacts", {})},
                    converted_files_cache=converted_files_cache
                )
                results["scenarios"] = scenario_result
                
                # Scenarios are less critical - only request if many critical missing
                if scenario_needs["missing"] and (should_request_data and critical_missing_count >= 2):
                    explanation = step_explanations["scenarios"]
                    missing_data_requests.append({
                        "step": "scenarios",
                        "step_name": explanation["step_name"],
                        "missing_requirements": scenario_needs["missing"],
                        "why_important": explanation["why_important"],
                        "can_skip": explanation["can_skip"],
                        "note": f"Analysis performed with available data ({', '.join(available_data_types) if available_data_types else 'general data'}), but some ideal requirements are missing",
                        "request_priority": "low"  # Scenarios can be estimated more easily
                    })
                elif scenario_needs["missing"]:
                    logger.info(f"Missing scenario requirements but proceeding with estimation")
            else:
                explanation = step_explanations["scenarios"]
                missing_data_requests.append({
                    "step": "scenarios",
                    "step_name": explanation["step_name"],
                    "missing_requirements": scenario_needs["missing"],
                    "why_important": explanation["why_important"],
                    "can_skip": explanation["can_skip"]
                })
                results["scenarios"] = {
                    "status": "missing_data",
                    "missing_requirements": scenario_needs["missing"]
                }
            
            # Pass 4: Recommendations
            logger.info("Pass 4: Generating recommendations...")
            
            # Recommendations can always proceed with partial data
            recommendations_result = await self.gemini_service.analyze_decision_pass(
                prompt=RECOMMENDATIONS_PROMPT.format(question=question),
                files=file_list,
                previous_results=results,
                converted_files_cache=converted_files_cache
            )
            results["recommendations"] = recommendations_result
            
            # Cleanup cached CSV files and temp Excel files at the end
            for file, (csv_path, _) in converted_files_cache.items():
                if csv_path and os.path.exists(csv_path):
                    try:
                        os.unlink(csv_path)
                        logger.debug(f"Cleaned up cached CSV: {csv_path}")
                    except Exception as e:
                        logger.warning(f"Error cleaning up cached CSV {csv_path}: {e}")
            
            # Cleanup temp Excel files
            for temp_excel in temp_excel_files:
                if os.path.exists(temp_excel):
                    try:
                        os.unlink(temp_excel)
                        logger.debug(f"Cleaned up temp Excel: {temp_excel}")
                    except Exception as e:
                        logger.warning(f"Error cleaning up temp Excel {temp_excel}: {e}")
            
            # Format results with missing data requests
            formatted_results = self.format_analysis_results(question, results, requirements)
            formatted_results["missing_data_requests"] = missing_data_requests
            formatted_results["analysis_type"] = "progressive"
            
            logger.info(f"Progressive analysis completed. {len(missing_data_requests)} missing data request(s)")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in progressive analysis: {e}", exc_info=True)
            raise
    
    async def analyze_decision_advisory(self, question: str) -> Dict[str, Any]:
        """
        Generate advisory-only analysis without data
        
        Args:
            question: User's decision question
            
        Returns:
            Advisory analysis results
        """
        logger.info("Generating advisory-only analysis...")
        
        prompt = ADVISORY_ONLY_PROMPT.format(question=question)
        
        try:
            response = self.gemini_service.model.generate_content(prompt)
            
            # Extract text content
            text_content = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content += part.text
            
            return {
                "analysis_type": "advisory_only",
                "decision_summary": {
                    "question": question,
                    "description": "General financial guidance without specific data"
                },
                "advisory_text": text_content,
                "key_considerations": self._extract_considerations(text_content),
                "required_data": "Financial data files needed for detailed analysis"
            }
            
        except Exception as e:
            logger.error(f"Error in advisory analysis: {e}", exc_info=True)
            raise
    
    def format_analysis_results(self, question: str, raw_results: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format multi-pass results into structured output matching example format
        
        Args:
            question: Original question
            raw_results: Results from multi-pass analysis
            requirements: Original requirements
            
        Returns:
            Formatted results dict
        """
        # Extract data from raw results
        current_context = raw_results.get("current_context", {})
        impacts = raw_results.get("impacts", {})
        scenarios = raw_results.get("scenarios", {})
        recommendations = raw_results.get("recommendations", {})
        
        # Check if any step has missing_data status
        has_missing_data = (
            (isinstance(current_context, dict) and current_context.get("status") == "missing_data") or
            (isinstance(impacts, dict) and impacts.get("status") == "missing_data") or
            (isinstance(scenarios, dict) and scenarios.get("status") == "missing_data")
        )
        
        # Extract key metrics from impacts (only if impacts completed)
        if isinstance(impacts, dict) and impacts.get("status") != "missing_data":
            impact_text = impacts.get("analysis_text", "")
            execution_outputs = impacts.get("execution_outputs", [])
            key_metrics = self._extract_key_metrics(impact_text, execution_outputs)
        else:
            key_metrics = {}
        
        # Extract critical factors
        critical_factors = self._extract_critical_factors(raw_results)
        
        # Extract scenarios (only if scenarios completed)
        if isinstance(scenarios, dict) and scenarios.get("status") != "missing_data":
            scenario_data = self._extract_scenarios(scenarios)
        else:
            scenario_data = {}
        
        # Extract recommendations
        recommended_actions = self._extract_recommendations(recommendations)
        alternatives = self._extract_alternatives(recommendations)
        
        # Extract charts
        charts = []
        for result_key, result_data in raw_results.items():
            if isinstance(result_data, dict) and result_data.get("chart_files"):
                charts.extend(result_data["chart_files"])
        
        # Determine analysis type
        analysis_type = "progressive" if has_missing_data else "full"
        
        # Extract hypotheses from requirements or raw_results if available
        hypotheses = []
        if isinstance(requirements, dict) and "hypotheses" in requirements:
            hypotheses = requirements["hypotheses"]
        elif isinstance(raw_results, dict):
            # Try to extract from any result that might contain hypotheses
            for result_key, result_data in raw_results.items():
                if isinstance(result_data, dict) and "hypotheses" in result_data:
                    hypotheses = result_data["hypotheses"]
                    break
        
        # Build formatted results
        formatted_results = {
            "analysis_type": analysis_type,
            "decision_summary": {
                "question": question,
                "description": requirements.get("decision_summary", {}).get("description", ""),
                "importance": requirements.get("decision_summary", {}).get("importance", "")
            },
            "key_metrics": key_metrics,
            "critical_factors": critical_factors,
            "current_context": self._format_current_context(current_context),
            "scenarios": scenario_data,
            "recommended_actions": recommended_actions,
            "alternatives": alternatives,
            "charts": charts,
            "hypotheses": hypotheses,  # Add hypotheses to the result
            "raw_results": raw_results  # Keep for debugging
        }
        
        # Enrich the results
        enriched_results = self._enrich_analysis(formatted_results, raw_results)
        
        return enriched_results
    
    def _extract_key_metrics(self, text: str, outputs: List[str]) -> Dict[str, Any]:
        """Extract key metrics from analysis text - enhanced for MVP"""
        metrics = {}
        
        # Combine text and outputs for extraction (Python print statements may contain metrics)
        combined_text = text + "\n" + "\n".join(outputs)
        logger.info(f"Extracting metrics from text (length: {len(text)}) and {len(outputs)} outputs")
        
        # Look for total cost (multiple patterns including formatted "85k€")
        cost_patterns = [
            r'(?:coût|cost).*total[:\s]*([0-9,\.]+)\s*([€$kK]?)\s*(?:sur|over|for)?\s*([0-9]+)?\s*(?:mois|months?|ans?|years?)?',
            r'total.*(?:coût|cost)[:\s]*([0-9,\.]+)\s*([€$kK]?)\s*(?:sur|over|for)?\s*([0-9]+)?\s*(?:mois|months?)?',
            r'([0-9,\.]+)\s*([€$kK]?)\s*(?:sur|over|for)?\s*([0-9]+)?\s*(?:mois|months?)?\s*(?:total|chargé)',
            r'(\d+)\s*k\s*€',  # Format "85k€"
            r'(\d+)\s*k€',  # Format "85k€" without space
        ]
        for pattern in cost_patterns:
            cost_match = re.search(pattern, combined_text, re.IGNORECASE)
            if cost_match:
                value = cost_match.group(1).replace(',', '').replace(' ', '')
                unit = cost_match.group(2) if len(cost_match.groups()) > 1 and cost_match.group(2) else "k€" if 'k' in pattern else "€"
                period = cost_match.group(3) if len(cost_match.groups()) > 2 and cost_match.group(3) else None
                period_str = f" over {period} months" if period else ""
                metrics["total_cost"] = {
                    "value": value,
                    "unit": unit,
                    "period": period,
                    "description": f"Total cost{period_str}"
                }
                logger.info(f"Found total_cost: {value}{unit}")
                break
        
        # Look for cash impact (multiple patterns including formatted "-12k€")
        cash_patterns = [
            r'(?:cash|trésorerie).*impact[:\s]*([-0-9,\.]+)\s*([€$kK]?)\s*(?:average|moyenne|réduction)?',
            r'impact.*(?:cash|trésorerie)[:\s]*([-0-9,\.]+)\s*([€$kK]?)',
            r'trésorerie[:\s]*([-0-9,\.]+)\s*([€$kK]?)\s*(?:réduction|impact)?',
            r'([-0-9,\.]+)\s*([€$kK]?)\s*(?:réduction|reduction|impact).*(?:moyenne|average)?',
            r'-(\d+)\s*k\s*€',  # Format "-12k€"
            r'-(\d+)\s*k€',  # Format "-12k€" without space
        ]
        for pattern in cash_patterns:
            cash_match = re.search(pattern, combined_text, re.IGNORECASE)
            if cash_match:
                value = cash_match.group(1).replace(',', '').replace(' ', '')
                # Skip if value is just a dot or empty
                if not value or value == '.' or value == '-':
                    continue
                # Add negative sign if pattern starts with -
                if pattern.startswith(r'-') or (len(cash_match.groups()) > 0 and '-' in cash_match.group(0)):
                    value = '-' + value.lstrip('-')
                # Validate that value is actually a number (allow decimal points)
                try:
                    float(value.replace('-', ''))
                except ValueError:
                    continue  # Skip invalid values like ".k€"
                unit = cash_match.group(2) if len(cash_match.groups()) > 1 and cash_match.group(2) else "k€" if 'k' in pattern else "€"
                metrics["cash_impact"] = {
                    "value": value,
                    "unit": unit,
                    "description": "Average cash impact"
                }
                logger.info(f"Found cash_impact: {value}{unit}")
                break
        
        # Look for break-even (multiple patterns including formatted "+4%")
        breakeven_patterns = [
            r'(?:break.*even|point.*mort)[:\s]*([0-9,\.]+)\s*(%|percent|pourcent)',
            r'point.*mort[:\s]*([0-9,\.]+)\s*(%|percent|pourcent)',
            r'([0-9,\.]+)\s*(%|percent|pourcent).*(?:supplémentaire|additional|requis|required).*(?:CA|revenue|revenu)',
            r'\+([0-9,\.]+)\s*(%|percent|pourcent)',  # Format "+4%"
            r'\+(\d+)\s*%',  # Format "+4%" without word
        ]
        for pattern in breakeven_patterns:
            breakeven_match = re.search(pattern, combined_text, re.IGNORECASE)
            if breakeven_match:
                value = breakeven_match.group(1).replace(',', '').replace(' ', '')
                metrics["break_even"] = {
                    "value": value,
                    "unit": "%",
                    "description": "Additional revenue required"
                }
                logger.info(f"Found break_even: {value}%")
                break
        
        # Look for payback period
        payback_patterns = [
            r'payback[:\s]*([0-9,\.]+)\s*(?:months?|mois)',
            r'rentabilisé.*([0-9,\.]+)\s*(?:mois|months?)',
            r'retour.*investissement[:\s]*([0-9,\.]+)\s*(?:mois|months?)'
        ]
        for pattern in payback_patterns:
            payback_match = re.search(pattern, combined_text, re.IGNORECASE)
            if payback_match:
                value = payback_match.group(1).replace(',', '').replace(' ', '')
                metrics["payback_period"] = {
                    "value": value,
                    "unit": "months",
                    "description": "Payback period"
                }
                logger.info(f"Found payback_period: {value} months")
                break
        
        # Look for ROI
        roi_patterns = [
            r'ROI[:\s]*([0-9,\.]+)\s*(%|percent|pourcent)',
            r'return.*investment[:\s]*([0-9,\.]+)\s*(%|percent|pourcent)',
            r'retour.*investissement[:\s]*([0-9,\.]+)\s*(%|percent|pourcent)'
        ]
        for pattern in roi_patterns:
            roi_match = re.search(pattern, combined_text, re.IGNORECASE)
            if roi_match:
                value = roi_match.group(1).replace(',', '').replace(' ', '')
                metrics["roi"] = {
                    "value": value,
                    "unit": "%",
                    "description": "Return on investment"
                }
                logger.info(f"Found roi: {value}%")
                break
        
        if not metrics:
            logger.warning("No metrics extracted! Text may not match expected format.")
            logger.debug(f"Text preview: {combined_text[:500]}")
        else:
            logger.info(f"Extracted {len(metrics)} metrics: {list(metrics.keys())}")
        
        return metrics
    
    def _extract_critical_factors(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract critical factors from results - enhanced for MVP"""
        factors = []
        
        # Try to extract from multiple sources
        text_sources = []
        
        # From recommendations
        if isinstance(results.get("recommendations"), dict):
            text_sources.append(results["recommendations"].get("analysis_text", ""))
        
        # From current context
        if isinstance(results.get("current_context"), dict):
            text_sources.append(results["current_context"].get("analysis_text", ""))
        
        # From impacts
        if isinstance(results.get("impacts"), dict):
            text_sources.append(results["impacts"].get("analysis_text", ""))
        
        combined_text = "\n".join(text_sources)
        
        # Look for numbered factors (multiple patterns)
        factor_patterns = [
            r'(\d+)\.\s*([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\d+\.|\n\*\*|\Z)',
            r'(\d+)\s+([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\d+\s+|\n\*\*|\Z)',
            r'factor\s+(\d+)[:\s]+([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\w+\s+\d+|\Z)'
        ]
        
        for pattern in factor_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches[:5]:  # Limit to 5 factors
                    number = match[0].strip()
                    factor_name = match[1].strip()
                    description = match[2].strip() if len(match) > 2 else ""
                    
                    # Clean up description
                    description = re.sub(r'\s+', ' ', description).strip()
                    
                    factors.append({
                        "number": int(number) if number.isdigit() else len(factors) + 1,
                        "factor": factor_name,
                        "description": description
                    })
                break
        
        # If no numbered factors found, try to extract from "Ce qu'il faut prendre en compte" section
        if not factors:
            section_pattern = r'(?:ce qu.*prendre|factors?|considérations?)[^\n]*\n((?:\d+\.\s*[^\n]+\n[^\n]+\n?)+)'
            section_match = re.search(section_pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            if section_match:
                section_text = section_match.group(1)
                factor_pattern = r'(\d+)\.\s*([^\n]+)\n([^\n]+)'
                matches = re.findall(factor_pattern, section_text)
                for match in matches[:5]:
                    factors.append({
                        "number": int(match[0]),
                        "factor": match[1].strip(),
                        "description": match[2].strip()
                    })
        
        return factors[:5]  # Limit to 5 factors
    
    def _extract_scenarios(self, scenarios_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scenario data - enhanced for MVP"""
        scenarios = {}
        
        if isinstance(scenarios_data, dict):
            text = scenarios_data.get("analysis_text", "")
            outputs = scenarios_data.get("execution_outputs", [])
            
            # Look for scenario descriptions with more flexible patterns
            scenario_patterns = {
                "optimistic": [
                    r'(?:scenario|scénario)\s+optimistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|\*\*|\Z))',
                    r'optimistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:realistic|pessimistic|scenario|\*\*|\Z))',
                    r'best case[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:realistic|pessimistic|scenario|\*\*|\Z))'
                ],
                "realistic": [
                    r'(?:scenario|scénario)\s+realistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|\*\*|\Z))',
                    r'realistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|pessimistic|scenario|\*\*|\Z))',
                    r'most likely[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|pessimistic|scenario|\*\*|\Z))'
                ],
                "pessimistic": [
                    r'(?:scenario|scénario)\s+pessimistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|\*\*|\Z))',
                    r'pessimistic[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|realistic|scenario|\*\*|\Z))',
                    r'worst case[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|realistic|scenario|\*\*|\Z))'
                ]
            }
            
            for scenario_name, patterns in scenario_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if match:
                        description = match.group(1).strip()
                        # Clean up description
                        description = re.sub(r'\s+', ' ', description)
                        
                        # Extract key milestones and risk periods from description
                        milestones = []
                        risk_periods = []
                        
                        # Look for milestones (e.g., "trésorerie remonte à 50k€ en juin")
                        milestone_pattern = r'(?:trésorerie|cash).*?([0-9,\.]+)\s*([€$kK]?).*?(?:en|in|à)\s*([^\s,\.]+)'
                        milestone_matches = re.findall(milestone_pattern, description, re.IGNORECASE)
                        for m in milestone_matches:
                            milestones.append(f"{m[0]}{m[1]} en {m[2]}")
                        
                        # Look for risk periods (e.g., "trésorerie sous les 10k€ en mars-avril")
                        risk_pattern = r'(?:trésorerie|cash).*?(?:sous|under|below).*?([0-9,\.]+)\s*([€$kK]?).*?(?:en|in|à)\s*([^\s,\.]+)'
                        risk_matches = re.findall(risk_pattern, description, re.IGNORECASE)
                        for r in risk_matches:
                            risk_periods.append(f"{r[0]}{r[1]} en {r[2]}")
                        
                        scenarios[scenario_name] = {
                            "description": description,
                            "key_milestones": milestones[:3] if milestones else [],
                            "risk_periods": risk_periods[:3] if risk_periods else []
                        }
                        break
            
            # Extract best case and worst case summaries
            best_case_pattern = r'(?:best case|meilleur cas)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:worst|pire|\*\*|\Z))'
            best_match = re.search(best_case_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if best_match:
                scenarios["best_case"] = best_match.group(1).strip()
            
            worst_case_pattern = r'(?:worst case|pire cas)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:best|meilleur|\*\*|\Z))'
            worst_match = re.search(worst_case_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if worst_match:
                scenarios["worst_case"] = worst_match.group(1).strip()
        
        return scenarios
    
    def _extract_recommendations(self, recommendations_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract recommended actions - enhanced for MVP"""
        actions = []
        
        if isinstance(recommendations_data, dict):
            text = recommendations_data.get("analysis_text", "")
            
            # Look for prioritized actions with more flexible patterns
            # Critical actions
            critical_patterns = [
                r'(?:critical|critique)[^\n]*\n-?\s*([^\n]+(?:\n\s+-?\s*[^\n]+)*?)(?=\n(?:important|recommended|alternative|\*\*|\Z))',
                r'(?:must do|à faire)[^\n]*\n-?\s*([^\n]+(?:\n\s+-?\s*[^\n]+)*?)(?=\n(?:important|recommended|alternative|\*\*|\Z))'
            ]
            
            for pattern in critical_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    action_text = match.group(1).strip()
                    # Extract action and impact
                    action_match = re.match(r'([^\n]+)(?:\n\s*-?\s*impact[:\s]+([^\n]+))?', action_text, re.IGNORECASE)
                    if action_match:
                        action = action_match.group(1).strip()
                        impact = action_match.group(2).strip() if action_match.group(2) else None
                        # Extract timeline if present
                        timeline_match = re.search(r'(?:timeline|timing|quand)[:\s]+([^\n]+)', action_text, re.IGNORECASE)
                        timeline = timeline_match.group(1).strip() if timeline_match else None
                        
                        actions.append({
                            "priority": "critical",
                            "action": action,
                            "impact": impact,
                            "timeline": timeline
                        })
            
            # Important actions
            important_patterns = [
                r'(?:important|should do|à considérer)[^\n]*\n-?\s*([^\n]+(?:\n\s+-?\s*[^\n]+)*?)(?=\n(?:critical|recommended|alternative|\*\*|\Z))'
            ]
            
            for pattern in important_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    action_text = match.group(1).strip()
                    action_match = re.match(r'([^\n]+)(?:\n\s*-?\s*impact[:\s]+([^\n]+))?', action_text, re.IGNORECASE)
                    if action_match:
                        action = action_match.group(1).strip()
                        impact = action_match.group(2).strip() if action_match.group(2) else None
                        timeline_match = re.search(r'(?:timeline|timing|quand)[:\s]+([^\n]+)', action_text, re.IGNORECASE)
                        timeline = timeline_match.group(1).strip() if timeline_match else None
                        
                        actions.append({
                            "priority": "important",
                            "action": action,
                            "impact": impact,
                            "timeline": timeline
                        })
            
            # Recommended actions
            recommended_patterns = [
                r'(?:recommended|recommandé|nice to have)[^\n]*\n-?\s*([^\n]+(?:\n\s+-?\s*[^\n]+)*?)(?=\n(?:critical|important|alternative|\*\*|\Z))'
            ]
            
            for pattern in recommended_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    action_text = match.group(1).strip()
                    action_match = re.match(r'([^\n]+)(?:\n\s*-?\s*impact[:\s]+([^\n]+))?', action_text, re.IGNORECASE)
                    if action_match:
                        action = action_match.group(1).strip()
                        impact = action_match.group(2).strip() if action_match.group(2) else None
                        timeline_match = re.search(r'(?:timeline|timing|quand)[:\s]+([^\n]+)', action_text, re.IGNORECASE)
                        timeline = timeline_match.group(1).strip() if timeline_match else None
                        
                        actions.append({
                            "priority": "recommended",
                            "action": action,
                            "impact": impact,
                            "timeline": timeline
                        })
        
        return actions
    
    def _extract_alternatives(self, recommendations_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract alternatives - enhanced for MVP"""
        alternatives = []
        
        if isinstance(recommendations_data, dict):
            text = recommendations_data.get("analysis_text", "")
            
            # Look for alternatives with more flexible patterns
            alt_patterns = [
                r'alternative\s+\d+[:\s]+([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:alternative|\*\*|\Z))',
                r'alternative\s+\d+[:\s]+([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:alternative|\*\*|\Z))',
                r'([^\n]+)[:\s]+\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:alternative|\*\*|\Z))'
            ]
            
            for pattern in alt_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    name = match.group(1).strip()
                    description = match.group(2).strip()
                    
                    # Extract impact from description
                    impact_match = re.search(r'impact[:\s]+([^\n]+)', description, re.IGNORECASE)
                    impact = impact_match.group(1).strip() if impact_match else None
                    
                    # Extract pros/cons if present
                    pros_cons_match = re.search(r'(?:pros?/cons?|avantages?/inconvénients?)[:\s]+([^\n]+)', description, re.IGNORECASE)
                    pros_cons = pros_cons_match.group(1).strip() if pros_cons_match else None
                    
                    # Clean description (remove impact and pros/cons if already extracted)
                    clean_description = description
                    if impact_match:
                        clean_description = clean_description.replace(impact_match.group(0), "").strip()
                    if pros_cons_match:
                        clean_description = clean_description.replace(pros_cons_match.group(0), "").strip()
                    
                    alternatives.append({
                        "name": name,
                        "description": clean_description,
                        "impact": impact,
                        "pros_cons": pros_cons
                    })
                
                if alternatives:
                    break
        
        return alternatives
    
    def _format_current_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format current context data"""
        if isinstance(context_data, dict):
            # Check if this step has missing data status
            if context_data.get("status") == "missing_data":
                return {
                    "status": "missing_data",
                    "missing_requirements": context_data.get("missing_requirements", []),
                    "strengths": [],
                    "weaknesses": [],
                    "summary": "Analysis pending - missing data required"
                }
            
            text = context_data.get("analysis_text", "")
            
            # Extract strengths and weaknesses
            strengths = []
            weaknesses = []
            
            strengths_match = re.search(r'strengths?[^\n]*\n((?:[^\n]+\n?)+?)(?=weaknesses?|\Z)', text, re.IGNORECASE)
            if strengths_match:
                strengths = [s.strip() for s in strengths_match.group(1).split('\n') if s.strip()]
            
            weaknesses_match = re.search(r'weaknesses?[^\n]*\n((?:[^\n]+\n?)+?)(?=strengths?|\Z)', text, re.IGNORECASE)
            if weaknesses_match:
                weaknesses = [w.strip() for w in weaknesses_match.group(1).split('\n') if w.strip()]
            
            return {
                "status": "completed",
                "strengths": strengths,
                "weaknesses": weaknesses,
                "summary": text[:500] + "..." if len(text) > 500 else text
            }
        
        return {"status": "completed", "strengths": [], "weaknesses": [], "summary": ""}
    
    def _extract_considerations(self, text: str) -> List[str]:
        """Extract key considerations from advisory text"""
        considerations = []
        
        # Look for bullet points or numbered lists
        bullet_pattern = r'(?:[-•*]|\d+\.)\s*([^\n]+)'
        matches = re.findall(bullet_pattern, text)
        
        return matches[:10]  # Limit to 10 considerations
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured JSON from Gemini response using multiple methods
        Validates each extraction before returning
        """
        extraction_methods = []
        
        # Method 1: Look for JSON in code blocks (most reliable)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            extraction_methods.append(("code_block", json_str))
        
        # Method 2: Find JSON after "```json" marker
        json_start = text.find('```json')
        if json_start != -1:
            json_end = text.find('```', json_start + 7)
            if json_end != -1:
                json_str = text[json_start + 7:json_end].strip()
                extraction_methods.append(("json_marker", json_str))
        
        # Method 3: Find JSON object at the end of text (common pattern)
        # Look for the last complete JSON object
        lines = text.split('\n')
        json_lines = []
        brace_count = 0
        in_json = False
        
        for line in reversed(lines):
            if '{' in line or '}' in line:
                json_lines.insert(0, line)
                brace_count += line.count('{') - line.count('}')
                if brace_count > 0:
                    in_json = True
                if brace_count == 0 and in_json:
                    break
        
        if json_lines:
            json_str = '\n'.join(json_lines)
            extraction_methods.append(("end_of_text", json_str))
        
        # Method 4: Try to find largest JSON object (fallback)
        json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            extraction_methods.append(("regex_fallback", json_str))
        
        # Try each extraction method and validate
        for method_name, json_str in extraction_methods:
            try:
                parsed_json = json.loads(json_str)
                # Basic validation: check if it's a dict
                if isinstance(parsed_json, dict):
                    logger.info(f"Successfully extracted JSON using method: {method_name}")
                    return parsed_json
            except json.JSONDecodeError as e:
                logger.debug(f"Method {method_name} failed: {e}")
                continue
        
        logger.warning("All JSON extraction methods failed")
        return None
    
    def _validate_json_schema(self, data: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Validate JSON structure against expected schema
        Returns validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        # Required top-level fields
        required_fields = ["decision_summary"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate decision_summary
        if "decision_summary" in data:
            ds = data["decision_summary"]
            if not isinstance(ds, dict):
                errors.append("decision_summary must be an object")
            else:
                if "description" not in ds or not ds.get("description"):
                    warnings.append("decision_summary.description is missing or empty")
        
        # Validate key_metrics (optional but should be object if present)
        if "key_metrics" in data:
            if not isinstance(data["key_metrics"], dict):
                errors.append("key_metrics must be an object")
            else:
                # Validate each metric has required fields
                for metric_name, metric_data in data["key_metrics"].items():
                    if not isinstance(metric_data, dict):
                        warnings.append(f"Metric {metric_name} is not an object")
                    elif "value" not in metric_data:
                        warnings.append(f"Metric {metric_name} missing 'value' field")
        
        # Validate critical_factors (optional but should be array if present)
        if "critical_factors" in data:
            if not isinstance(data["critical_factors"], list):
                errors.append("critical_factors must be an array")
            else:
                for i, factor in enumerate(data["critical_factors"]):
                    if not isinstance(factor, dict):
                        warnings.append(f"critical_factors[{i}] is not an object")
                    elif "factor" not in factor or "description" not in factor:
                        warnings.append(f"critical_factors[{i}] missing required fields")
        
        # Validate scenarios (optional but should be object if present)
        if "scenarios" in data:
            if not isinstance(data["scenarios"], dict):
                errors.append("scenarios must be an object")
        
        # Validate recommended_actions (optional but should be array if present)
        if "recommended_actions" in data:
            if not isinstance(data["recommended_actions"], list):
                errors.append("recommended_actions must be an array")
            else:
                for i, action in enumerate(data["recommended_actions"]):
                    if not isinstance(action, dict):
                        warnings.append(f"recommended_actions[{i}] is not an object")
                    elif "action" not in action:
                        warnings.append(f"recommended_actions[{i}] missing 'action' field")
        
        # Validate hypotheses (optional but should be array if present)
        if "hypotheses" in data:
            if not isinstance(data["hypotheses"], list):
                errors.append("hypotheses must be an array")
            else:
                for i, hyp in enumerate(data["hypotheses"]):
                    if not isinstance(hyp, dict):
                        warnings.append(f"hypotheses[{i}] is not an object")
                    elif not all(k in hyp for k in ["id", "label", "value", "type"]):
                        warnings.append(f"hypotheses[{i}] missing required fields (id, label, value, type)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "has_critical_errors": len(errors) > 0
        }
    
    async def _validate_and_fix_json(
        self, 
        extracted_json: Dict[str, Any], 
        original_text: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Validate extracted JSON and fix it using Gemini if needed
        Returns corrected JSON or original if validation passes
        """
        validation_result = self._validate_json_schema(extracted_json, question)
        
        if validation_result["valid"] and len(validation_result["warnings"]) == 0:
            logger.info("JSON validation passed - no fixes needed")
            return extracted_json
        
        # Log issues
        if validation_result["errors"]:
            logger.warning(f"JSON validation errors: {validation_result['errors']}")
        if validation_result["warnings"]:
            logger.info(f"JSON validation warnings: {validation_result['warnings']}")
        
        # If only warnings (no critical errors), return as-is
        if validation_result["valid"]:
            logger.info("JSON has warnings but is valid - returning as-is")
            return extracted_json
        
        # Critical errors detected - try to fix with Gemini
        logger.info("Attempting to fix JSON using Gemini...")
        
        try:
            fix_prompt = f"""Le JSON suivant extrait d'une analyse financière contient des erreurs. Corrige-le pour qu'il soit valide et complet.

Question originale: {question}

JSON à corriger:
```json
{json.dumps(extracted_json, indent=2, ensure_ascii=False)}
```

Erreurs détectées:
{chr(10).join(f"- {error}" for error in validation_result['errors'])}

Instructions:
1. Corrige toutes les erreurs listées
2. Assure-toi que le JSON est valide et complet
3. Conserve toutes les données existantes valides
4. Ajoute les champs manquants avec des valeurs appropriées basées sur le contexte
5. Retourne UNIQUEMENT le JSON corrigé, sans texte supplémentaire

Format attendu:
- decision_summary: {{ description: string, importance: string }}
- key_metrics: {{ [metric_name]: {{ value: string|number, unit?: string, period?: string, description?: string }} }}
- critical_factors: [{{ number: number, factor: string, description: string }}]
- scenarios: {{ optimistic?: {{ description: string }}, realistic?: {{ description: string }}, pessimistic?: {{ description: string }} }}
- recommended_actions: [{{ priority: "critical"|"important"|"recommended", action: string, impact?: string }}]
- alternatives: [{{ name: string, description: string, impact?: string }}]
- hypotheses: [{{ id: string, label: string, value: number|string, type: "number"|"date" }}]

JSON corrigé:"""
            
            response = self.gemini_service.model_normal.generate_content(fix_prompt)
            fixed_text = ""
            if response.candidates and len(response.candidates) > 0:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        fixed_text += part.text
            
            # Extract JSON from fixed response
            fixed_json = self._extract_json_from_response(fixed_text)
            
            if fixed_json:
                # Validate the fixed JSON
                fixed_validation = self._validate_json_schema(fixed_json, question)
                if fixed_validation["valid"]:
                    logger.info("Successfully fixed JSON using Gemini")
                    return fixed_json
                else:
                    logger.warning(f"Fixed JSON still has errors: {fixed_validation['errors']}")
                    # Return original with errors logged
                    return extracted_json
            else:
                logger.warning("Could not extract JSON from Gemini fix response")
                return extracted_json
                
        except Exception as e:
            logger.error(f"Error fixing JSON with Gemini: {e}", exc_info=True)
            return extracted_json
    
    async def _format_comprehensive_results(
        self,
        question: str,
        comprehensive_result: Dict[str, Any],
        requirements: Dict[str, Any],
        availability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format single comprehensive analysis result into structured output
        
        Args:
            question: Original question
            comprehensive_result: Result from single comprehensive pass
            requirements: Requirements dict
            availability: Availability status
            
        Returns:
            Formatted results dict matching expected structure
        """
        analysis_text = comprehensive_result.get("analysis_text", "")
        execution_outputs = comprehensive_result.get("execution_outputs", [])
        charts = comprehensive_result.get("chart_files", [])
        
        # Log what we received for debugging
        logger.info(f"Formatting comprehensive results - Analysis text length: {len(analysis_text)}")
        logger.info(f"Analysis text preview: {analysis_text[:500]}...")
        logger.info(f"Execution outputs count: {len(execution_outputs)}")
        
        # Try to extract structured JSON first (more reliable than regex)
        extracted_json = self._extract_json_from_response(analysis_text)
        
        # Validate and fix JSON if needed
        structured_data = None
        if extracted_json:
            structured_data = await self._validate_and_fix_json(extracted_json, analysis_text, question)
        
        decision_summary_from_json = {}
        if structured_data:
            logger.info("Found and validated structured JSON in response - using it for extraction")
            # Use JSON data if available - convert to expected format
            key_metrics_dict = structured_data.get("key_metrics", {})
            # Convert JSON metrics to expected format
            key_metrics = {}
            for metric_name, metric_data in key_metrics_dict.items():
                if isinstance(metric_data, dict):
                    # Translate English metric names to French
                    french_name = self._translate_metric_name(metric_name)
                    
                    # Skip metrics with "Needs Data" or empty values
                    value = metric_data.get("value", "")
                    if isinstance(value, str) and ("needs data" in value.lower() or value.strip() == ""):
                        logger.info(f"Skipping metric {metric_name} with 'Needs Data' or empty value")
                        continue
                    
                    key_metrics[french_name] = {
                        "value": str(value),
                        "unit": metric_data.get("unit", ""),
                        "description": self._translate_text(metric_data.get("description", "")),
                        "period": metric_data.get("period", "")
                    }
            
            critical_factors = structured_data.get("critical_factors", [])
            # Translate factor names and descriptions to French if needed
            if critical_factors:
                for factor in critical_factors:
                    if isinstance(factor, dict):
                        if "factor" in factor:
                            factor["factor"] = self._translate_text(factor["factor"])
                        if "description" in factor:
                            factor["description"] = self._translate_text(factor["description"])
            
            current_context = structured_data.get("current_context", {})
            scenarios = structured_data.get("scenarios", {})
            recommended_actions = structured_data.get("recommended_actions", [])
            alternatives = structured_data.get("alternatives", [])
            
            # Store decision summary from JSON
            decision_summary_from_json = structured_data.get("decision_summary", {})
        else:
            logger.info("No structured JSON found - falling back to regex extraction")
            decision_summary_from_json = {}
            # Fallback to regex extraction if no JSON found
            key_metrics = self._extract_key_metrics(analysis_text, execution_outputs)
            critical_factors = self._extract_critical_factors_from_comprehensive(analysis_text)
            current_context = self._extract_current_context_from_comprehensive(analysis_text)
            scenarios = self._extract_scenarios_from_comprehensive(analysis_text)
            recommended_actions = self._extract_recommendations_from_comprehensive(analysis_text)
            alternatives = self._extract_alternatives_from_comprehensive(analysis_text)
        
        # Check if extraction found little content (potential issues)
        has_extraction_issues = (
            len(key_metrics) == 0 or 
            len(critical_factors) == 0 or
            (isinstance(current_context, dict) and len(current_context.get("strengths", [])) == 0 and len(current_context.get("weaknesses", [])) == 0)
        )
        
        if has_extraction_issues:
            logger.warning(f"Extraction issues detected: metrics={len(key_metrics)}, factors={len(critical_factors)}, context={current_context}")
        
        # IMPORTANT: ALWAYS save full analysis text for display
        # This ensures we don't lose any generated content even if extraction fails
        
        # Check for missing data requests (light logic)
        missing_count = len(availability.get("missing", []))
        critical_missing_count = len([r for r in availability.get("missing", []) if r.get("critical", False)])
        should_request_data = missing_count >= 3 or critical_missing_count >= 2
        
        missing_data_requests = []
        if should_request_data and missing_count > 0:
            missing_data_requests.append({
                "step": "comprehensive",
                "step_name": "Comprehensive Analysis",
                "missing_requirements": availability.get("missing", [])[:3],  # Limit to 3
                "why_important": "Additional data would improve analysis precision",
                "can_skip": True,
                "request_priority": "high" if critical_missing_count >= 2 else "medium"
            })
        
        # Get decision summary from JSON if available, otherwise from requirements
        decision_summary_data = requirements.get("decision_summary", {})
        if decision_summary_from_json:
            decision_summary_data = decision_summary_from_json
        
        # Extract hypotheses from structured data if available
        hypotheses = []
        if structured_data and "hypotheses" in structured_data:
            hypotheses = structured_data["hypotheses"]
        elif decision_summary_from_json and "hypotheses" in decision_summary_from_json:
            hypotheses = decision_summary_from_json["hypotheses"]
        
        # Extract report_structure from structured data if available
        report_structure = None
        if structured_data and "report_structure" in structured_data:
            report_structure = structured_data["report_structure"]
            # Validate report_structure
            if isinstance(report_structure, dict):
                # Ensure sections_order exists
                if "sections_order" not in report_structure:
                    report_structure["sections_order"] = []
                # Ensure sections_config exists
                if "sections_config" not in report_structure:
                    report_structure["sections_config"] = {}
                # Ensure custom_sections exists
                if "custom_sections" not in report_structure:
                    report_structure["custom_sections"] = []
            else:
                report_structure = None
        
        # Generate default report_structure if not provided
        if not report_structure:
            # Determine which sections have data
            available_sections = []
            if decision_summary_data.get("description") or decision_summary_data.get("importance"):
                available_sections.append("decision_summary")
            if key_metrics:
                available_sections.append("key_metrics")
            if critical_factors:
                available_sections.append("critical_factors")
            if current_context and (current_context.get("strengths") or current_context.get("weaknesses")):
                available_sections.append("current_context")
            if scenarios:
                available_sections.append("scenarios")
            if recommended_actions:
                available_sections.append("recommended_actions")
            if alternatives:
                available_sections.append("alternatives")
            
            report_structure = {
                "sections_order": available_sections,
                "sections_config": {
                    section: {"visible": True} for section in available_sections
                },
                "custom_sections": []
            }
        
        formatted_results = {
            "analysis_type": "fast_comprehensive",
            "decision_summary": {
                "question": question,
                "description": decision_summary_data.get("description", ""),
                "importance": decision_summary_data.get("importance", "")
            },
            "key_metrics": key_metrics,
            "critical_factors": critical_factors,
            "current_context": current_context,
            "scenarios": scenarios,
            "recommended_actions": recommended_actions,
            "alternatives": alternatives,
            "charts": charts,
            "hypotheses": hypotheses,  # Add hypotheses to the result
            "report_structure": report_structure,  # Add report structure
            "missing_data_requests": missing_data_requests,
            "full_analysis_text": analysis_text,  # ALWAYS save full text
            "execution_outputs": execution_outputs,  # Save for debugging
            "has_extraction_issues": has_extraction_issues,  # Flag for display logic
            "raw_results": comprehensive_result  # Keep for debugging
        }
        
        # Validate quality and add quality metrics
        quality_validation = self._validate_analysis_quality(formatted_results, question)
        formatted_results["quality_metrics"] = quality_validation
        
        # Log quality issues if any
        if quality_validation["needs_improvement"]:
            logger.warning(f"Analysis quality needs improvement (score: {quality_validation['quality_score']})")
            logger.info(f"Quality issues: {quality_validation['issues']}")
        
        return formatted_results
    
    def _extract_critical_factors_from_comprehensive(self, text: str) -> List[Dict[str, Any]]:
        """Extract critical factors from comprehensive analysis text - enhanced to capture full descriptions"""
        factors = []
        
        logger.info("Extracting critical factors from analysis text")
        
        # Look for numbered factors section with more flexible patterns
        factors_section_patterns = [
            r'(?:critical factors?|ce qu.*prendre en compte|facteurs? critiques?)[^\n]*\n((?:\d+\.\s*[^\n]+\n[^\n]+(?:\n[^\n]+)*?\n?)+)',
            r'(?:avant de valider|factors? to consider)[^\n]*\n((?:\d+\.\s*[^\n]+\n[^\n]+(?:\n[^\n]+)*?\n?)+)',
            r'(\d+\.\s*[^\n]+\n[^\n]+(?:\n[^\n]+)*?)(?=\n\d+\.|\n(?:scenario|contexte|recommendations?|\*\*[A-Z])|\Z)'
        ]
        
        factors_text = None
        for pattern in factors_section_patterns:
            factors_section = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if factors_section:
                factors_text = factors_section.group(1)
                logger.info(f"Found factors section with pattern: {pattern[:50]}...")
                break
        
        if factors_text:
            # Extract numbered factors with full descriptions (capture multiple paragraphs)
            # Pattern matches: number. factor_name\nfull_description (until next number or section header)
            factor_pattern = r'(\d+)\.\s*([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n\d+\.|\n(?:scenario|contexte|recommendations?|chart|graph|\*\*[A-Z])|\Z)'
            matches = re.findall(factor_pattern, factors_text, re.MULTILINE | re.DOTALL)
            
            for match in matches[:5]:
                description = match[2].strip()
                # Preserve paragraph structure - normalize spaces but keep newlines
                description = re.sub(r'[ \t]+', ' ', description)  # Normalize spaces/tabs
                description = re.sub(r'\n{3,}', '\n\n', description)  # Max 2 consecutive newlines
                
                factors.append({
                    "number": int(match[0]),
                    "factor": match[1].strip(),
                    "description": description  # Keep full description with paragraphs
                })
        
        # Also try to extract factors with title format (English: "Current Cash Position:", etc.)
        if not factors:
            logger.info("No numbered factors found, trying title-based extraction")
            # Look for factors section
            factors_section = re.search(
                r'(?:critical factors?|ce qu.*prendre en compte|facteurs? critiques?)[^\n]*\n(.*?)(?=\n(?:scenarios?|current|recommendations?|alternatives?|\*\*[A-Z]|\Z))',
                text,
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            
            if factors_section:
                factors_text = factors_section.group(1)
                # Extract factors with title format: "Title:\nDescription"
                title_factor_pattern = r'([A-Z][^:\n]+):\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n[A-Z][^:\n]+:|\n(?:scenario|current|recommendations?|alternatives?|\*\*[A-Z])|\Z)'
                matches = re.findall(title_factor_pattern, factors_text, re.MULTILINE | re.DOTALL)
                
                for idx, match in enumerate(matches[:5], 1):
                    factor_name = match[0].strip()
                    description = match[1].strip()
                    description = re.sub(r'[ \t]+', ' ', description)
                    description = re.sub(r'\n{3,}', '\n\n', description)
                    
                    factors.append({
                        "number": idx,
                        "factor": factor_name,
                        "description": description
                    })
        
        # Fallback: try to find numbered factors anywhere in text
        if not factors:
            logger.info("No factors section found, trying fallback pattern")
            factor_pattern = r'(\d+)\.\s*([^\n]+)\n([^\n]+(?:\n[^\n]+){0,3}?)(?=\n\d+\.|\n(?:scenario|contexte|recommendations?|chart|graph|\*\*[A-Z])|\Z)'
            matches = re.findall(factor_pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches[:5]:
                description = match[2].strip()
                description = re.sub(r'[ \t]+', ' ', description)
                description = re.sub(r'\n{3,}', '\n\n', description)
                
                factors.append({
                    "number": int(match[0]),
                    "factor": match[1].strip(),
                    "description": description
                })
        
        logger.info(f"Extracted {len(factors)} critical factors")
        if not factors:
            logger.warning("No critical factors extracted! Text may not match expected format.")
        
        return factors
    
    def _extract_current_context_from_comprehensive(self, text: str) -> Dict[str, Any]:
        """Extract current context from comprehensive analysis - enhanced with French patterns"""
        strengths = []
        weaknesses = []
        
        logger.info("Extracting current context from analysis text")
        
        # Extract strengths (multiple patterns in French and English)
        strengths_patterns = [
            r'(?:strengths?|points? forts?|forces?)[^\n]*\n((?:[-•*]|\d+\.)\s*[^\n]+\n?)+',
            r'points?\s+forts[^\n]*\n((?:[-•*]|\d+\.)\s*[^\n]+\n?)+',
            r'trésorerie.*saine[^\n]*([0-9,\.]+)\s*([€$kK]?)',  # Extract specific metrics
        ]
        
        for pattern in strengths_patterns:
            strengths_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if strengths_match:
                if len(strengths_match.groups()) > 1:
                    # Pattern matched a specific metric
                    value = strengths_match.group(1)
                    unit = strengths_match.group(2) if len(strengths_match.groups()) > 1 else ""
                    strengths.append(f"Trésorerie saine : {value}{unit}")
                else:
                    # Pattern matched a list
                    strengths_text = strengths_match.group(1)
                    strength_items = re.findall(r'(?:[-•*]|\d+\.)\s*([^\n]+)', strengths_text)
                    strengths.extend([s.strip() for s in strength_items if s.strip()])
                break
        
        # Also look for English format: "Points forts:" followed by list items
        if not strengths:
            strengths_section = re.search(
                r'points?\s+forts[^\n]*\n(.*?)(?=\n(?:points?\s+d.*attention|weaknesses?|scenarios?|recommendations?|\*\*[A-Z]|\Z))',
                text,
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            if strengths_section:
                strengths_text = strengths_section.group(1)
                # Extract items (can be bullet points or plain lines)
                strength_items = re.findall(r'(?:[-•*]|\d+\.)?\s*([^\n]+)', strengths_text)
                strengths.extend([s.strip() for s in strength_items if s.strip() and len(s.strip()) > 3])
        
        # Also look for specific metrics mentioned in text
        if not strengths:
            # Look for "Trésorerie saine : 45k€" pattern
            cash_match = re.search(r'trésorerie.*saine[^\n]*([0-9,\.]+)\s*([€$kK]?)', text, re.IGNORECASE)
            if cash_match:
                strengths.append(f"Trésorerie saine : {cash_match.group(1)}{cash_match.group(2) or '€'}")
        
        # Extract weaknesses (multiple patterns in French and English)
        weaknesses_patterns = [
            r'(?:weaknesses?|points? d.*attention|fragilités?|concerns?)[^\n]*\n((?:[-•*]|\d+\.)\s*[^\n]+\n?)+',
            r'points?\s+d.*attention[^\n]*\n((?:[-•*]|\d+\.)\s*[^\n]+\n?)+',
            r'(?:rotation|délais|marge)[^\n]*([0-9,\.]+)\s*(?:jours|%|€)',  # Extract specific metrics
        ]
        
        for pattern in weaknesses_patterns:
            weaknesses_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if weaknesses_match:
                if 'rotation' in pattern.lower() or 'délais' in pattern.lower() or 'marge' in pattern.lower():
                    # Pattern matched a specific metric
                    metric_name = weaknesses_match.group(0).split(':')[0] if ':' in weaknesses_match.group(0) else ""
                    value = weaknesses_match.group(1) if len(weaknesses_match.groups()) > 0 else ""
                    unit = re.search(r'(jours|%|€)', weaknesses_match.group(0), re.IGNORECASE)
                    unit_str = unit.group(1) if unit else ""
                    if metric_name and value:
                        weaknesses.append(f"{metric_name.strip()} : {value} {unit_str}".strip())
                else:
                    # Pattern matched a list
                    weaknesses_text = weaknesses_match.group(1)
                    weakness_items = re.findall(r'(?:[-•*]|\d+\.)\s*([^\n]+)', weaknesses_text)
                    weaknesses.extend([w.strip() for w in weakness_items if w.strip()])
                break
        
        # Also look for English format: "Points d'attention:" followed by list items
        if not weaknesses:
            weaknesses_section = re.search(
                r'points?\s+d.*attention[^\n]*\n(.*?)(?=\n(?:points?\s+forts|strengths?|scenarios?|recommendations?|\*\*[A-Z]|\Z))',
                text,
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            if weaknesses_section:
                weaknesses_text = weaknesses_section.group(1)
                # Extract items (can be bullet points or plain lines)
                weakness_items = re.findall(r'(?:[-•*]|\d+\.)?\s*([^\n]+)', weaknesses_text)
                weaknesses.extend([w.strip() for w in weakness_items if w.strip() and len(w.strip()) > 3])
        
        # Also look for specific metrics mentioned in text
        if not weaknesses:
            # Look for "Rotation stocks : 60 jours" pattern
            rotation_match = re.search(r'rotation.*stocks[^\n]*([0-9,\.]+)\s*(jours|days)', text, re.IGNORECASE)
            if rotation_match:
                weaknesses.append(f"Rotation stocks : {rotation_match.group(1)} jours")
            
            delays_match = re.search(r'délais.*clients[^\n]*([0-9,\.]+)\s*(jours|days)', text, re.IGNORECASE)
            if delays_match:
                weaknesses.append(f"Délais clients : {delays_match.group(1)} jours")
            
            margin_match = re.search(r'marge.*brute[^\n]*([0-9,\.]+)\s*%', text, re.IGNORECASE)
            if margin_match:
                weaknesses.append(f"Marge brute : {margin_match.group(1)}%")
        
        # Extract summary
        summary_patterns = [
            r'(?:summary|contexte|situation|dans ce contexte)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenarios?|recommendations?|alternatives?|\*\*[A-Z]|\Z))',
            r'dans ce contexte[^\n]*([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenarios?|recommendations?|alternatives?|\*\*[A-Z]|\Z))',
        ]
        summary = ""
        for pattern in summary_patterns:
            summary_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()[:500]
                break
        
        logger.info(f"Extracted {len(strengths)} strengths and {len(weaknesses)} weaknesses")
        if not strengths and not weaknesses:
            logger.warning("No strengths/weaknesses extracted! Text may not match expected format.")
        
        return {
            "status": "completed",
            "strengths": strengths[:5],  # Limit to 5
            "weaknesses": weaknesses[:5],  # Limit to 5
            "summary": summary
        }
    
    def _extract_scenarios_from_comprehensive(self, text: str) -> Dict[str, Any]:
        """Extract scenarios from comprehensive analysis - enhanced to capture full narrative descriptions"""
        scenarios = {}
        
        logger.info("Extracting scenarios from analysis text")
        
        # Extract each scenario with FULL narrative descriptions (preserve paragraphs)
        scenario_patterns = {
            "optimistic": [
                # Match "Scénario Optimiste:" or "**Scénario Optimiste:**" followed by full description
                r'(?:scenario|scénario)\s+optimistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|realistic|pessimistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'\*\*scénario\s+optimiste\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|realistic|pessimistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'optimistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:realistic|pessimistic|scenario|meilleur|pire|\*\*[A-Z]|\Z))',
                r'best case[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:realistic|pessimistic|scenario|worst|pire|\*\*[A-Z]|\Z))'
            ],
            "realistic": [
                r'(?:scenario|scénario)\s+realistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|optimistic|pessimistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'\*\*scénario\s+réaliste\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|optimistic|pessimistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'realistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|pessimistic|scenario|meilleur|pire|\*\*[A-Z]|\Z))',
                r'most likely[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|pessimistic|scenario|worst|pire|\*\*[A-Z]|\Z))'
            ],
            "pessimistic": [
                r'(?:scenario|scénario)\s+pessimistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|optimistic|realistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'\*\*scénario\s+pessimiste\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:scenario|scénario|optimistic|realistic|meilleur|pire|\*\*[A-Z]|\Z))',
                r'pessimistic[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|realistic|scenario|meilleur|pire|\*\*[A-Z]|\Z))',
                r'worst case[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:optimistic|realistic|scenario|best|meilleur|\*\*[A-Z]|\Z))'
            ]
        }
        
        for scenario_name, patterns in scenario_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if match:
                    description = match.group(1).strip()
                    # Preserve paragraph structure - only normalize excessive whitespace, keep newlines
                    # Remove multiple consecutive spaces but keep single newlines
                    description = re.sub(r'[ \t]+', ' ', description)  # Normalize spaces/tabs
                    description = re.sub(r'\n{3,}', '\n\n', description)  # Max 2 consecutive newlines
                    # Don't collapse all whitespace - preserve narrative structure
                    
                    # Extract milestones and risk periods from the full description
                    milestones = []
                    risk_periods = []
                    
                    # Look for milestones in narrative (e.g., "trésorerie remonte à 50k€ en juin" or "cash flow improves")
                    milestone_pattern = r'(?:trésorerie|cash|ca|revenu|revenue|flow).*?(?:remonte|monte|atteint|arrive|génère|improves?|reaches?|exceeds?)\s*(?:à|à|to)?\s*([0-9,\.]+)\s*([€$kK]?).*?(?:en|in|à|dès|début|fin|within|after|months?|mois)?'
                    milestone_matches = re.findall(milestone_pattern, description, re.IGNORECASE)
                    for m in milestone_matches[:5]:  # Capture more milestones
                        milestones.append(f"{m[0]}{m[1]}")
                    
                    # Look for risk periods (e.g., "trésorerie sous les 10k€ en mars-avril" or "cash flow remains constrained")
                    risk_pattern = r'(?:trésorerie|cash|flow).*?(?:sous|under|below|minimale|minimal|constrained|remains?)\s*(?:les|the)?\s*([0-9,\.]+)\s*([€$kK]?).*?(?:en|in|à|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|months?)?'
                    risk_matches = re.findall(risk_pattern, description, re.IGNORECASE)
                    for r in risk_matches[:5]:  # Capture more risk periods
                        risk_periods.append(f"{r[0]}{r[1]}")
                    
                    scenarios[scenario_name] = {
                        "description": description,  # Keep full narrative
                        "key_milestones": milestones,
                        "risk_periods": risk_periods
                    }
                    break
        
        # Extract best/worst case summaries with better patterns
        best_patterns = [
            r'(?:best case|meilleur cas)[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:worst|pire|scenario|\*\*[A-Z]|\Z))',
            r'\*\*meilleur cas\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:worst|pire|scenario|\*\*[A-Z]|\Z))'
        ]
        for pattern in best_patterns:
            best_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if best_match:
                scenarios["best_case"] = best_match.group(1).strip()
                break
        
        worst_patterns = [
            r'(?:worst|pire) case[^\n]*:?\s*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:best|meilleur|scenario|\*\*[A-Z]|\Z))',
            r'\*\*pire cas\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:best|meilleur|scenario|\*\*[A-Z]|\Z))'
        ]
        for pattern in worst_patterns:
            worst_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if worst_match:
                scenarios["worst_case"] = worst_match.group(1).strip()
                break
        
        logger.info(f"Extracted scenarios: {list(scenarios.keys())}")
        if not scenarios:
            logger.warning("No scenarios extracted! Text may not match expected format.")
        
        return scenarios
    
    def _translate_metric_name(self, name: str) -> str:
        """Translate English metric names to French"""
        translations = {
            "total_cost": "coût_total",
            "payback_period": "période_de_retour",
            "operating_costs": "coûts_exploitation",
            "break_even_point": "seuil_de_rentabilité",
            "return_on_investment": "retour_sur_investissement",
            "estimated_increase_in_revenue": "augmentation_estimée_revenus",
            "estimated_increase_in_production": "augmentation_estimée_production",
            "cash_impact": "impact_trésorerie",
            "gain_mensuel": "gain_mensuel",
            "coût_mensuel": "coût_mensuel",
        }
        
        # If already in French or not in translation dict, return as-is
        if name in translations:
            return translations[name]
        
        # If name contains underscores and looks English, try to translate common words
        if "_" in name:
            parts = name.split("_")
            translated_parts = []
            for part in parts:
                if part in translations:
                    translated_parts.append(translations[part])
                else:
                    translated_parts.append(part)
            return "_".join(translated_parts)
        
        return name
    
    def _translate_text(self, text: str) -> str:
        """Translate common English phrases to French in text"""
        if not text:
            return text
        
        # Common translations for factor names and descriptions
        translations = {
            "Increase in production and sales estimation": "Estimation de l'augmentation de production et de ventes",
            "Operating Costs": "Coûts d'exploitation",
            "Existing Cash Flow and Financial Stability": "Trésorerie existante et stabilité financière",
            "increase in production": "augmentation de production",
            "operating costs": "coûts d'exploitation",
            "cash flow": "trésorerie",
            "financial stability": "stabilité financière",
        }
        
        # Check if entire text matches a translation
        if text in translations:
            return translations[text]
        
        # Try to translate parts of the text
        translated = text
        for english, french in translations.items():
            if english.lower() in translated.lower():
                translated = translated.replace(english, french)
                translated = translated.replace(english.lower(), french.lower())
                translated = translated.replace(english.capitalize(), french)
        
        return translated
    
    def _clean_action_text(self, text: str) -> str:
        """Clean action text by removing markdown artifacts and section markers"""
        if not text:
            return ""
        
        # CRITICAL: Stop at section boundaries - remove everything after section markers
        section_markers = [
            r'\*\*\d+\.\s*STRATEGIC\s+ALTERNATIVES?\*\*',
            r'\*\*\d+\.\s*ALTERNATIVES?\s+STRATÉGIQUES?\*\*',
            r'\*\*\d+\.\s*CHARTS?\*\*',
            r'\*\*\d+\.\s*GRAPH\w*\*\*',
            r'STRATEGIC\s+ALTERNATIVES?:',
            r'ALTERNATIVES?\s+STRATÉGIQUES?:',
            r'CHARTS?:',
            r'GRAPH\w*:',
            r'\*\*Alternative\s+\d+:',
            r'Alternative\s+\d+:',
            r'Impact\s+tréso:',  # This is for alternatives, not actions
        ]
        
        # Find the earliest section marker and cut everything after it
        earliest_pos = len(text)
        for marker in section_markers:
            match = re.search(marker, text, re.IGNORECASE)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
        
        if earliest_pos < len(text):
            text = text[:earliest_pos]
        
        # Remove section markers that might still be in the text
        text = re.sub(r'\*\*\d+\.\s*[A-Z\s]+\*\*', '', text)
        text = re.sub(r'\*\*[A-Z\s]+\*\*', '', text)
        text = re.sub(r'\*\*Recommandé\*\*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*', '', text)
        
        # Remove common section prefixes
        text = re.sub(r'^\d+\.\s*', '', text)  # Remove numbered prefixes
        text = re.sub(r'^[-•*]\s*', '', text)  # Remove bullet points
        
        # Remove any remaining section markers
        for marker in section_markers:
            text = re.sub(marker + r'.*$', '', text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        # Remove "Impact tréso:" patterns that might have been included
        text = re.sub(r'Impact\s+tréso:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up whitespace and trailing punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*[.*]\s*$', '', text)  # Remove trailing dots/asterisks
        text = text.strip()
        
        return text
    
    def _extract_recommendations_from_comprehensive(self, text: str) -> List[Dict[str, Any]]:
        """Extract recommendations from comprehensive analysis - enhanced to capture full descriptions"""
        actions = []
        
        # Extract by priority sections with more flexible patterns
        # Pattern 1: **Critique** followed by action and impact on separate lines
        # Pattern 2: Critical: followed by bullet points
        # Pattern 3: **Critique (Must Do):** format
        
        priority_patterns = {
            "critical": [
                r'\*\*critique\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n\*\*(?:important|recommended|alternative)|\Z)',
                r'(?:critical|critique)[^\n]*\n((?:[-•*]?\s*[^\n]+\n(?:\s*(?:impact|libère|gain|will|help|potentially)[:\s]+[^\n]+\n?)*)+)',
                r'(?:critical|critique)[^\n]*\n((?:[-•*]?\s*[^\n]+(?:\n[^\n]+)*?)+)(?=\n(?:important|recommended|alternative|\*\*[A-Z])|\Z)',
                # Also match plain text format: "Critique\nAction text\nImpact text"
                r'(?:critical|critique)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:important|recommended|alternative|\*\*[A-Z])|\Z)'
            ],
            "important": [
                r'\*\*important\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n\*\*(?:critical|recommended|alternative)|\Z)',
                r'(?:important)[^\n]*\n((?:[-•*]?\s*[^\n]+\n(?:\s*(?:impact|libère|gain|will|help|potentially)[:\s]+[^\n]+\n?)*)+)',
                r'(?:important)[^\n]*\n((?:[-•*]?\s*[^\n]+(?:\n[^\n]+)*?)+)(?=\n(?:critical|recommended|alternative|\*\*[A-Z])|\Z)',
                # Also match plain text format
                r'(?:important)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:critical|recommended|alternative|\*\*[A-Z])|\Z)'
            ],
            "recommended": [
                r'\*\*(?:recommended|recommandé)\*\*[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n\*\*(?:critical|important|alternative)|\Z)',
                r'(?:recommended|recommandé)[^\n]*\n((?:[-•*]?\s*[^\n]+\n(?:\s*(?:impact|libère|gain|meilleure|will|help|potentially)[:\s]+[^\n]+\n?)*)+)',
                r'(?:recommended|recommandé)[^\n]*\n((?:[-•*]?\s*[^\n]+(?:\n[^\n]+)*?)+)(?=\n(?:critical|important|alternative|\*\*[A-Z])|\Z)',
                # Also match plain text format
                r'(?:recommended|recommandé)[^\n]*\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:critical|important|alternative|\*\*[A-Z])|\Z)'
            ]
        }
        
        for priority, patterns in priority_patterns.items():
            for pattern in patterns:
                section_match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if section_match:
                    section_text = section_match.group(1).strip()
                    
                    # Stop extraction at section boundaries (alternatives, charts, etc.)
                    stop_markers = [
                        r'\*\*\d+\.\s*STRATEGIC\s+ALTERNATIVES?\*\*',
                        r'\*\*\d+\.\s*ALTERNATIVES?\s+STRATÉGIQUES?\*\*',
                        r'\*\*\d+\.\s*CHARTS?\*\*',
                        r'\*\*\d+\.\s*GRAPH\w*\*\*',
                        r'STRATEGIC\s+ALTERNATIVES?:',
                        r'ALTERNATIVES?\s+STRATÉGIQUES?:',
                        r'CHARTS?:',
                        r'GRAPH\w*:',
                    ]
                    
                    for marker in stop_markers:
                        marker_match = re.search(marker, section_text, re.IGNORECASE)
                        if marker_match:
                            section_text = section_text[:marker_match.start()].strip()
                            break
                    
                    # Clean up markdown artifacts and section markers
                    section_text = re.sub(r'\*\*\d+\.\s*[A-Z\s]+\*\*', '', section_text)  # Remove section headers
                    section_text = re.sub(r'\*\*[A-Z\s]+\*\*', '', section_text)  # Remove bold headers
                    section_text = re.sub(r'\*\*Recommandé\*\*', '', section_text, flags=re.IGNORECASE)  # Remove "Recommandé" markers
                    section_text = re.sub(r'\*\*', '', section_text)  # Remove remaining bold markers
                    
                    # Try to extract individual actions from the section
                    # Split by lines and group action + impact pairs
                    lines = section_text.split('\n')
                    current_action = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Skip lines that are clearly section markers or not actions
                        if any(skip in line.upper() for skip in ['STRATEGIC ALTERNATIVES', 'ALTERNATIVES STRATÉGIQUES', 'CHARTS', 'GRAPH', 'SCENARIOS', 'MÉTRIQUES']):
                            break
                        
                        # Check if this line is an action (starts with action keywords or is a sentence)
                        action_keywords = ['implement', 'negotiate', 'secure', 'develop', 'consolidate', 'négocier', 'mettre', 'établir', 'créer', 'améliorer']
                        if any(keyword in line.lower() for keyword in action_keywords):
                            # Save previous action if exists
                            if current_action and len(current_action.get('action', '')) > 5:
                                # Clean action text before saving
                                current_action["action"] = self._clean_action_text(current_action["action"])
                                actions.append(current_action)
                            
                            # Start new action
                            action_text = re.sub(r'^[-•*]\s*', '', line)  # Remove bullet
                            action_text = self._clean_action_text(action_text)
                            current_action = {
                                "priority": priority,
                                "action": action_text,
                                "impact": None
                            }
                        elif current_action and any(keyword in line.lower() for keyword in ['impact', 'libère', 'gain', 'help', 'will', 'potentially', 'increase', 'reduce', 'réduit', 'améliore']):
                            # This line is likely an impact description
                            # BUT check if it contains section markers first
                            if any(marker in line.upper() for marker in ['STRATEGIC ALTERNATIVES', 'ALTERNATIVES STRATÉGIQUES', 'CHARTS', 'GRAPH', 'ALTERNATIVE']):
                                # This is not an impact, it's a section marker - stop processing
                                if current_action and len(current_action.get('action', '')) > 5:
                                    current_action["action"] = self._clean_action_text(current_action["action"])
                                    actions.append(current_action)
                                current_action = None
                                break
                            
                            impact_text = self._clean_action_text(line)
                            # Remove "Impact:" prefix if present
                            impact_text = re.sub(r'^impact\s*:?\s*', '', impact_text, flags=re.IGNORECASE)
                            # Stop at "Impact tréso:" if present (that's for alternatives, not actions)
                            impact_tréso_match = re.search(r'Impact\s+tréso:', impact_text, re.IGNORECASE)
                            if impact_tréso_match:
                                impact_text = impact_text[:impact_tréso_match.start()].strip()
                            
                            if impact_text:
                                current_action["impact"] = impact_text
                        elif current_action and len(line) > 10 and not any(skip in line.upper() for skip in ['ALTERNATIVE', 'CHART', 'GRAPH', 'SCENARIO']):
                            # Might be continuation of action description (but not a new section)
                            continuation = self._clean_action_text(line)
                            if continuation:
                                current_action["action"] += " " + continuation
                    
                    # Save last action
                    if current_action and len(current_action.get('action', '')) > 5:
                        current_action["action"] = self._clean_action_text(current_action["action"])
                        actions.append(current_action)
                    
                    # Fallback: try regex patterns if no actions found
                    if not actions:
                        action_patterns = [
                            r'([^\n]+)\n([^\n]*(?:impact|libère|gain|meilleure|help|will|potentially)[^\n]*)',  # Action\nImpact
                            r'[-•*]\s*([^\n]+)\n(?:\s*(?:impact|libère|gain|meilleure)[:\s]+([^\n]+))?',  # Bullet format
                            r'([^\n]+)\s*→\s*(?:impact|impact tréso)[:\s]+([^\n]+)',  # Arrow format
                            r'([^\n]+)',  # Fallback: just the action line
                        ]
                        
                        for action_pattern in action_patterns:
                            matches = re.finditer(action_pattern, section_text, re.IGNORECASE | re.MULTILINE)
                            for match in matches:
                                action_text = match.group(1).strip()
                                impact_text = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None
                                
                                # Clean up action text - remove section markers
                                action_text = self._clean_action_text(action_text)
                                
                                # Skip if action contains section markers
                                if any(marker in action_text.upper() for marker in ['STRATEGIC ALTERNATIVES', 'ALTERNATIVES STRATÉGIQUES', 'CHARTS', 'GRAPH']):
                                    continue
                                
                                if impact_text:
                                    impact_text = self._clean_action_text(impact_text)
                                
                                # If no impact found, look for it on next lines
                                if not impact_text:
                                    # Look for impact pattern in surrounding text
                                    impact_match = re.search(r'(?:impact|libère|gain|meilleure|help|will|potentially)[:\s]+([^\n]+)', section_text[section_text.find(action_text):], re.IGNORECASE)
                                    if impact_match:
                                        impact_text = impact_match.group(1).strip()
                                        impact_text = self._clean_action_text(impact_text)
                                
                                if action_text and len(action_text) > 5:  # Valid action
                                    actions.append({
                                        "priority": priority,
                                        "action": action_text,
                                        "impact": impact_text
                                    })
                    
                    break  # Found section, move to next priority
        
        # Remove duplicates and clean actions
        seen_actions = set()
        unique_actions = []
        for action in actions:
            # Clean action text one more time
            action["action"] = self._clean_action_text(action.get("action", ""))
            
            # Skip if action is empty or too short after cleaning
            if not action["action"] or len(action["action"]) < 10:
                continue
            
            # Normalize action text for comparison (remove punctuation, normalize whitespace)
            normalized = action.get('action', '').lower().strip()
            normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
            normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
            
            # Extract first 30 chars for comparison (most actions start similarly)
            normalized_key = normalized[:50] if len(normalized) > 50 else normalized
            
            # Check if we've seen a similar action
            is_duplicate = False
            for seen in seen_actions:
                # Check if actions are very similar (one contains the other or they share significant prefix)
                if normalized_key in seen or seen in normalized_key or \
                   (len(normalized_key) > 20 and len(seen) > 20 and normalized_key[:20] == seen[:20]):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_actions.add(normalized_key)
                unique_actions.append(action)
        
        logger.info(f"Extracted {len(unique_actions)} unique recommended actions (from {len(actions)} total)")
        if not unique_actions:
            logger.warning("No recommended actions extracted! Text may not match expected format.")
        
        return unique_actions
    
    def _extract_alternatives_from_comprehensive(self, text: str) -> List[Dict[str, Any]]:
        """Extract alternatives from comprehensive analysis"""
        alternatives = []
        
        logger.info("Extracting alternatives from analysis text")
        
        # Look for alternatives section
        alt_pattern = r'alternative\s+\d+[:\s]+([^\n]+)\n([^\n]+(?:\n[^\n]+)*?)(?=\n(?:alternative|\*\*|\Z))'
        matches = re.finditer(alt_pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        for match in matches:
            name = match.group(1).strip()
            description = match.group(2).strip()
            
            # Extract impact
            impact_match = re.search(r'impact[:\s]+([^\n]+)', description, re.IGNORECASE)
            impact = impact_match.group(1).strip() if impact_match else None
            
            # Clean description
            if impact_match:
                description = description.replace(impact_match.group(0), "").strip()
            
            alternatives.append({
                "name": name,
                "description": description,
                "impact": impact
            })
        
        logger.info(f"Extracted {len(alternatives)} alternatives")
        if not alternatives:
            logger.warning("No alternatives extracted! Text may not match expected format.")
        
        return alternatives
    
    def _estimate_missing_data(self, available_data: Dict[str, Any], missing_requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Intelligently estimate missing data based on available patterns and industry standards
        
        Args:
            available_data: Data that is available
            missing_requirements: List of missing data requirements
            
        Returns:
            Dict with estimated data and notes
        """
        estimations = {}
        estimation_notes = []
        
        # Industry standard ratios (can be expanded)
        industry_ratios = {
            "gross_margin": 0.35,  # 35% average
            "payroll_percentage": 0.30,  # 30% of revenue
            "cash_safety_threshold": 15000,  # 15k€ safety threshold
            "client_payment_delay_days": 45,
            "stock_rotation_days": 60
        }
        
        for req in missing_requirements:
            req_id = req.get("requirement_id", "")
            data_type = req.get("data_type", "").lower()
            
            # Estimate based on data type
            if data_type == "cash_flow" and available_data.get("revenue"):
                # Estimate cash flow from revenue (assuming 20% cash margin)
                estimated_cash = available_data["revenue"] * 0.20
                estimations[req_id] = {
                    "estimated_value": estimated_cash,
                    "method": "revenue_based_estimation",
                    "confidence": "medium"
                }
                estimation_notes.append(f"Estimated cash flow from revenue data (20% margin assumption)")
            
            elif data_type == "expenses" and available_data.get("revenue"):
                # Estimate expenses from revenue (assuming 65% expense ratio)
                estimated_expenses = available_data["revenue"] * 0.65
                estimations[req_id] = {
                    "estimated_value": estimated_expenses,
                    "method": "revenue_based_estimation",
                    "confidence": "medium"
                }
                estimation_notes.append(f"Estimated expenses from revenue data (65% expense ratio assumption)")
            
            elif data_type == "payroll" and available_data.get("revenue"):
                # Estimate payroll from revenue
                estimated_payroll = available_data["revenue"] * industry_ratios["payroll_percentage"]
                estimations[req_id] = {
                    "estimated_value": estimated_payroll,
                    "method": "industry_standard",
                    "confidence": "low"
                }
                estimation_notes.append(f"Estimated payroll using industry standard ({industry_ratios['payroll_percentage']*100}% of revenue)")
        
        return {
            "estimations": estimations,
            "notes": estimation_notes
        }
    
    def _validate_analysis_quality(self, formatted_results: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Validate the quality and completeness of an analysis
        Returns quality score and suggestions for improvement
        """
        quality_score = 100
        issues = []
        suggestions = []
        
        # Check decision_summary completeness
        decision_summary = formatted_results.get("decision_summary", {})
        if not decision_summary.get("description"):
            quality_score -= 15
            issues.append("Missing decision summary description")
            suggestions.append("Add a detailed description of the decision being analyzed")
        elif len(decision_summary.get("description", "")) < 50:
            quality_score -= 5
            issues.append("Decision summary description is too short")
            suggestions.append("Expand the decision summary description with more details")
        
        if not decision_summary.get("importance"):
            quality_score -= 10
            issues.append("Missing decision importance explanation")
            suggestions.append("Explain why this decision matters financially")
        
        # Check key_metrics completeness
        key_metrics = formatted_results.get("key_metrics", {})
        if not key_metrics or len(key_metrics) == 0:
            quality_score -= 20
            issues.append("No key metrics provided")
            suggestions.append("Include at least 2-3 key financial metrics relevant to this decision")
        elif len(key_metrics) < 2:
            quality_score -= 10
            issues.append("Too few key metrics")
            suggestions.append("Add more key metrics to provide a comprehensive financial picture")
        else:
            # Validate metric quality
            for metric_name, metric_data in key_metrics.items():
                if not metric_data.get("value"):
                    quality_score -= 5
                    issues.append(f"Metric {metric_name} missing value")
                if not metric_data.get("description") and not metric_data.get("unit"):
                    quality_score -= 2
                    issues.append(f"Metric {metric_name} lacks context")
        
        # Check critical_factors completeness
        critical_factors = formatted_results.get("critical_factors", [])
        if not critical_factors or len(critical_factors) == 0:
            quality_score -= 15
            issues.append("No critical factors identified")
            suggestions.append("Identify at least 2-3 critical factors that should be considered")
        elif len(critical_factors) < 2:
            quality_score -= 5
            issues.append("Too few critical factors")
            suggestions.append("Add more critical factors for a thorough analysis")
        else:
            # Validate factor quality
            for i, factor in enumerate(critical_factors):
                if not factor.get("factor"):
                    quality_score -= 3
                    issues.append(f"Critical factor {i+1} missing factor name")
                if not factor.get("description") or len(factor.get("description", "")) < 20:
                    quality_score -= 3
                    issues.append(f"Critical factor {i+1} description is too brief")
        
        # Check scenarios completeness
        scenarios = formatted_results.get("scenarios", {})
        if not scenarios:
            quality_score -= 10
            issues.append("No scenarios provided")
            suggestions.append("Include at least realistic and pessimistic scenarios")
        else:
            scenario_count = sum([
                1 if scenarios.get("optimistic") else 0,
                1 if scenarios.get("realistic") else 0,
                1 if scenarios.get("pessimistic") else 0,
            ])
            if scenario_count < 2:
                quality_score -= 5
                issues.append("Too few scenarios")
                suggestions.append("Include at least realistic and pessimistic scenarios")
            else:
                # Validate scenario quality
                for scenario_type in ["optimistic", "realistic", "pessimistic"]:
                    scenario = scenarios.get(scenario_type)
                    if scenario and not scenario.get("description"):
                        quality_score -= 3
                        issues.append(f"{scenario_type} scenario missing description")
                    elif scenario and len(scenario.get("description", "")) < 30:
                        quality_score -= 2
                        issues.append(f"{scenario_type} scenario description is too brief")
        
        # Check recommended_actions completeness
        recommended_actions = formatted_results.get("recommended_actions", [])
        if not recommended_actions or len(recommended_actions) == 0:
            quality_score -= 10
            issues.append("No recommended actions provided")
            suggestions.append("Include at least 2-3 actionable recommendations")
        elif len(recommended_actions) < 2:
            quality_score -= 5
            issues.append("Too few recommended actions")
            suggestions.append("Add more actionable recommendations")
        else:
            # Validate action quality
            for i, action in enumerate(recommended_actions):
                if not action.get("action"):
                    quality_score -= 3
                    issues.append(f"Recommended action {i+1} missing action text")
                if not action.get("priority"):
                    quality_score -= 2
                    issues.append(f"Recommended action {i+1} missing priority")
        
        # Check current_context completeness (optional but valuable)
        current_context = formatted_results.get("current_context", {})
        if current_context:
            if not current_context.get("strengths") and not current_context.get("weaknesses"):
                quality_score -= 5
                issues.append("Current context lacks strengths or weaknesses")
            elif len(current_context.get("strengths", [])) == 0 and len(current_context.get("weaknesses", [])) == 0:
                quality_score -= 5
                issues.append("Current context is empty")
        
        # Check for narrative quality (full_analysis_text)
        full_analysis_text = formatted_results.get("full_analysis_text", "")
        if not full_analysis_text or len(full_analysis_text) < 200:
            quality_score -= 10
            issues.append("Analysis narrative is too brief")
            suggestions.append("Expand the narrative analysis with more detailed explanations")
        elif len(full_analysis_text) < 500:
            quality_score -= 5
            issues.append("Analysis narrative could be more detailed")
        
        # Determine quality level
        if quality_score >= 90:
            quality_level = "excellent"
        elif quality_score >= 75:
            quality_level = "good"
        elif quality_score >= 60:
            quality_level = "acceptable"
        else:
            quality_level = "needs_improvement"
        
        return {
            "quality_score": max(0, quality_score),  # Ensure non-negative
            "quality_level": quality_level,
            "issues": issues,
            "suggestions": suggestions,
            "needs_improvement": quality_score < 75,
        }
    
    def _enrich_analysis(self, formatted_results: Dict[str, Any], raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich analysis results with additional metrics, ratios, and insights
        
        Args:
            formatted_results: Already formatted results
            raw_results: Raw results from analysis passes
            
        Returns:
            Enriched results dict
        """
        enriched = formatted_results.copy()
        
        # Determine data quality
        has_missing = len(formatted_results.get("missing_data_requests", [])) > 0
        has_estimated = any("estimated" in str(v).lower() for v in formatted_results.values())
        
        if has_estimated:
            data_quality = "estimated"
        elif has_missing:
            data_quality = "partial"
        else:
            data_quality = "good"
        
        enriched["data_quality"] = data_quality
        
        # Add financial ratios if we have metrics
        if formatted_results.get("key_metrics"):
            ratios = {}
            metrics = formatted_results["key_metrics"]
            
            # Calculate additional ratios if we have the data
            if metrics.get("total_cost") and metrics.get("cash_impact"):
                try:
                    cost_value = float(str(metrics["total_cost"]["value"]).replace(',', '').replace('k', '000').replace('K', '000'))
                    impact_value = abs(float(str(metrics["cash_impact"]["value"]).replace(',', '').replace('k', '000').replace('K', '000')))
                    if cost_value > 0:
                        impact_ratio = (impact_value / cost_value) * 100
                        ratios["cost_impact_ratio"] = {
                            "value": round(impact_ratio, 1),
                            "unit": "%",
                            "description": "Cash impact as percentage of total cost"
                        }
                except (ValueError, TypeError):
                    pass
            
            if ratios:
                enriched["financial_ratios"] = ratios
        
        # Add risk assessment if we have scenarios
        if formatted_results.get("scenarios"):
            risk_assessment = {
                "has_risk_periods": any(
                    scenario.get("risk_periods") 
                    for scenario in formatted_results["scenarios"].values() 
                    if isinstance(scenario, dict)
                ),
                "scenario_count": len(formatted_results["scenarios"])
            }
            enriched["risk_assessment"] = risk_assessment
        
        # Add estimation notes if any
        estimation_notes = []
        if has_estimated:
            estimation_notes.append("Some metrics were estimated based on available data patterns and industry standards.")
        if has_missing:
            estimation_notes.append("Analysis performed with partial data - some ideal requirements were missing.")
        
        if estimation_notes:
            enriched["estimation_notes"] = estimation_notes
        
        return enriched

