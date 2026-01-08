"""
Streamlit application for Financial Decision Analysis
Uses Gemini Code Execution to analyze financial decisions
"""
import streamlit as st
import os
from dotenv import load_dotenv
import logging
import traceback
from io import BytesIO
import base64
import uuid
import datetime
import asyncio

from services.gemini_service import GeminiCodeExecutionService
from services.file_utils import get_file_info, aggregate_file_metadata
from services.decision_analyzer import DecisionAnalyzer
import tempfile
import pandas as pd
from pathlib import Path

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Financial Decision Analyzer",
    page_icon="📊",
    layout="wide"
)

# Logging configuration to display in UI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {}  # {file_id: {file, name, info, uploaded_at}}
if 'decision_question' not in st.session_state:
    st.session_state.decision_question = None
if 'analysis_status' not in st.session_state:
    st.session_state.analysis_status = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'requirements' not in st.session_state:
    st.session_state.requirements = None
if 'data_availability' not in st.session_state:
    st.session_state.data_availability = None
if 'structure_definition' not in st.session_state:
    st.session_state.structure_definition = None
if 'adapted_structure' not in st.session_state:
    st.session_state.adapted_structure = None
if 'partial_analysis' not in st.session_state:
    st.session_state.partial_analysis = False
if 'progressive_analysis_state' not in st.session_state:
    st.session_state.progressive_analysis_state = None
if 'pending_uploads' not in st.session_state:
    st.session_state.pending_uploads = {}
if 'logs' not in st.session_state:
    st.session_state.logs = []


def add_log(message: str, level: str = "INFO"):
    """Adds a log to session state"""
    st.session_state.logs.append({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message
    })


def convert_excel_to_csv(file_content: BytesIO, original_name: str) -> tuple[BytesIO, str]:
    """
    Convert Excel file to CSV format
    
    Args:
        file_content: BytesIO content of the Excel file
        original_name: Original filename
        
    Returns:
        Tuple of (CSV BytesIO content, CSV filename)
    """
    file_content.seek(0)
    suffix = Path(original_name).suffix.lower()
    
    # Read Excel file
    if suffix == '.xls':
        df = pd.read_excel(file_content, engine='xlrd')
    else:
        df = pd.read_excel(file_content, engine='openpyxl')
    
    # Convert to CSV in memory
    csv_content = BytesIO()
    csv_filename = Path(original_name).stem + '.csv'
    df.to_csv(csv_content, index=False, encoding='utf-8')
    csv_content.seek(0)
    
    return csv_content, csv_filename


def add_file_to_session(uploaded_file) -> str:
    """Add file to session state with metadata and convert Excel to CSV"""
    file_id = str(uuid.uuid4())
    
    # Extract metadata
    try:
        file_info = get_file_info(uploaded_file)
        uploaded_file.seek(0)  # Reset for later use
        
        # Read file content into BytesIO for persistence across reruns
        file_content = BytesIO(uploaded_file.read())
        file_content.seek(0)
        
        original_name = uploaded_file.name
        suffix = Path(original_name).suffix.lower()
        
        # Convert Excel to CSV if needed
        csv_content = None
        csv_filename = None
        if suffix in ['.xlsx', '.xls']:
            csv_content, csv_filename = convert_excel_to_csv(file_content, original_name)
            add_log(f"Converted {original_name} to CSV: {csv_filename}")
        
        # Create a file-like object wrapper for original file
        class FileWrapper:
            def __init__(self, content: BytesIO, name: str):
                self.content = content
                self.name = name
            
            def read(self, size=-1):
                return self.content.read(size)
            
            def seek(self, pos):
                self.content.seek(pos)
                return self.content.tell()
            
            def getvalue(self):
                return self.content.getvalue()
        
        # Create wrapper for CSV if converted
        csv_wrapper = None
        if csv_content:
            csv_wrapper = FileWrapper(csv_content, csv_filename)
        
        file_wrapper = FileWrapper(file_content, original_name)
        
        st.session_state.uploaded_files[file_id] = {
            "file": csv_wrapper if csv_wrapper else file_wrapper,  # Use CSV if available, otherwise original
            "original_file": file_wrapper,  # Keep original for reference
            "csv_file": csv_wrapper,  # CSV version (None if already CSV)
            "name": original_name,
            "csv_name": csv_filename if csv_filename else original_name,
            "info": file_info,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "is_excel": suffix in ['.xlsx', '.xls']
        }
        
        add_log(f"File added: {original_name}" + (f" (converted to {csv_filename})" if csv_filename else ""))
        return file_id
    except Exception as e:
        add_log(f"Error adding file {uploaded_file.name}: {str(e)}", "ERROR")
        raise


def remove_file_from_session(file_id: str):
    """Remove file from session state"""
    if file_id in st.session_state.uploaded_files:
        file_name = st.session_state.uploaded_files[file_id]["name"]
        del st.session_state.uploaded_files[file_id]
        add_log(f"File removed: {file_name}")
        st.rerun()


def get_all_file_metadata() -> dict:
    """Aggregate metadata from all uploaded files"""
    return aggregate_file_metadata(st.session_state.uploaded_files)


def prepare_json_export(data):
    """Prepares data for JSON export by converting bytes to base64"""
    import json
    import base64
    import copy
    
    def convert_bytes_recursive(obj):
        """Recursively converts bytes to base64 strings"""
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        elif isinstance(obj, dict):
            return {key: convert_bytes_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_bytes_recursive(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    try:
        export_data = copy.deepcopy(data)
    except Exception:
        export_data = data
    
    export_data = convert_bytes_recursive(export_data)
    
    if "charts" in export_data and isinstance(export_data["charts"], list):
        simplified_charts = []
        for chart in export_data["charts"]:
            if isinstance(chart, dict):
                simplified_chart = {
                    "filename": chart.get("filename", "unknown.png"),
                    "mime_type": chart.get("mime_type", "unknown"),
                }
                if "data" in chart:
                    if isinstance(chart["data"], str):
                        simplified_chart["data_base64"] = chart["data"]
                    elif isinstance(chart["data"], bytes):
                        simplified_chart["data_base64"] = base64.b64encode(chart["data"]).decode('utf-8')
                simplified_charts.append(simplified_chart)
            else:
                simplified_charts.append(chart)
        export_data["charts"] = simplified_charts
    
    return export_data


def display_decision_analysis(result: dict):
    """Display structured analysis results - Enhanced for MVP"""
    st.header("📊 Decision Analysis Results")
    
    # Data Quality Indicator
    data_quality = result.get("data_quality", "unknown")
    quality_badges = {
        "good": "🟢 Complete Analysis",
        "partial": "🟡 Partial Analysis",
        "estimated": "🟠 Analysis with Estimates",
        "unknown": "⚪ Analysis"
    }
    st.caption(f"**Analysis Quality:** {quality_badges.get(data_quality, quality_badges['unknown'])}")
    if result.get("estimation_notes"):
        for note in result["estimation_notes"]:
            st.info(f"ℹ️ {note}")
    
    st.markdown("---")
    
    # ALWAYS show full analysis text if available (for transparency and fallback)
    full_text = result.get("full_analysis_text", "")
    has_extraction_issues = result.get("has_extraction_issues", False)
    has_structured_content = (
        result.get("key_metrics") or 
        result.get("critical_factors") or 
        result.get("scenarios") or 
        result.get("recommended_actions")
    )
    
    # Show warning if extraction had issues
    if has_extraction_issues:
        st.warning("⚠️ Some content extraction may be incomplete. Full analysis text is available below.")
    
    # ALWAYS show full text in an expander (expanded if extraction issues detected)
    if full_text and len(full_text) > 500:
        with st.expander("📄 Full Analysis Report", expanded=has_extraction_issues or not has_structured_content):
            st.markdown(full_text)
            
            # Also show execution outputs if available (Python print statements)
            execution_outputs = result.get("execution_outputs", [])
            if execution_outputs:
                st.markdown("---")
                st.subheader("📊 Execution Outputs")
                for idx, output in enumerate(execution_outputs, 1):
                    with st.expander(f"Output #{idx}"):
                        st.code(output, language="text")
        
        st.markdown("---")
    
    # Decision Summary
    if result.get("decision_summary"):
        summary = result["decision_summary"]
        st.subheader("💡 La Décision à Analyser")
        
        # Format like example: "Vous envisagez de..."
        if summary.get('description'):
            st.write(summary['description'])
        
        if summary.get('importance'):
            st.info(f"**Pourquoi cette décision est importante :** {summary['importance']}")
        
        st.markdown("---")
    
    # Key Metrics - Enhanced display
    if result.get("key_metrics"):
        st.subheader("📈 Key Metrics")
        metrics = result["key_metrics"]
        
        # Create metric cards in a grid
        num_metrics = len(metrics)
        if num_metrics > 0:
            cols = st.columns(min(num_metrics, 3))
            
            metric_labels = {
                "total_cost": "Coût Total Chargé",
                "cash_impact": "Impact Trésorerie",
                "break_even": "Point Mort",
                "payback_period": "Délai de Récupération",
                "roi": "Retour sur Investissement"
            }
            
            for idx, (metric_name, metric_data) in enumerate(metrics.items()):
                with cols[idx % len(cols)]:
                    if isinstance(metric_data, dict):
                        value = metric_data.get("value", "N/A")
                        unit = metric_data.get("unit", "")
                        description = metric_data.get("description", "")
                        period = metric_data.get("period")
                        
                        # Format display value
                        display_value = f"{value} {unit}".strip()
                        if period:
                            display_value += f"\nSur {period} mois"
                        
                        # Use French label if available
                        label = metric_labels.get(metric_name, metric_name.replace("_", " ").title())
                        
                        st.metric(
                            label,
                            display_value.split("\n")[0],
                            delta=None,
                            help=f"{description}\n{display_value}" if period else description
                        )
                        if period:
                            st.caption(f"Sur {period} mois")
        
        st.markdown("---")
    
    # Critical Factors - Enhanced display
    if result.get("critical_factors"):
        st.subheader("⚠️ Ce qu'il faut prendre en compte")
        st.write("Avant de valider cette décision, plusieurs facteurs critiques doivent être évalués :")
        st.markdown("")
        
        for idx, factor in enumerate(result["critical_factors"], 1):
            if isinstance(factor, dict):
                factor_number = factor.get("number", idx)
                factor_name = factor.get("factor", "Factor")
                factor_desc = factor.get("description", "")
                
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.markdown(f"### {factor_number}")
                with col2:
                    st.markdown(f"**{factor_name}**")
                    # Display full description with markdown to preserve paragraph structure
                    if factor_desc:
                        st.markdown(factor_desc)
                    else:
                        st.write("Description non disponible")
            else:
                st.write(f"**{idx}. {factor}**")
        
        st.markdown("---")
    
    # Current Context - Enhanced display
    if result.get("current_context"):
        st.subheader("🏢 Contexte actuel de votre entreprise")
        context = result["current_context"]
        
        # Check if context has missing data status
        if isinstance(context, dict) and context.get("status") == "missing_data":
            st.warning("⚠️ Analysis pending - missing data required for this step")
            st.info("Please upload the required files below to complete this analysis step.")
        else:
            st.write("Votre situation financière actuelle présente des forces et des fragilités :")
            st.markdown("")
            
            col1, col2 = st.columns(2)
            with col1:
                if context.get("strengths"):
                    st.markdown("**Points forts**")
                    for strength in context["strengths"]:
                        st.success(f"✓ {strength}")
            
            with col2:
                if context.get("weaknesses"):
                    st.markdown("**Points d'attention**")
                    for weakness in context["weaknesses"]:
                        st.warning(f"⚠ {weakness}")
            
            if context.get("summary"):
                st.markdown("")
                st.write(context["summary"])
        
        st.markdown("---")
    
    # Scenarios - Enhanced display
    if result.get("scenarios"):
        st.subheader("🔮 Possibilités et Prédictions")
        st.write("Voici ce qui pourrait se passer selon différents scénarios :")
        st.markdown("")
        
        scenarios = result["scenarios"]
        
        # Display main scenarios (optimistic, realistic, pessimistic)
        scenario_order = ["optimistic", "realistic", "pessimistic"]
        scenario_labels = {
            "optimistic": "Scénario Optimiste",
            "realistic": "Scénario Réaliste",
            "pessimistic": "Scénario Pessimiste"
        }
        
        for scenario_name in scenario_order:
            if scenario_name in scenarios:
                scenario_data = scenarios[scenario_name]
                if isinstance(scenario_data, dict):
                    st.markdown(f"**{scenario_labels.get(scenario_name, scenario_name.title())}**")
                    # Display full narrative description with markdown formatting
                    description = scenario_data.get("description", "")
                    if description:
                        # Use markdown to preserve paragraph structure
                        st.markdown(description)
                    else:
                        st.write("Description non disponible")
                    
                    # Show milestones if available (as supplementary info, not replacing description)
                    if scenario_data.get("key_milestones"):
                        st.caption("**Points clés :** " + " | ".join(scenario_data["key_milestones"]))
                    
                    # Show risk periods if available (as supplementary info)
                    if scenario_data.get("risk_periods"):
                        st.caption("⚠️ **Périodes à risque :** " + " | ".join(scenario_data["risk_periods"]))
                    
                    st.markdown("")
        
        # Display best case and worst case summaries if available
        if scenarios.get("best_case"):
            st.markdown("**Meilleur Cas**")
            st.info(scenarios["best_case"])
            st.markdown("")
        
        if scenarios.get("worst_case"):
            st.markdown("**Pire Cas**")
            st.error(scenarios["worst_case"])
            st.markdown("")
        
        st.markdown("---")
    
    # Recommended Actions - Enhanced display
    if result.get("recommended_actions"):
        st.subheader("✅ Actions Recommandées")
        st.write("Pour sécuriser cette décision, voici les actions prioritaires :")
        st.markdown("")
        
        actions = result["recommended_actions"]
        
        # Group by priority
        critical = [a for a in actions if isinstance(a, dict) and a.get("priority") == "critical"]
        important = [a for a in actions if isinstance(a, dict) and a.get("priority") == "important"]
        recommended = [a for a in actions if isinstance(a, dict) and a.get("priority") == "recommended"]
        
        if critical:
            st.markdown("**Critique**")
            for action in critical:
                action_text = action.get('action', '')
                impact_text = action.get('impact', '')
                
                # Display action with full text (may contain multiple lines)
                st.error(f"• {action_text}")
                
                # Display impact prominently if available
                if impact_text:
                    st.caption(f"**{impact_text}**")
                
                if action.get('timeline'):
                    st.caption(f"  📅 Timeline: {action['timeline']}")
            st.markdown("")
        
        if important:
            st.markdown("**Important**")
            for action in important:
                action_text = action.get('action', '')
                impact_text = action.get('impact', '')
                
                st.warning(f"• {action_text}")
                
                if impact_text:
                    st.caption(f"**{impact_text}**")
                
                if action.get('timeline'):
                    st.caption(f"  📅 Timeline: {action['timeline']}")
            st.markdown("")
        
        if recommended:
            st.markdown("**Recommandé**")
            for action in recommended:
                action_text = action.get('action', '')
                impact_text = action.get('impact', '')
                
                st.info(f"• {action_text}")
                
                if impact_text:
                    st.caption(f"**{impact_text}**")
                
                if action.get('timeline'):
                    st.caption(f"  📅 Timeline: {action['timeline']}")
        
        st.markdown("---")
    
    # Alternatives - Enhanced display
    if result.get("alternatives"):
        st.subheader("🔄 Alternatives Stratégiques")
        st.write("Si cette décision vous semble trop risquée, voici des alternatives adaptées à votre situation :")
        st.markdown("")
        
        alternatives = result["alternatives"]
        
        for idx, alt in enumerate(alternatives, 1):
            if isinstance(alt, dict):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Alternative {idx} : {alt.get('name', 'Alternative')}**")
                    # Display full description with markdown to preserve formatting
                    description = alt.get("description", "")
                    if description:
                        st.markdown(description)
                    else:
                        st.write("Description non disponible")
                    if alt.get("pros_cons"):
                        st.caption(f"**Pros/Cons:** {alt['pros_cons']}")
                with col2:
                    if alt.get("impact"):
                        st.markdown("**Impact tréso :**")
                        st.caption(f"{alt['impact']}")
            else:
                st.write(f"**Alternative {idx}:** {alt}")
        
        st.markdown("---")
    
    # Fallback: Display full analysis text if structured extraction seems incomplete
    full_text = result.get("full_analysis_text", "")
    if full_text and len(full_text) > 500:
        # Check if we've displayed meaningful structured content
        has_structured_content = (
            result.get("key_metrics") or
            result.get("critical_factors") or
            result.get("current_context") or
            result.get("scenarios") or
            result.get("recommended_actions") or
            result.get("alternatives")
        )
        
        # If structured content is sparse but we have substantial text, show it
        if not has_structured_content or len(full_text) > 2000:
            st.subheader("📄 Complete Analysis Report")
            with st.expander("View Full Analysis Text", expanded=(not has_structured_content)):
                st.markdown(full_text)
            
            # Also show execution outputs if available (may contain additional insights)
            execution_outputs = result.get("execution_outputs", [])
            if execution_outputs:
                with st.expander("📊 Execution Results & Calculations", expanded=False):
                    for idx, output in enumerate(execution_outputs, 1):
                        if output and len(str(output)) > 50:  # Only show substantial outputs
                            st.write(f"**Output {idx}:**")
                            output_str = str(output)
                            if len(output_str) > 2000:
                                st.code(output_str[:2000] + "\n\n... (truncated)", language="text")
                            else:
                                st.code(output_str, language="text")
            st.markdown("---")
    
    # Charts - Enhanced display
    if result.get("charts"):
        st.subheader("📊 Projections Multi-Scénarios")
        st.write("Visualisation de tous les scénarios possibles pour cette décision stratégique")
        st.markdown("")
        
        charts = result["charts"]
        
        num_charts = len(charts)
        cols_per_row = 1 if num_charts == 1 else 2
        
        for idx, chart in enumerate(charts):
            chart_col = idx % cols_per_row
            
            if idx % cols_per_row == 0:
                chart_cols = st.columns(cols_per_row)
            
            with chart_cols[chart_col]:
                chart_title = chart.get("filename", f"Chart {idx + 1}")
                mime_type = chart.get("mime_type", "image/png")
                
                try:
                    image_data = None
                    data = chart.get("data")
                    
                    if data:
                        if isinstance(data, bytes):
                            image_data = data
                        elif isinstance(data, str):
                            try:
                                image_data = base64.b64decode(data)
                            except Exception:
                                st.warning(f"Unrecognized data format for {chart_title}")
                                continue
                        else:
                            st.warning(f"Unsupported data type for {chart_title}")
                            continue
                        
                        if image_data:
                            # Enhanced chart display
                            st.image(image_data, caption=chart_title, use_container_width=True)
                            
                            # Download button
                            st.download_button(
                                label=f"📥 Télécharger {chart_title}",
                                data=image_data,
                                file_name=chart_title,
                                mime=mime_type,
                                key=f"download_chart_{idx}"
                            )
                    else:
                        st.warning(f"No data found for chart {chart_title}")
                        
                except Exception as e:
                    st.error(f"Error displaying chart {chart_title}: {str(e)}")
        
        st.markdown("---")


def main():
    st.title("📊 Financial Decision Analyzer")
    st.markdown("""
    Upload your financial files and ask a decision question. The AI will analyze the financial impact
    and provide projections, scenarios, and recommendations.
    """)
    
    # API key verification
    if not os.getenv("gemini_token"):
        st.error("⚠️ Missing API key: Add `gemini_token` to your `.env` file")
        st.stop()
    
    # ==========================================
    # SECTION 1 : MULTI-FILE UPLOAD
    # ==========================================
    st.header("📁 1. Upload Financial Files")
    
    uploaded_files = st.file_uploader(
        "Select Excel or CSV files",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Upload multiple files (cash flow, balance sheets, income statements, etc.)"
    )
    
    # Add new files to session
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Check if file already exists
            file_exists = any(
                file_data["name"] == uploaded_file.name 
                for file_data in st.session_state.uploaded_files.values()
            )
            
            if not file_exists:
                try:
                    add_file_to_session(uploaded_file)
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Display uploaded files
    if st.session_state.uploaded_files:
        st.subheader(f"Uploaded Files ({len(st.session_state.uploaded_files)})")
        
        for file_id, file_data in st.session_state.uploaded_files.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                file_info = file_data.get("info", {})
                if "error" in file_info:
                    st.error(f"❌ {file_data['name']} - Error: {file_info['error']}")
                else:
                    st.success(f"✅ {file_data['name']}")
                    with st.expander("View metadata"):
                        col1_meta, col2_meta, col3_meta = st.columns(3)
                        with col1_meta:
                            st.metric("Columns", file_info.get("num_columns", 0))
                        with col2_meta:
                            st.metric("Rows", file_info.get("num_rows", 0))
                        with col3_meta:
                            if file_info.get("file_size_mb"):
                                st.metric("Size", f"{file_info['file_size_mb']} MB")
                        
                        st.write("**Columns:**", file_info.get("columns", []))
            
            with col2:
                if st.button("🗑️ Remove", key=f"remove_{file_id}"):
                    remove_file_from_session(file_id)
            
            with col3:
                if file_info.get("has_total_rows"):
                    st.warning(f"⚠️ {file_info.get('total_rows_count', 0)} total row(s)")
    else:
        st.info("No files uploaded yet. Upload financial files to begin analysis.")
    
    # ==========================================
    # SECTION 2 : DECISION QUESTION
    # ==========================================
    st.header("💡 2. Your Decision Question")
    
    decision_question = st.text_area(
        "What decision do you want to analyze?",
        value=st.session_state.decision_question or "",
        height=100,
        help="Example: 'Can I hire a sales director at 60k annual gross in 3 months?'",
        placeholder="Enter your financial decision question here..."
    )
    
    if decision_question:
        st.session_state.decision_question = decision_question
    
    # Analysis buttons
    col1, col2 = st.columns(2)
    with col1:
        analyze_button = st.button(
            "🚀 Analyze Decision (Full)",
            type="primary",
            disabled=not decision_question or len(st.session_state.uploaded_files) == 0,
            use_container_width=True,
            help="Run complete analysis: requirements extraction, data check, and full analysis"
        )
    with col2:
        audit_button = st.button(
            "🔍 Audit Requirements & Availability",
            disabled=not decision_question or len(st.session_state.uploaded_files) == 0,
            use_container_width=True,
            help="Only extract requirements and check data availability (no full analysis)"
        )
    
    # ==========================================
    # SECTION 3 : AUDIT WORKFLOW (Requirements & Availability)
    # ==========================================
    if audit_button and decision_question:
        st.header("🔍 Audit: Requirements & Data Availability")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize services
            status_text.text("Initializing services...")
            progress_bar.progress(10)
            add_log("Starting audit: requirements extraction")
            
            gemini_service = GeminiCodeExecutionService()
            decision_analyzer = DecisionAnalyzer(gemini_service)
            
            # Step 1: Analyze question requirements
            status_text.text("Step 1/2: Analyzing question and identifying data needs...")
            progress_bar.progress(30)
            add_log("Step 1: Analyzing question requirements")
            
            requirements = asyncio.run(decision_analyzer.analyze_question_requirements(decision_question))
            st.session_state.requirements = requirements
            
            # Step 2: Check data availability
            status_text.text("Step 2/2: Checking data availability...")
            progress_bar.progress(70)
            add_log("Step 2: Checking data availability")
            
            data_availability = asyncio.run(
                decision_analyzer.check_data_availability(requirements, st.session_state.uploaded_files)
            )
            st.session_state.data_availability = data_availability
            
            progress_bar.progress(100)
            status_text.text("✅ Audit completed!")
            st.success("Requirements and availability check completed!")
            
            import time
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error during audit: {str(e)}")
            add_log(f"Audit error: {str(e)}", "ERROR")
            st.exception(e)
            progress_bar.empty()
            status_text.empty()
    
    # ==========================================
    # SECTION 3.5 : AUDIT RESULTS DISPLAY
    # ==========================================
    if st.session_state.requirements or st.session_state.data_availability:
        st.header("📊 Audit Results: Requirements & Availability")
        
        audit_tab1, audit_tab2, audit_tab3 = st.tabs([
            "📋 Extracted Requirements",
            "✅ Data Availability Check",
            "📈 Summary"
        ])
        
        with audit_tab1:
            st.subheader("Data Requirements Extracted from Question")
            
            if st.session_state.requirements:
                requirements = st.session_state.requirements
                
                # Decision Summary
                if requirements.get("decision_summary"):
                    summary = requirements["decision_summary"]
                    st.write("### 💡 Decision Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Question:** {summary.get('question', 'N/A')}")
                    with col2:
                        st.write(f"**Importance:** {summary.get('importance', 'N/A')}")
                    st.write(f"**Description:** {summary.get('description', 'N/A')}")
                    st.markdown("---")
                
                # Data Requirements
                data_reqs = requirements.get("data_requirements", [])
                if data_reqs:
                    st.write(f"### 📊 Data Requirements ({len(data_reqs)} identified)")
                    
                    for idx, req in enumerate(data_reqs, 1):
                        with st.expander(
                            f"Requirement #{idx}: {req.get('requirement_id', f'req_{idx}')} "
                            f"{'🔴 Critical' if req.get('critical') else '🟡 Optional'}",
                            expanded=False
                        ):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Data Type:** `{req.get('data_type', 'N/A')}`")
                                st.write(f"**Description:** {req.get('description', 'N/A')}")
                                st.write(f"**Why Needed:** {req.get('why_needed', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Where Found:** {req.get('where_found', 'N/A')}")
                                st.write(f"**Critical:** {'Yes ⚠️' if req.get('critical') else 'No'}")
                            
                            columns_needed = req.get('columns_needed', [])
                            if columns_needed:
                                st.write("**Columns Needed:**")
                                st.code(', '.join(columns_needed), language=None)
                else:
                    st.info("No data requirements identified")
                
                # Analysis Steps
                if requirements.get("analysis_steps"):
                    st.write("### 🔄 Planned Analysis Steps")
                    for idx, step in enumerate(requirements.get("analysis_steps", []), 1):
                        st.write(f"{idx}. {step}")
                
                # Raw JSON
                with st.expander("🔧 Raw Requirements JSON", expanded=False):
                    import json
                    st.json(requirements)
            else:
                st.info("No requirements extracted yet. Run the audit to extract requirements.")
        
        with audit_tab2:
            st.subheader("Data Availability Analysis")
            
            if st.session_state.data_availability:
                availability = st.session_state.data_availability
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Available", len(availability.get("available", [])))
                with col2:
                    st.metric("Partial", len(availability.get("partial", [])))
                with col3:
                    st.metric("Missing", len(availability.get("missing", [])))
                with col4:
                    analysis_type = availability.get("analysis_type", "unknown")
                    type_icon = {
                        "full": "🟢",
                        "partial": "🟡",
                        "advisory_only": "🔴"
                    }.get(analysis_type, "⚪")
                    st.metric("Analysis Type", f"{type_icon} {analysis_type}")
                
                st.markdown("---")
                
                # Available requirements
                available_reqs = availability.get("available", [])
                if available_reqs:
                    st.write(f"### ✅ Available Data ({len(available_reqs)})")
                    for req in available_reqs:
                        with st.expander(
                            f"✅ {req.get('requirement_id', 'Unknown')} - Match Score: {req.get('match_score', 0):.1%}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            if req.get('best_match'):
                                match = req['best_match']
                                st.success(f"📁 Found in: {match.get('file_name', 'Unknown')}")
                                st.write(f"**Match Score:** {match.get('match_score', 0):.1%}")
                                
                                matched_cols = match.get('matched_columns', {})
                                if matched_cols:
                                    st.write("**Matched Columns:**")
                                    for req_col, match_info in matched_cols.items():
                                        st.code(f"{req_col} → {match_info.get('matched_column', 'N/A')} "
                                               f"(score: {match_info.get('score', 0):.1%})", language=None)
                                
                                unmatched = match.get('unmatched_columns', [])
                                if unmatched:
                                    st.warning(f"⚠️ Unmatched columns: {', '.join(unmatched)}")
                
                # Partial requirements
                partial_reqs = availability.get("partial", [])
                if partial_reqs:
                    st.write(f"### 🟡 Partially Available ({len(partial_reqs)})")
                    for req in partial_reqs:
                        with st.expander(
                            f"🟡 {req.get('requirement_id', 'Unknown')} - Match Score: {req.get('match_score', 0):.1%}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            if req.get('best_match'):
                                match = req['best_match']
                                st.warning(f"📁 Partial match in: {match.get('file_name', 'Unknown')}")
                                st.write(f"**Match Score:** {match.get('match_score', 0):.1%}")
                                
                                matched_cols = match.get('matched_columns', {})
                                if matched_cols:
                                    st.write("**Matched Columns:**")
                                    for req_col, match_info in matched_cols.items():
                                        st.code(f"{req_col} → {match_info.get('matched_column', 'N/A')}", language=None)
                                
                                unmatched = match.get('unmatched_columns', [])
                                if unmatched:
                                    st.error(f"❌ Missing columns: {', '.join(unmatched)}")
                
                # Missing requirements
                missing_reqs = availability.get("missing", [])
                if missing_reqs:
                    st.write(f"### ❌ Missing Data ({len(missing_reqs)})")
                    for req in missing_reqs:
                        with st.expander(
                            f"❌ {req.get('requirement_id', 'Unknown')} "
                            f"{'🔴 CRITICAL' if req.get('critical') else ''}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            st.write(f"**Data Type:** `{req.get('data_type', 'N/A')}`")
                            
                            if req.get('where_found'):
                                st.info(f"📍 **Where to find:** {req['where_found']}")
                            
                            columns_needed = req.get('columns_needed', [])
                            if columns_needed:
                                st.write("**Required Columns:**")
                                st.code(', '.join(columns_needed), language=None)
                            
                            if req.get('critical'):
                                st.error("⚠️ **This is a CRITICAL requirement** - analysis may be limited without this data")
                
                # Critical missing
                critical_missing = availability.get("critical_missing", [])
                if critical_missing:
                    st.error(f"### 🚨 Critical Missing Data ({len(critical_missing)})")
                    st.warning("⚠️ The following CRITICAL requirements are missing. Full analysis may not be possible.")
                    for req in critical_missing:
                        st.write(f"- **{req.get('requirement_id', 'Unknown')}:** {req.get('description', 'N/A')}")
                
                # Raw JSON
                with st.expander("🔧 Raw Availability JSON", expanded=False):
                    import json
                    st.json(availability)
            else:
                st.info("No availability data yet. Run the audit to check data availability.")
        
        with audit_tab3:
            st.subheader("Audit Summary")
            
            if st.session_state.requirements and st.session_state.data_availability:
                requirements = st.session_state.requirements
                availability = st.session_state.data_availability
                
                # Overall status
                analysis_type = availability.get("analysis_type", "unknown")
                
                if analysis_type == "full":
                    st.success("✅ **Full Analysis Possible**")
                    st.write("All required data is available. You can proceed with full analysis.")
                elif analysis_type == "partial":
                    st.warning("🟡 **Partial Analysis Possible**")
                    st.write("Some data is missing, but partial analysis can still be performed.")
                else:
                    st.error("❌ **Advisory Analysis Only**")
                    st.write("Critical data is missing. Only general guidance can be provided.")
                
                st.markdown("---")
                
                # Statistics
                st.write("### 📊 Statistics")
                total_reqs = len(requirements.get("data_requirements", []))
                available_count = len(availability.get("available", []))
                partial_count = len(availability.get("partial", []))
                missing_count = len(availability.get("missing", []))
                
                if total_reqs > 0:
                    st.write(f"- **Total Requirements:** {total_reqs}")
                    st.write(f"- **Available:** {available_count} ({available_count/total_reqs*100:.1f}%)")
                    st.write(f"- **Partially Available:** {partial_count} ({partial_count/total_reqs*100:.1f}%)")
                    st.write(f"- **Missing:** {missing_count} ({missing_count/total_reqs*100:.1f}%)")
                
                # Recommendations
                st.write("### 💡 Recommendations")
                if missing_count > 0:
                    critical_missing = availability.get("critical_missing", [])
                    if critical_missing:
                        st.error("**Action Required:** Upload files containing the critical missing data to enable full analysis.")
                    else:
                        st.warning("**Optional:** Consider uploading files with missing data for more complete analysis.")
                
                if analysis_type == "full":
                    st.success("**Ready:** You can proceed with full analysis using the 'Analyze Decision (Full)' button.")
    
    # ==========================================
    # SECTION 4 : ANALYSIS WORKFLOW
    # ==========================================
    if analyze_button and decision_question:
        st.header("🔍 3. Analysis in Progress...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize services
            status_text.text("Initializing services...")
            progress_bar.progress(5)
            add_log("Initializing services")
            
            gemini_service = GeminiCodeExecutionService()
            decision_analyzer = DecisionAnalyzer(gemini_service)
            
            # Combined Step 1+2: Analyze question and adapt structure to data
            status_text.text("Step 1/2: Analyzing question and adapting structure to data...")
            progress_bar.progress(20)
            add_log("Step 1+2: Combined analysis")
            
            combined_result = asyncio.run(
                decision_analyzer.analyze_question_and_adapt_structure(
                    decision_question,
                    st.session_state.uploaded_files
                )
            )
            
            # Extract components from combined result
            structure_definition = {
                "decision_summary": combined_result.get("decision_summary", {}),
                "expected_structure": combined_result.get("final_structure", {})
            }
            adapted_structure = {
                "final_structure": combined_result.get("final_structure", {}),
                "file_analysis": combined_result.get("file_analysis", {})
            }
            
            st.session_state.structure_definition = structure_definition
            st.session_state.adapted_structure = adapted_structure
            
            # Check for missing data requests from Step 1
            missing_data_requests = combined_result.get("final_structure", {}).get("missing_data_requests", [])
            critical_missing = [r for r in missing_data_requests if r.get("priority") == "high" and not r.get("can_proceed_without", True)]
            
            # If there are missing data requests AND user hasn't chosen partial analysis, show request UI
            # Show UI if: (1) there are any missing requests, AND (2) user hasn't clicked "partial analysis" yet
            should_show_missing_data_ui = (
                missing_data_requests and 
                not st.session_state.get("partial_analysis", False)
            )
            
            if should_show_missing_data_ui:
                progress_bar.progress(40)
                status_text.text("⚠️ Additional data needed for complete analysis")
                
                st.markdown("---")
                st.header("📥 Données Complémentaires Requises")
                
                st.warning("**Pour une analyse complète et précise**, les données suivantes sont nécessaires :")
                
                # Display missing data requests
                for idx, request in enumerate(missing_data_requests):
                    priority = request.get("priority", "medium")
                    priority_badges = {
                        "high": "🔴 **Priorité Haute**",
                        "medium": "🟡 **Priorité Moyenne**",
                        "low": "🟢 **Priorité Basse**"
                    }
                    
                    with st.expander(f"{priority_badges.get(priority, '🟡 Priorité Moyenne')} - {request.get('data_type', 'Données')}", expanded=(priority == "high")):
                        st.markdown(f"**Type de données :** {request.get('data_type', 'N/A')}")
                        st.markdown(f"**Pourquoi nécessaire :** {request.get('why_needed', 'N/A')}")
                        st.markdown(f"**Où trouver :** {request.get('where_found', 'N/A')}")
                        
                        columns_needed = request.get('columns_needed', [])
                        if columns_needed:
                            st.markdown(f"**Colonnes nécessaires :** {', '.join(columns_needed)}")
                        
                        if request.get('can_proceed_without', True):
                            st.info("ℹ️ Analyse partielle possible sans ces données")
                        else:
                            st.error("⚠️ Ces données sont critiques pour l'analyse")
                
                # File uploader for missing data
                st.markdown("---")
                st.subheader("📎 Ajouter les fichiers manquants")
                
                additional_files = st.file_uploader(
                    "Glissez-déposez ou sélectionnez les fichiers contenant les données requises",
                    type=['xlsx', 'xls', 'csv'],
                    accept_multiple_files=True,
                    key="missing_data_uploader",
                    help="Ajoutez les fichiers Excel/CSV contenant les données demandées ci-dessus"
                )
                
                # Add additional files to session
                if additional_files:
                    for uploaded_file in additional_files:
                        file_exists = any(
                            file_data["name"] == uploaded_file.name 
                            for file_data in st.session_state.uploaded_files.values()
                        )
                        
                        if not file_exists:
                            try:
                                add_file_to_session(uploaded_file)
                                st.success(f"✅ Fichier ajouté : {uploaded_file.name}")
                            except Exception as e:
                                st.error(f"❌ Erreur lors de l'ajout de {uploaded_file.name}: {str(e)}")
                
                # Options to continue
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Relancer l'analyse avec les nouveaux fichiers", type="primary", use_container_width=True):
                        # Clear the analysis result to trigger re-analysis
                        if "analysis_result" in st.session_state:
                            del st.session_state.analysis_result
                        st.rerun()
                
                with col2:
                    if st.button("📊 Continuer avec analyse partielle", use_container_width=True):
                        # Mark that we're proceeding with partial analysis
                        st.session_state.partial_analysis = True
                        # Clear progress bar and continue to Step 2
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                
                # Stop here - wait for user action (unless button was clicked)
                progress_bar.empty()
                status_text.empty()
                st.stop()
            
            # Step 2 (now Step 2/2): Generate final report
            # Reset partial_analysis flag after using it (for next analysis)
            if st.session_state.get("partial_analysis", False):
                st.session_state.partial_analysis = False
            
            has_files = len(st.session_state.uploaded_files) > 0
            
            if has_files:
                status_text.text("Step 2/2: Generating final report...")
                progress_bar.progress(60)
                add_log("Step 2: Generating final report")
                
                result = asyncio.run(
                    decision_analyzer.generate_final_report(
                        decision_question,
                        adapted_structure,
                        st.session_state.uploaded_files,
                        structure_definition.get("decision_summary", {})
                    )
                )
                
                progress_bar.progress(95)
                status_text.text("Formatting results...")
            else:
                # No files uploaded - advisory only
                status_text.text("Step 2/2: No files - generating advisory analysis...")
                progress_bar.progress(50)
                add_log("Step 2: Generating advisory-only analysis")
                
                st.info("ℹ️ No financial data files uploaded. Generating general financial guidance.")
                
                result = asyncio.run(decision_analyzer.analyze_decision_advisory(decision_question))
                progress_bar.progress(90)
            
            st.session_state.analysis_result = result
            add_log("Analysis completed successfully")
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis completed!")
            st.success("Analysis completed successfully!")
            
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            add_log(f"Analysis error: {str(e)}", "ERROR")
            st.exception(e)
            progress_bar.empty()
            status_text.empty()
    
    # ==========================================
    # SECTION 4 : RESULTS DISPLAY
    # ==========================================
    
    # Show audit section if available (even if full analysis was done)
    if st.session_state.requirements or st.session_state.data_availability:
        if st.session_state.analysis_result:
            st.markdown("---")
        
        st.header("📊 Audit: Requirements & Data Availability")
        
        audit_tab1, audit_tab2, audit_tab3 = st.tabs([
            "📋 Extracted Requirements",
            "✅ Data Availability Check",
            "📈 Summary"
        ])
        
        with audit_tab1:
            st.subheader("Data Requirements Extracted from Question")
            
            if st.session_state.requirements:
                requirements = st.session_state.requirements
                
                # Decision Summary
                if requirements.get("decision_summary"):
                    summary = requirements["decision_summary"]
                    st.write("### 💡 Decision Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Question:** {summary.get('question', 'N/A')}")
                    with col2:
                        st.write(f"**Importance:** {summary.get('importance', 'N/A')}")
                    st.write(f"**Description:** {summary.get('description', 'N/A')}")
                    st.markdown("---")
                
                # Data Requirements
                data_reqs = requirements.get("data_requirements", [])
                if data_reqs:
                    st.write(f"### 📊 Data Requirements ({len(data_reqs)} identified)")
                    
                    for idx, req in enumerate(data_reqs, 1):
                        with st.expander(
                            f"Requirement #{idx}: {req.get('requirement_id', f'req_{idx}')} "
                            f"{'🔴 Critical' if req.get('critical') else '🟡 Optional'}",
                            expanded=False
                        ):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Data Type:** `{req.get('data_type', 'N/A')}`")
                                st.write(f"**Description:** {req.get('description', 'N/A')}")
                                st.write(f"**Why Needed:** {req.get('why_needed', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Where Found:** {req.get('where_found', 'N/A')}")
                                st.write(f"**Critical:** {'Yes ⚠️' if req.get('critical') else 'No'}")
                            
                            columns_needed = req.get('columns_needed', [])
                            if columns_needed:
                                st.write("**Columns Needed:**")
                                st.code(', '.join(columns_needed), language=None)
                else:
                    st.info("No data requirements identified")
                
                # Analysis Steps
                if requirements.get("analysis_steps"):
                    st.write("### 🔄 Planned Analysis Steps")
                    for idx, step in enumerate(requirements.get("analysis_steps", []), 1):
                        st.write(f"{idx}. {step}")
                
                # Raw JSON
                with st.expander("🔧 Raw Requirements JSON", expanded=False):
                    import json
                    st.json(requirements)
            else:
                st.info("No requirements extracted yet. Run the audit to extract requirements.")
        
        with audit_tab2:
            st.subheader("Data Availability Analysis")
            
            if st.session_state.data_availability:
                availability = st.session_state.data_availability
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Available", len(availability.get("available", [])))
                with col2:
                    st.metric("Partial", len(availability.get("partial", [])))
                with col3:
                    st.metric("Missing", len(availability.get("missing", [])))
                with col4:
                    analysis_type = availability.get("analysis_type", "unknown")
                    type_icon = {
                        "full": "🟢",
                        "partial": "🟡",
                        "advisory_only": "🔴"
                    }.get(analysis_type, "⚪")
                    st.metric("Analysis Type", f"{type_icon} {analysis_type}")
                
                st.markdown("---")
                
                # Available requirements
                available_reqs = availability.get("available", [])
                if available_reqs:
                    st.write(f"### ✅ Available Data ({len(available_reqs)})")
                    for req in available_reqs:
                        with st.expander(
                            f"✅ {req.get('requirement_id', 'Unknown')} - Match Score: {req.get('match_score', 0):.1%}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            if req.get('best_match'):
                                match = req['best_match']
                                st.success(f"📁 Found in: {match.get('file_name', 'Unknown')}")
                                st.write(f"**Match Score:** {match.get('match_score', 0):.1%}")
                                
                                matched_cols = match.get('matched_columns', {})
                                if matched_cols:
                                    st.write("**Matched Columns:**")
                                    for req_col, match_info in matched_cols.items():
                                        st.code(f"{req_col} → {match_info.get('matched_column', 'N/A')} "
                                               f"(score: {match_info.get('score', 0):.1%})", language=None)
                                
                                unmatched = match.get('unmatched_columns', [])
                                if unmatched:
                                    st.warning(f"⚠️ Unmatched columns: {', '.join(unmatched)}")
                
                # Partial requirements
                partial_reqs = availability.get("partial", [])
                if partial_reqs:
                    st.write(f"### 🟡 Partially Available ({len(partial_reqs)})")
                    for req in partial_reqs:
                        with st.expander(
                            f"🟡 {req.get('requirement_id', 'Unknown')} - Match Score: {req.get('match_score', 0):.1%}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            if req.get('best_match'):
                                match = req['best_match']
                                st.warning(f"📁 Partial match in: {match.get('file_name', 'Unknown')}")
                                st.write(f"**Match Score:** {match.get('match_score', 0):.1%}")
                                
                                matched_cols = match.get('matched_columns', {})
                                if matched_cols:
                                    st.write("**Matched Columns:**")
                                    for req_col, match_info in matched_cols.items():
                                        st.code(f"{req_col} → {match_info.get('matched_column', 'N/A')}", language=None)
                                
                                unmatched = match.get('unmatched_columns', [])
                                if unmatched:
                                    st.error(f"❌ Missing columns: {', '.join(unmatched)}")
                
                # Missing requirements
                missing_reqs = availability.get("missing", [])
                if missing_reqs:
                    st.write(f"### ❌ Missing Data ({len(missing_reqs)})")
                    for req in missing_reqs:
                        with st.expander(
                            f"❌ {req.get('requirement_id', 'Unknown')} "
                            f"{'🔴 CRITICAL' if req.get('critical') else ''}",
                            expanded=False
                        ):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            st.write(f"**Data Type:** `{req.get('data_type', 'N/A')}`")
                            
                            if req.get('where_found'):
                                st.info(f"📍 **Where to find:** {req['where_found']}")
                            
                            columns_needed = req.get('columns_needed', [])
                            if columns_needed:
                                st.write("**Required Columns:**")
                                st.code(', '.join(columns_needed), language=None)
                            
                            if req.get('critical'):
                                st.error("⚠️ **This is a CRITICAL requirement** - analysis may be limited without this data")
                
                # Critical missing
                critical_missing = availability.get("critical_missing", [])
                if critical_missing:
                    st.error(f"### 🚨 Critical Missing Data ({len(critical_missing)})")
                    st.warning("⚠️ The following CRITICAL requirements are missing. Full analysis may not be possible.")
                    for req in critical_missing:
                        st.write(f"- **{req.get('requirement_id', 'Unknown')}:** {req.get('description', 'N/A')}")
                
                # Raw JSON
                with st.expander("🔧 Raw Availability JSON", expanded=False):
                    import json
                    st.json(availability)
            else:
                st.info("No availability data yet. Run the audit to check data availability.")
        
        with audit_tab3:
            st.subheader("Audit Summary")
            
            if st.session_state.requirements and st.session_state.data_availability:
                requirements = st.session_state.requirements
                availability = st.session_state.data_availability
                
                # Overall status
                analysis_type = availability.get("analysis_type", "unknown")
                
                if analysis_type == "full":
                    st.success("✅ **Full Analysis Possible**")
                    st.write("All required data is available. You can proceed with full analysis.")
                elif analysis_type == "partial":
                    st.warning("🟡 **Partial Analysis Possible**")
                    st.write("Some data is missing, but partial analysis can still be performed.")
                else:
                    st.error("❌ **Advisory Analysis Only**")
                    st.write("Critical data is missing. Only general guidance can be provided.")
                
                st.markdown("---")
                
                # Statistics
                st.write("### 📊 Statistics")
                total_reqs = len(requirements.get("data_requirements", []))
                available_count = len(availability.get("available", []))
                partial_count = len(availability.get("partial", []))
                missing_count = len(availability.get("missing", []))
                
                if total_reqs > 0:
                    st.write(f"- **Total Requirements:** {total_reqs}")
                    st.write(f"- **Available:** {available_count} ({available_count/total_reqs*100:.1f}%)")
                    st.write(f"- **Partially Available:** {partial_count} ({partial_count/total_reqs*100:.1f}%)")
                    st.write(f"- **Missing:** {missing_count} ({missing_count/total_reqs*100:.1f}%)")
                
                # Recommendations
                st.write("### 💡 Recommendations")
                if missing_count > 0:
                    critical_missing = availability.get("critical_missing", [])
                    if critical_missing:
                        st.error("**Action Required:** Upload files containing the critical missing data to enable full analysis.")
                    else:
                        st.warning("**Optional:** Consider uploading files with missing data for more complete analysis.")
                
                if analysis_type == "full":
                    st.success("**Ready:** You can proceed with full analysis using the 'Analyze Decision (Full)' button.")
    
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        # Display file content analysis if available
        if result.get("file_content_analysis") or st.session_state.get("file_content_analysis"):
            file_analysis = result.get("file_content_analysis") or st.session_state.get("file_content_analysis")
            
            st.header("📊 File Content Analysis")
            with st.expander("🔍 What Data Was Found in Your Files", expanded=True):
                if file_analysis.get("files_analyzed"):
                    st.write(f"**Files analyzed:** {', '.join(file_analysis.get('files_analyzed', []))}")
                
                if file_analysis.get("available_data_types"):
                    st.write(f"**Available data types:** {', '.join(file_analysis['available_data_types'])}")
                else:
                    st.write("**Available data types:** General financial data (structure being analyzed)")
                
                if file_analysis.get("possible_analyses"):
                    st.write("**Possible analyses identified:**")
                    for analysis in file_analysis["possible_analyses"]:
                        st.success(f"✓ {analysis}")
                
                if file_analysis.get("columns_found"):
                    st.write("**Columns found in files:**")
                    st.json(file_analysis["columns_found"])
                
                if file_analysis.get("time_periods"):
                    st.write("**Time periods covered:**")
                    st.json(file_analysis["time_periods"])
                
                if file_analysis.get("data_quality"):
                    quality_icon = {
                        "good": "🟢",
                        "partial": "🟡",
                        "limited": "🟠",
                        "unknown": "⚪"
                    }.get(file_analysis["data_quality"], "⚪")
                    st.write(f"**Data quality:** {quality_icon} {file_analysis['data_quality']}")
            
            st.markdown("---")
        
        # Display based on analysis type
        if result.get("analysis_type") == "advisory_only":
            st.header("📋 Financial Guidance")
            st.info("This is general financial guidance without specific data analysis.")
            
            if result.get("decision_summary"):
                summary = result["decision_summary"]
                st.write(f"**Question:** {summary.get('question', '')}")
            
            if result.get("advisory_text"):
                st.markdown(result["advisory_text"])
            
            if result.get("key_considerations"):
                st.subheader("Key Considerations")
                for consideration in result["key_considerations"]:
                    st.write(f"• {consideration}")
        else:
            display_decision_analysis(result)
        
        # Missing Data Requests Section - Light version
        if result.get("missing_data_requests"):
            st.header("📥 Données Complémentaires")
            st.info("Pour améliorer la précision de l'analyse, vous pouvez fournir les données complémentaires ci-dessous.")
            st.markdown("---")
            
            files_uploaded_for_missing = False
            
            # Sort requests by priority
            sorted_requests = sorted(
                result["missing_data_requests"],
                key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("request_priority", "medium"), 1)
            )
            
            for idx, request in enumerate(sorted_requests):
                priority = request.get("request_priority", "medium")
                priority_badges = {
                    "high": "🔴 **Priorité Haute**",
                    "medium": "🟡 **Priorité Moyenne**",
                    "low": "🟢 **Priorité Basse**"
                }
                
                with st.expander(
                    f"{priority_badges.get(priority, '')} {request['step_name']} - Données Manquantes",
                    expanded=(priority == "high")
                ):
                    st.write(f"**Pourquoi c'est important :** {request['why_important']}")
                    
                    if request.get('can_skip'):
                        st.info("ℹ️ Cette étape peut être ignorée si les données ne sont pas disponibles")
                    else:
                        st.warning("⚠️ Cette étape est requise pour une analyse complète")
                    
                    if request.get('note'):
                        st.caption(f"ℹ️ {request['note']}")
                    
                    st.markdown("**Données requises :**")
                    for req in request["missing_requirements"]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"- **{req.get('requirement_id', 'Unknown')}:** {req.get('description', '')}")
                            if req.get('where_found'):
                                st.caption(f"📍 **Où trouver :** {req['where_found']}")
                            if req.get('columns_needed'):
                                st.caption(f"📊 **Colonnes nécessaires :** {', '.join(req['columns_needed'])}")
                        with col2:
                            if req.get('critical'):
                                st.error("🔴 Critique")
                            else:
                                st.info("🟡 Optionnel")
                    
                    # File uploader for this specific missing data
                    uploaded_file = st.file_uploader(
                        f"Télécharger les données pour {request['step_name']}",
                        type=['xlsx', 'xls', 'csv'],
                        key=f"missing_data_{idx}",
                        help=f"Téléchargez un fichier contenant les données requises pour {request['step_name']}"
                    )
                    
                    if uploaded_file:
                        # Check if file already exists
                        file_exists = any(
                            file_data.get("name") == uploaded_file.name 
                            for file_data in st.session_state.uploaded_files.values()
                        )
                        
                        if not file_exists:
                            try:
                                file_id = add_file_to_session(uploaded_file)
                                st.success(f"✅ Fichier téléchargé: {uploaded_file.name}")
                                files_uploaded_for_missing = True
                            except Exception as e:
                                st.error(f"Erreur lors du téléchargement: {str(e)}")
                        else:
                            st.info(f"ℹ️ Le fichier '{uploaded_file.name}' est déjà dans la liste")
                            files_uploaded_for_missing = True
            
            # Button to continue analysis with new files
            if files_uploaded_for_missing:
                st.markdown("---")
                if st.button("🔄 Continuer l'analyse avec les nouveaux fichiers", type="primary", use_container_width=True):
                    # Re-check data availability and re-run progressive analysis
                    st.info("🔄 Réanalyse en cours avec les fichiers complémentaires...")
                    st.rerun()
        
        # Export section
        st.header("💾 Export Results")
        import json
        try:
            export_data = prepare_json_export(result)
            json_export = json.dumps(export_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Download Analysis Results (JSON)",
                data=json_export,
                file_name="decision_analysis.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Error preparing export: {str(e)}")
    
    # ==========================================
    # SECTION 5 : LOGS AND DEBUG
    # ==========================================
    st.header("📋 Logs and Debug")
    
    with st.expander("🔍 View Logs", expanded=False):
        if st.session_state.logs:
            for log in st.session_state.logs[-50:]:
                log_color = {
                    "INFO": "🔵",
                    "WARNING": "🟡",
                    "ERROR": "🔴",
                    "DEBUG": "⚪"
                }.get(log["level"], "⚪")
                st.text(f"{log_color} [{log['timestamp']}] {log['level']}: {log['message']}")
        else:
            st.info("No logs at the moment")
        
        if st.button("🗑️ Clear Logs"):
            st.session_state.logs = []
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("Financial Decision Analyzer - Powered by Gemini Code Execution")


if __name__ == "__main__":
    main()
