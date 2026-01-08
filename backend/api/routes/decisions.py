"""
Decision analysis routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
import asyncio
from pathlib import Path
import logging
import base64

# Add code_interpreter to path
code_interpreter_path = Path(__file__).parent.parent.parent.parent / "code_interpreter"
sys.path.insert(0, str(code_interpreter_path))

try:
    from services.decision_analyzer import DecisionAnalyzer
    from services.gemini_service import GeminiCodeExecutionService
except ImportError as e:
    logging.error(f"Error importing code_interpreter services: {e}")
    raise

router = APIRouter()

# Upload directory - relative to project root
project_root = Path(__file__).parent.parent.parent.parent
UPLOAD_DIR = project_root / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class DecisionRequest(BaseModel):
    question: str
    file_ids: Optional[List[str]] = None  # If None, use all available files

class FileData(BaseModel):
    file_id: str
    original_name: str
    file_type: str
    content_base64: str
    mime_type: str

class StreamDecisionRequest(BaseModel):
    question: str
    file_ids: Optional[List[str]] = None
    files_data: Optional[List[FileData]] = None  # File content sent directly from Next.js
    analysis_id: Optional[str] = None  # For status updates
    update_status_url: Optional[str] = None  # URL to call for status updates

class ChatRequest(BaseModel):
    analysis_id: str
    question: str  # Original question
    message: str  # User's chat message
    analysis_result: Optional[Dict[str, Any]] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    hypotheses: Optional[List[Dict[str, Any]]] = None
    should_update_hypotheses: bool = False

class GenerateHypothesesRequest(BaseModel):
    question: str
    analysis_result: Optional[Dict[str, Any]] = None

@router.post("/analyze")
async def analyze_decision(request: DecisionRequest) -> Dict[str, Any]:
    """
    Analyze a decision question using available files
    """
    try:
        # Initialize services
        gemini_service = GeminiCodeExecutionService()
        decision_analyzer = DecisionAnalyzer(gemini_service)

        # Get files to analyze
        files_to_analyze = {}
        
        if request.file_ids:
            # Use specified files
            for file_id in request.file_ids:
                file_path = UPLOAD_DIR / file_id
                csv_path = UPLOAD_DIR / f"{Path(file_id).stem}.csv"
                
                # Prefer CSV if exists, otherwise use original
                if csv_path.exists():
                    files_to_analyze[file_id] = {
                        "file": csv_path,
                        "name": csv_path.name,
                        "info": {}
                    }
                elif file_path.exists():
                    files_to_analyze[file_id] = {
                        "file": file_path,
                        "name": file_path.name,
                        "info": {}
                    }
        else:
            # Use all CSV files in uploads directory
            for csv_file in UPLOAD_DIR.glob("*.csv"):
                file_id = csv_file.stem
                files_to_analyze[file_id] = {
                    "file": csv_file,
                    "name": csv_file.name,
                    "info": {}
                }

        # Run analysis
        if files_to_analyze:
            # Combined analysis: question + structure adaptation
            combined_result = await decision_analyzer.analyze_question_and_adapt_structure(
                request.question,
                files_to_analyze
            )

            # Generate final report
            structure_definition = {
                "decision_summary": combined_result.get("decision_summary", {}),
                "expected_structure": combined_result.get("final_structure", {})
            }
            
            adapted_structure = {
                "final_structure": combined_result.get("final_structure", {}),
                "file_analysis": combined_result.get("file_analysis", {})
            }

            result = await decision_analyzer.generate_final_report(
                request.question,
                adapted_structure,
                files_to_analyze,
                structure_definition.get("decision_summary", {})
            )

            # Convert chart bytes to base64 before returning
            result = convert_charts_to_base64(result)
            return result
        else:
            # No files - advisory only analysis
            result = await decision_analyzer.analyze_decision_advisory(request.question)
            # Convert chart bytes to base64 before returning
            result = convert_charts_to_base64(result)
            return result

    except Exception as e:
        logging.error(f"Error analyzing decision: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing decision: {str(e)}"
        )

def save_files_from_data(files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save files from base64 content sent from Next.js
    Returns dict mapping file_id to local file path
    """
    files_to_analyze = {}
    
    try:
        for file_data in files_data:
            file_id = file_data["file_id"]
            original_name = file_data["original_name"]
            file_type = file_data["file_type"]
            content_base64 = file_data.get("content_base64")
            
            if not content_base64:
                logging.error(f"No content_base64 for file {file_id}")
                continue
            
            # Determine file extension
            if file_type == "csv":
                extension = ".csv"
            elif file_type == "excel":
                extension = Path(original_name).suffix or ".xlsx"
            else:
                extension = Path(original_name).suffix or ".csv"
            
            # Create temporary file in uploads directory
            temp_file_path = UPLOAD_DIR / f"{file_id}{extension}"
            
            # Decode and save file content
            try:
                file_content = base64.b64decode(content_base64)
                temp_file_path.write_bytes(file_content)
            except Exception as e:
                logging.error(f"Error decoding file {file_id}: {e}")
                continue
            
            # If Excel file, convert to CSV
            if file_type == "excel" and extension in [".xlsx", ".xls"]:
                try:
                    from services.gemini_service import GeminiCodeExecutionService
                    gemini_service = GeminiCodeExecutionService()
                    csv_path = gemini_service._convert_to_csv(str(temp_file_path), original_name)
                    csv_file_path = Path(csv_path)
                    
                    # Use CSV if conversion successful
                    if csv_file_path.exists():
                        files_to_analyze[file_id] = {
                            "file": csv_file_path,
                            "name": csv_file_path.name,
                            "info": {}
                        }
                        # Remove temp Excel file
                        temp_file_path.unlink()
                        continue
                except Exception as e:
                    logging.warning(f"Failed to convert Excel to CSV for {file_id}: {e}")
                    # Continue with Excel file
            
            # Use file as-is
            files_to_analyze[file_id] = {
                "file": temp_file_path,
                "name": original_name,
                "info": {}
            }
        
        return files_to_analyze
        
    except Exception as e:
        logging.error(f"Error saving files from data: {e}", exc_info=True)
        return {}


def convert_bytes_to_base64_recursive(obj: Any) -> Any:
    """
    Recursively convert all bytes objects to base64 strings for JSON serialization
    """
    if isinstance(obj, bytes):
        # Convert bytes to base64 string
        return base64.b64encode(obj).decode('utf-8')
    elif isinstance(obj, dict):
        # Recursively process dictionary
        converted_dict = {}
        for key, value in obj.items():
            if isinstance(value, bytes):
                # Convert bytes to base64, keep original key or use data_base64
                if key == "data":
                    converted_dict["data_base64"] = base64.b64encode(value).decode('utf-8')
                else:
                    converted_dict[key] = base64.b64encode(value).decode('utf-8')
            else:
                converted_dict[key] = convert_bytes_to_base64_recursive(value)
        return converted_dict
    elif isinstance(obj, list):
        # Recursively process list
        return [convert_bytes_to_base64_recursive(item) for item in obj]
    elif isinstance(obj, tuple):
        # Recursively process tuple
        return tuple(convert_bytes_to_base64_recursive(item) for item in obj)
    else:
        # Return as-is for other types (str, int, float, bool, None, etc.)
        return obj


def convert_charts_to_base64(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert chart binary data to base64 strings for JSON serialization
    Uses recursive conversion to catch all bytes objects
    """
    return convert_bytes_to_base64_recursive(result)


@router.post("/analyze/stream")
async def analyze_decision_stream(request: StreamDecisionRequest) -> Dict[str, Any]:
    """
    Analyze a decision question with step-by-step status updates
    This endpoint is called asynchronously and updates are tracked via analysis_id
    """
    try:
        # Initialize services
        gemini_service = GeminiCodeExecutionService()
        decision_analyzer = DecisionAnalyzer(gemini_service)

        # Get files to analyze
        files_to_analyze = {}
        temp_files_to_cleanup = []
        
        if request.files_data and len(request.files_data) > 0:
            # Files sent directly from Next.js (preferred method)
            logging.info(f"Received {len(request.files_data)} files from Next.js API")
            files_dict = [f.dict() for f in request.files_data]
            files_to_analyze = save_files_from_data(files_dict)
            temp_files_to_cleanup = list(files_to_analyze.values())
            logging.info(f"Saved {len(files_to_analyze)} files successfully")
        elif request.file_ids:
            # Fallback: try to find files locally (for backward compatibility)
            logging.info(f"Looking for {len(request.file_ids)} files locally...")
            for file_id in request.file_ids:
                file_path = UPLOAD_DIR / file_id
                csv_path = UPLOAD_DIR / f"{Path(file_id).stem}.csv"
                
                # Prefer CSV if exists, otherwise use original
                if csv_path.exists():
                    files_to_analyze[file_id] = {
                        "file": csv_path,
                        "name": csv_path.name,
                        "info": {}
                    }
                elif file_path.exists():
                    files_to_analyze[file_id] = {
                        "file": file_path,
                        "name": file_path.name,
                        "info": {}
                    }
            
            if len(files_to_analyze) == 0:
                logging.warning(f"No files found locally for {len(request.file_ids)} file_ids")
        else:
            # Use all CSV files in uploads directory (fallback)
            for csv_file in UPLOAD_DIR.glob("*.csv"):
                file_id = csv_file.stem
                files_to_analyze[file_id] = {
                    "file": csv_file,
                    "name": csv_file.name,
                    "info": {}
                }

        # Helper function to update status via Next.js API
        async def update_step(step_name: str, progress: int, message: str = "", step_status: str = "in_progress"):
            if not request.update_status_url:
                logging.info(f"[Step Update] {step_name}: {message} (progress: {progress}%)")
                return
            
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # Get current steps from Supabase or use defaults
                    steps_update = [
                        {"name": "analyzing_question", "label": "Analyse de la question", "status": "completed" if step_name != "analyzing_question" else step_status, "message": ""},
                        {"name": "checking_files", "label": "Vérification des fichiers disponibles", "status": "completed" if step_name == "analyzing_structure" or step_name in ["calculating_metrics", "generating_scenarios", "creating_recommendations"] else ("in_progress" if step_name == "checking_files" else "pending"), "message": ""},
                        {"name": "analyzing_structure", "label": "Analyse de la structure des données", "status": "completed" if step_name in ["calculating_metrics", "generating_scenarios", "creating_recommendations"] else ("in_progress" if step_name == "analyzing_structure" else "pending"), "message": ""},
                        {"name": "calculating_metrics", "label": "Calcul des métriques clés", "status": "completed" if step_name in ["generating_scenarios", "creating_recommendations"] else ("in_progress" if step_name == "calculating_metrics" else "pending"), "message": ""},
                        {"name": "generating_scenarios", "label": "Génération des scénarios", "status": "completed" if step_name == "creating_recommendations" else ("in_progress" if step_name == "generating_scenarios" else "pending"), "message": ""},
                        {"name": "creating_recommendations", "label": "Création des recommandations", "status": "completed" if step_name == "creating_recommendations" else ("in_progress" if step_name == "creating_recommendations" else "pending"), "message": ""},
                    ]
                    
                    # Update the current step with message
                    for step in steps_update:
                        if step["name"] == step_name:
                            step["status"] = step_status
                            step["message"] = message
                    
                    response = await client.post(
                        request.update_status_url,
                        json={
                            "status": "in_progress",
                            "current_step": step_name,
                            "progress": progress,
                            "steps": steps_update,
                            "message": message,
                        },
                        headers={"Content-Type": "application/json"},
                    )
                    if response.status_code == 200:
                        logging.info(f"[Step Update] Successfully updated {step_name} at {progress}%")
                    else:
                        logging.warning(f"[Step Update] Failed to update {step_name}: {response.status_code}")
            except Exception as e:
                logging.warning(f"[Step Update] Error updating step {step_name}: {e}")

        # Run analysis with steps tracking
        if files_to_analyze:
            # Step 1: Analyze question structure
            await update_step("analyzing_question", 10, "Analyse de la question et extraction des paramètres clés...")
            
            # Step 2: Analyze files structure
            await update_step("checking_files", 20, f"Analyse de {len(files_to_analyze)} fichier(s) disponible(s)...")
            
            # Step 3: Analyze structure
            await update_step("analyzing_structure", 30, "Analyse de la structure des données et adaptation...")
            
            # Combined analysis: question + structure adaptation
            combined_result = await decision_analyzer.analyze_question_and_adapt_structure(
                request.question,
                files_to_analyze
            )

            # Step 4: Calculate metrics
            await update_step("calculating_metrics", 50, "Calcul des métriques financières clés...")

            # Generate final report
            structure_definition = {
                "decision_summary": combined_result.get("decision_summary", {}),
                "expected_structure": combined_result.get("final_structure", {})
            }
            
            adapted_structure = {
                "final_structure": combined_result.get("final_structure", {}),
                "file_analysis": combined_result.get("file_analysis", {})
            }

            # Step 5: Generate scenarios
            await update_step("generating_scenarios", 70, "Génération des scénarios optimiste, réaliste et pessimiste...")

            result = await decision_analyzer.generate_final_report(
                request.question,
                adapted_structure,
                files_to_analyze,
                structure_definition.get("decision_summary", {})
            )

            # Step 6: Create recommendations
            await update_step("creating_recommendations", 90, "Création des recommandations et alternatives...")

            # Convert chart bytes to base64 before returning
            result = convert_charts_to_base64(result)
            
            # Final step completed
            await update_step("creating_recommendations", 100, "Analyse terminée avec succès", "completed")
            
            return result
        else:
            # No files - advisory only analysis
            await update_step("analyzing_question", 30, "Analyse de la question sans fichiers...")
            await update_step("calculating_metrics", 50, "Calcul des métriques basées sur la question...")
            await update_step("generating_scenarios", 70, "Génération des scénarios...")
            await update_step("creating_recommendations", 90, "Création des recommandations...")
            
            result = await decision_analyzer.analyze_decision_advisory(request.question)
            # Convert chart bytes to base64 before returning
            result = convert_charts_to_base64(result)
            
            await update_step("creating_recommendations", 100, "Analyse terminée avec succès", "completed")
            
            return result

    except Exception as e:
        logging.error(f"Error analyzing decision (stream): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing decision: {str(e)}"
        )
    finally:
        # Cleanup temporary files downloaded from Supabase
        for file_data in temp_files_to_cleanup:
            try:
                file_path = file_data.get("file")
                if file_path and Path(file_path).exists():
                    # Only delete if it's a temporary file (UUID as filename)
                    file_name = Path(file_path).name
                    if len(file_name.split('.')) > 0:
                        file_stem = Path(file_path).stem
                        # Check if it looks like a UUID (has dashes and is long enough)
                        if '-' in file_stem and len(file_stem) > 20:
                            Path(file_path).unlink()
                            logging.info(f"Cleaned up temporary file: {file_path}")
            except Exception as cleanup_error:
                logging.warning(f"Error cleaning up temp file: {cleanup_error}")


@router.post("/chat")
async def chat_about_analysis(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat contextually about an existing analysis
    Can update hypotheses and suggest relaunching the analysis
    """
    try:
        # Initialize services
        gemini_service = GeminiCodeExecutionService()
        decision_analyzer = DecisionAnalyzer(gemini_service)
        
        # Build context from analysis result
        analysis_context = request.analysis_result or {}
        
        # Format chat history for the AI
        chat_context = ""
        if request.chat_history:
            for msg in request.chat_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")
                chat_context += f"{role.capitalize()}: {content}\n"
        
        # Build prompt for contextual chat
        hypotheses_str = ""
        if request.hypotheses:
            hypotheses_str = "\n".join([
                f"- {h.get('label', h.get('id', 'Unknown'))}: {h.get('value', 'N/A')}"
                for h in request.hypotheses
            ])
        
        prompt = f"""Tu es un assistant CFO qui aide à analyser des décisions financières.

Question originale: {request.question}

Contexte de l'analyse actuelle:
- Résumé: {analysis_context.get('decision_summary', {}).get('description', 'N/A')}
- Métriques clés: {analysis_context.get('key_metrics', {})}
- Scénarios: {analysis_context.get('scenarios', {})}

Historique de la conversation:
{chat_context}

Message de l'utilisateur: {request.message}

Hypothèses actuelles:
{hypotheses_str if hypotheses_str else "Aucune hypothèse définie"}

IMPORTANT: 
- Réponds de manière contextuelle et utile
- Si l'utilisateur modifie EXPLICITEMENT une valeur d'hypothèse (ex: "change le salaire à 70k€"), alors suggère de mettre à jour cette hypothèse
- Ne suggère PAS de relancer l'analyse si l'utilisateur pose juste une question ou fait un commentaire sans modifier d'hypothèse
- Ne suggère de relancer l'analyse QUE si une hypothèse a été modifiée avec une nouvelle valeur numérique

Réponds en français de manière professionnelle et concise."""

        # Get response from Gemini using the normal model (without code execution)
        response = gemini_service.model_normal.generate_content(prompt)
        response_text = ""
        if response.candidates and len(response.candidates) > 0:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
        
        # Fallback if no text was extracted
        if not response_text:
            response_text = "Je n'ai pas pu générer de réponse. Veuillez réessayer."
        
        # Try to extract updated hypotheses if the AI suggests changes
        updated_hypotheses = None
        should_relaunch = False
        
        # Simple heuristic: if the response mentions specific values or changes, suggest updating hypotheses
        if request.should_update_hypotheses:
            # Check if response contains numeric values that could be hypotheses
            import re
            # Look for patterns like "60 000€", "50k€", etc.
            value_patterns = re.findall(r'(\d+[\s,.]?\d*)\s*(?:k|K|€|euros?)', response_text)
            if value_patterns and request.hypotheses:
                # Try to match values to existing hypotheses
                updated_hypotheses = request.hypotheses.copy()
                hypotheses_changed = False
                for i, hyp in enumerate(updated_hypotheses):
                    # Simple matching logic - can be improved
                    if value_patterns and i < len(value_patterns):
                        try:
                            new_value = float(value_patterns[i].replace(',', '.').replace(' ', ''))
                            if 'k' in value_patterns[i] or 'K' in value_patterns[i]:
                                new_value *= 1000
                            
                            # Compare with current value
                            current_value = hyp.get('value')
                            if current_value != new_value:
                                updated_hypotheses[i]['value'] = new_value
                                hypotheses_changed = True
                        except:
                            pass
                
                # Only suggest relaunch if hypotheses actually changed
                if hypotheses_changed:
                    should_relaunch = True
                else:
                    # If no changes detected, don't suggest relaunch even if keywords are present
                    updated_hypotheses = None
        
        return {
            "response": response_text,
            "updated_hypotheses": updated_hypotheses,
            "should_relaunch_analysis": should_relaunch,
        }
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

