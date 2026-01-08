"""
Service pour interagir avec Gemini API avec Code Execution activé
"""
import google.generativeai as genai
from google.generativeai import types
import os
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import tempfile
import pandas as pd
import json
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env.local ou .env à la racine du projet
project_root = Path(__file__).parent.parent.parent.parent
env_paths = [
    project_root / '.env.local',  # Priorité à .env.local (standard Next.js)
    project_root / '.env',
    project_root / 'backend' / '.env',  # Essayer aussi dans le dossier backend
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # override=False pour garder les valeurs déjà chargées
        break

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiCodeExecutionService:
    """
    Service pour utiliser Gemini avec Code Execution
    pour analyser automatiquement les fichiers Excel financiers
    """
    
    def __init__(self):
        """Initialise le service Gemini avec la clé API"""
        api_key = os.getenv("gemini_token")
        if not api_key:
            raise ValueError("gemini_token non trouvée dans les variables d'environnement")
        
        genai.configure(api_key=api_key)
        
        # Configuration du modèle avec Code Execution activé
        # Selon la doc Gemini, on active Code Execution via tools
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",  # Modèle avec Code Execution
            tools=[{"code_execution": {}}]  # Active Code Execution
        )
        
        # Configuration du modèle normal (sans Code Execution) pour Step 2
        self.model_normal = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp"  # Même modèle mais sans Code Execution
            # Pas de tools - donc pas de Code Execution
        )
        
        # Load financial rules
        self.financial_rules = self._load_financial_rules()
        
        logger.info("Gemini service initialized with Code Execution")
        logger.info("Gemini normal model initialized (for structure analysis)")
        logger.info(f"Financial rules loaded: {len(self.financial_rules.get('document_types', {}))} document types")
    
    def _load_financial_rules(self) -> Dict[str, Any]:
        """
        Loads financial rules from JSON file
        
        Returns:
            Dict containing financial rules
        """
        try:
            rules_path = Path(__file__).parent.parent / "financial_rules.json"
            if rules_path.exists():
                with open(rules_path, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                logger.info(f"Financial rules loaded from {rules_path}")
                return rules
            else:
                logger.warning(f"Financial rules file not found: {rules_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading financial rules: {e}")
            return {}
    
    def _detect_document_type(self, file_info: Dict[str, Any]) -> Optional[str]:
        """
        Detects the financial document type based on columns and rules
        
        Args:
            file_info: File metadata (columns, types, etc.)
            
        Returns:
            Detected document type or None
        """
        if not self.financial_rules or "detection_rules" not in self.financial_rules:
            return None
        
        columns = [col.lower() for col in file_info.get("columns", [])]
        filename = file_info.get("filename", "").lower()
        
        detection_rules = self.financial_rules["detection_rules"]
        scores = {}
        
        for doc_type, rules in detection_rules.items():
            score = 0
            
            # Check keywords in columns
            keywords_found = 0
            for keyword in rules.get("column_keywords", []):
                keyword_lower = keyword.lower()
                for col in columns:
                    if keyword_lower in col:
                        keywords_found += 1
                        break
            
            # Check keywords in filename
            filename_matches = sum(1 for keyword in rules.get("file_keywords", []) 
                                  if keyword.lower() in filename)
            
            # Calculate score
            min_match = rules.get("min_columns_match", 2)
            if keywords_found >= min_match:
                score = keywords_found * rules.get("score_boost", 1.0) + filename_matches * 0.5
            
            if score > 0:
                scores[doc_type] = score
        
        if scores:
            # Retourner le type avec le score le plus élevé
            detected_type = max(scores, key=scores.get)
            logger.info(f"Detected document type: {detected_type} (score: {scores[detected_type]:.2f})")
            return detected_type
        
        logger.info("No document type detected with rules")
        return None
    
    def _build_enhanced_prompt(self, doc_type: Optional[str], doc_rules: Optional[Dict], file_info: Dict) -> str:
        """
        Builds an enhanced prompt based on detected financial rules
        
        Args:
            doc_type: Detected document type
            doc_rules: Rules for this document type
            file_info: File metadata
            
        Returns:
            Enhanced prompt for Gemini
        """
        base_prompt = """
You are an expert financial analyst. Your role is to analyze financial CSV files 
(of unknown structure, converted from Excel) and automatically generate relevant insights.

Note: The file has been converted to CSV for analysis. Use pandas.read_csv() to load it.

STEPS TO FOLLOW:

1. STRUCTURE ANALYSIS
   - Identify all columns in the file
   - Determine data types (dates, amounts, categories, etc.)
   - Identify the type of financial document
"""
        
        # If we detected a type and rules, enrich the prompt
        if doc_type and doc_rules:
            description = doc_rules.get("description", "")
            kpis = doc_rules.get("indicators", {}).get("kpis", [])
            charts = doc_rules.get("indicators", {}).get("suggested_charts", [])
            
            enhanced_prompt = base_prompt + f"""

🎯 DETECTED DOCUMENT TYPE: {doc_type.upper().replace('_', ' ')}
   Description: {description}

2. RELEVANT KPIs CALCULATION
   Based on the detected document type ({doc_type}), you MUST calculate the following KPIs:
"""
            
            # Add priority KPIs
            kpis_high = [kpi for kpi in kpis if kpi.get("priority") == "high"]
            kpis_medium = [kpi for kpi in kpis if kpi.get("priority") == "medium"]
            
            if kpis_high:
                enhanced_prompt += "\n   PRIORITY KPIs (must calculate):\n"
                for kpi in kpis_high:
                    enhanced_prompt += f"   - {kpi['name']}: {kpi['description']}\n"
                    enhanced_prompt += f"     Suggested formula: {kpi.get('formula', 'To be determined')}\n"
                    enhanced_prompt += f"     Unit: {kpi.get('unit', 'N/A')}\n"
            
            if kpis_medium:
                enhanced_prompt += "\n   SECONDARY KPIs (calculate if data is available):\n"
                for kpi in kpis_medium:
                    enhanced_prompt += f"   - {kpi['name']}: {kpi['description']}\n"
                    enhanced_prompt += f"     Suggested formula: {kpi.get('formula', 'To be determined')}\n"
            
            # Add suggested charts
            enhanced_prompt += "\n3. CHART GENERATION\n"
            enhanced_prompt += "   Suggested charts for this document type:\n"
            for chart in charts:
                enhanced_prompt += f"   - {chart.get('title', 'Chart')} ({chart.get('type', 'bar')}): {chart.get('description', '')}\n"
                if chart.get('axis_x'):
                    enhanced_prompt += f"     X-axis: {chart['axis_x']}\n"
                if chart.get('axis_y'):
                    enhanced_prompt += f"     Y-axis: {chart['axis_y']}\n"
            
            enhanced_prompt += """
   IMPORTANT for charts:
   - Use matplotlib.pyplot or seaborn to create charts
   - Save charts with plt.savefig('chart_name.png') in PNG format
   - Charts must be saved with descriptive names
   - Use plt.show() to display charts (they will be captured automatically)
   - Ensure charts are readable with clear labels, titles and legends

4. RESPONSE FORMAT
   Use Python code with pandas, matplotlib, seaborn to:
   - Read and clean data
   - Calculate ALL priority KPIs listed above
   - Generate suggested charts
   - Display a structured summary with results

IMPORTANT:
- Code must be robust (handle format errors, missing values)
- If a column needed for a KPI doesn't exist, adapt the formula or report it in the analysis
- Charts must be saved in PNG format in the current directory
- Provide a clear textual analysis of results with calculated KPI values

⚠️ CRITICAL - TOTAL ROWS HANDLING:
- BEFORE ANY CALCULATION, you MUST identify and EXCLUDE total rows
- Total rows can be identified by:
  * Text values like "TOTAL", "Total", "TOTALS", "SUB-TOTAL", "Subtotal", "GRAND TOTAL"
  * Text values like "SUM", "TOTAL GENERAL", etc.
  * Rows where all numeric columns contain very high values (suspected totals)
  * Empty rows followed by a row with "TOTAL"
- For each numeric column, check if there are total rows and EXCLUDE them from calculations
- Example code to use:
  ```python
  # Exclude total rows - CONVERT TO STRING FIRST
  df_clean = df[~df[text_column].astype(str).str.contains('TOTAL|Total|SUB-TOTAL|Subtotal', case=False, na=False)]
  # Or if no text column:
  df_clean = df[~df.apply(lambda row: any('total' in str(val).lower() for val in row), axis=1)]
  ```
- NEVER include total rows in sum, average, etc. calculations
- If you detect total rows, mention it in your analysis

📅 DATE HANDLING (CRITICAL):
- Dates can be in different formats (French "Fév 2023", English "Feb 2023", ISO "2023-02", etc.)
- ALWAYS use `pd.to_datetime()` with `errors='coerce'` and `format='mixed'` or without specific format
- NEVER use a fixed format like `format='%b %Y'` because months can be in French ("Fév", "Jan") or English ("Feb", "Jan")
- Robust code example:
  ```python
  # Robust method to parse dates (handles French and English)
  df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed', dayfirst=True)
  # OR without specific format (pandas detects automatically)
  df['date'] = pd.to_datetime(df['date'], errors='coerce', infer_datetime_format=True)
  ```
- If parsing fails, use `errors='coerce'` to convert to NaT rather than crashing
- NEVER try to change locale with `locale.setlocale()` - this doesn't work in the sandbox environment and will cause an error

🔤 DATA TYPE HANDLING:
- BEFORE using `.str` accessor, ALWAYS convert column to string with `.astype(str)`
- Example:
  ```python
  # ❌ BAD (may crash if column is not string)
  df['column'].str.contains('pattern')
  
  # ✅ GOOD (convert to string first)
  df['column'].astype(str).str.contains('pattern', na=False)
  ```
- Check type with `df.dtypes` before using specific accessors (.str, .dt)
- Use `na=False` in string methods to avoid errors with NaN
- Always convert to string before text operations: `df['col'].astype(str).str.method()`
"""
        else:
            # Default prompt if no rules detected
            enhanced_prompt = base_prompt + """
   - Identify the type of financial document (Balance Sheet, Income Statement, General Ledger, 
     Cash Flow, Stock Portfolio, Invoices, etc.)

2. RELEVANT KPIs CALCULATION
   Based on the detected document type, calculate the most relevant KPIs:
   
   - For a Balance Sheet: Working Capital, Liquidity Ratio, Debt/Equity
   - For an Income Statement: Total Revenue, Gross Margin, MoM/YoY Growth
   - For a General Ledger: Top expenses, Top revenues, Balance by category
   - For Cash Flow: Net cash, Time trend
   - For a Portfolio: Total performance, Return, Diversification
   - etc.

3. CHART GENERATION
   Generate relevant charts to visualize trends:
   - Time evolution (if dates present)
   - Distribution by category (pie chart)
   - Comparisons (bar chart)
   - Trends (line chart)
   
   IMPORTANT for charts:
   - Use matplotlib.pyplot or seaborn to create charts
   - Save charts with plt.savefig('chart_name.png') in PNG format
   - Charts must be saved with descriptive names
   - Use plt.show() to display charts (they will be captured automatically)
   - Ensure charts are readable with clear labels, titles and legends

4. RESPONSE FORMAT
   Use Python code with pandas, matplotlib, seaborn to:
   - Read and clean data
   - Calculate KPIs
   - Generate charts
   - Display a structured summary with results

IMPORTANT:
- Code must be robust (handle format errors, missing values)
- Charts must be saved in PNG format in the current directory
- Provide a clear textual analysis of results

⚠️ CRITICAL - TOTAL ROWS HANDLING:
- BEFORE ANY CALCULATION, you MUST identify and EXCLUDE total rows
- Total rows can be identified by:
  * Text values like "TOTAL", "Total", "TOTALS", "SUB-TOTAL", "Subtotal", "GRAND TOTAL"
  * Text values like "SUM", "TOTAL GENERAL", etc.
  * Rows where all numeric columns contain very high values (suspected totals)
  * Empty rows followed by a row with "TOTAL"
- For each numeric column, check if there are total rows and EXCLUDE them from calculations
- Example code to use:
  ```python
  # Exclude total rows - CONVERT TO STRING FIRST
  df_clean = df[~df[text_column].astype(str).str.contains('TOTAL|Total|SUB-TOTAL|Subtotal', case=False, na=False)]
  # Or if no text column:
  df_clean = df[~df.apply(lambda row: any('total' in str(val).lower() for val in row), axis=1)]
  ```
- NEVER include total rows in sum, average, etc. calculations
- If you detect total rows, mention it in your analysis

📅 DATE HANDLING (CRITICAL):
- Dates can be in different formats (French "Fév 2023", English "Feb 2023", ISO "2023-02", etc.)
- ALWAYS use `pd.to_datetime()` with `errors='coerce'` and `format='mixed'` or without specific format
- NEVER use a fixed format like `format='%b %Y'` because months can be in French ("Fév", "Jan") or English ("Feb", "Jan")
- Robust code example:
  ```python
  # Robust method to parse dates (handles French and English)
  df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed', dayfirst=True)
  # OR without specific format (pandas detects automatically)
  df['date'] = pd.to_datetime(df['date'], errors='coerce', infer_datetime_format=True)
  ```
- If parsing fails, use `errors='coerce'` to convert to NaT rather than crashing
- NEVER try to change locale with `locale.setlocale()` - this doesn't work in the sandbox environment and will cause an error

🔤 DATA TYPE HANDLING:
- BEFORE using `.str` accessor, ALWAYS convert column to string with `.astype(str)`
- Example:
  ```python
  # ❌ BAD (may crash if column is not string)
  df['column'].str.contains('pattern')
  
  # ✅ GOOD (convert to string first)
  df['column'].astype(str).str.contains('pattern', na=False)
  ```
- Check type with `df.dtypes` before using specific accessors (.str, .dt)
- Use `na=False` in string methods to avoid errors with NaN
- Toujours convertir en string avant de faire des opérations de texte : `df['col'].astype(str).str.method()`
"""
        
        return enhanced_prompt
    
    def _convert_to_csv(self, file_path: str, original_name: str) -> str:
        """
        Convertit un fichier Excel en CSV pour compatibilité avec Gemini Code Execution
        
        Args:
            file_path: Chemin vers le fichier Excel
            original_name: Nom original du fichier
            
        Returns:
            Chemin vers le fichier CSV créé (avec extension .csv garantie)
        """
        try:
            # Read Excel file (handle .xls and .xlsx)
            if Path(file_path).suffix.lower() == '.xls':
                # Old Excel format
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                # Modern Excel format
                df = pd.read_excel(file_path, engine='openpyxl')
            
            # Create temporary CSV file with guaranteed .csv extension
            csv_dir = Path(file_path).parent
            import time
            csv_path = csv_dir / f"converted_{int(time.time() * 1000)}.csv"
            
            # Save as CSV with UTF-8 encoding
            df.to_csv(str(csv_path), index=False, encoding='utf-8')
            
            # Verify file exists and has .csv extension
            if not csv_path.exists():
                raise Exception(f"CSV file was not created: {csv_path}")
            
            if not str(csv_path).endswith('.csv'):
                raise Exception(f"CSV file doesn't have correct extension: {csv_path}")
            
            logger.info(f"Excel file converted to CSV: {csv_path} ({csv_path.stat().st_size} bytes)")
            return str(csv_path)
        except Exception as e:
            logger.error(f"Error converting to CSV: {e}")
            raise
    
    async def analyze_financial_file(
        self, 
        file,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyse un fichier Excel financier et génère des KPIs automatiquement
        
        Args:
            file: Fichier uploadé (Streamlit UploadedFile ou chemin)
            custom_prompt: Prompt personnalisé optionnel
            
        Returns:
            Dict contenant:
            - document_type: Detected document type
            - kpis: List of calculated KPIs
            - chart_data: Data for charts
            - analysis: Textual analysis
            - generated_code: Generated Python code (for transparency)
            - execution_results: Code execution results
            - chart_files: List of generated chart files
            - raw_response: Complete raw response
        """
        
        # Temporarily save file if necessary
        temp_file_path = None
        temp_csv_path = None
        uploaded_file = None
        
        try:
            # If it's a file object (Streamlit), temporarily save it
            if hasattr(file, 'read'):
                file.seek(0)
                # Create temporary file
                original_name = getattr(file, 'name', 'file.xlsx')
                suffix = Path(original_name).suffix or '.xlsx'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file.read())
                    temp_file_path = tmp.name
                file.seek(0)
                
                # Convertir TOUJOURS en CSV pour Gemini Code Execution
                # Gemini Code Execution ne supporte que CSV, pas Excel
                file_to_upload = temp_file_path
                display_name = original_name
                
                if suffix.lower() in ['.xlsx', '.xls']:
                    logger.info(f"Conversion du fichier Excel ({suffix}) en CSV pour Gemini...")
                    temp_csv_path = self._convert_to_csv(temp_file_path, original_name)
                    file_to_upload = temp_csv_path
                    display_name = Path(original_name).stem + '.csv'
                    logger.info(f"Fichier converti: {temp_file_path} -> {temp_csv_path}")
                elif suffix.lower() == '.csv':
                    # Déjà un CSV, on peut l'utiliser directement
                    logger.info("Fichier CSV détecté, pas de conversion nécessaire")
                else:
                    # Unknown format, try to convert to CSV anyway
                    logger.warning(f"Unknown file format ({suffix}), attempting CSV conversion...")
                    try:
                        temp_csv_path = self._convert_to_csv(temp_file_path, original_name)
                        file_to_upload = temp_csv_path
                        display_name = Path(original_name).stem + '.csv'
                    except Exception as e:
                        logger.error(f"Unable to convert file: {e}")
                        raise Exception(f"Unsupported file format: {suffix}. Only .xlsx, .xls and .csv are supported.")
                
                # Verify file to upload exists and has .csv extension
                if not Path(file_to_upload).exists():
                    raise Exception(f"File to upload does not exist: {file_to_upload}")
                
                if not file_to_upload.endswith('.csv'):
                    raise Exception(f"File to upload must be a CSV: {file_to_upload}")
                
                logger.info(f"Uploading CSV file to Gemini: {file_to_upload}")
                # Explicitly specify mime_type to force CSV
                try:
                    uploaded_file = genai.upload_file(
                        path=file_to_upload,
                        display_name=display_name,
                        mime_type='text/csv'  # Force CSV MIME type
                    )
                except TypeError:
                    # If mime_type is not supported, try without
                    uploaded_file = genai.upload_file(
                        path=file_to_upload,
                        display_name=display_name
                    )
                logger.info(f"File uploaded to Gemini: {uploaded_file.name} (display: {display_name})")
            else:
                # Si c'est un chemin de fichier
                file_path = file
                display_name = Path(file).name
                
                # Convertir TOUJOURS en CSV pour Gemini Code Execution
                suffix = Path(file).suffix.lower()
                if suffix in ['.xlsx', '.xls']:
                    logger.info(f"Converting Excel file ({suffix}) to CSV for Gemini...")
                    temp_csv_path = self._convert_to_csv(file_path, display_name)
                    file_path = temp_csv_path
                    display_name = Path(display_name).stem + '.csv'
                    logger.info(f"File converted: {file} -> {file_path}")
                elif suffix == '.csv':
                    logger.info("CSV file detected, no conversion needed")
                else:
                    raise Exception(f"Unsupported file format: {suffix}. Only .xlsx, .xls and .csv are supported.")
                
                # Verify file exists and has .csv extension
                if not Path(file_path).exists():
                    raise Exception(f"File to upload does not exist: {file_path}")
                
                if not file_path.endswith('.csv'):
                    raise Exception(f"File to upload must be a CSV: {file_path}")
                
                logger.info(f"Uploading CSV file to Gemini: {file_path}")
                # Explicitly specify mime_type to force CSV
                try:
                    uploaded_file = genai.upload_file(
                        path=file_path,
                        display_name=display_name,
                        mime_type='text/csv'  # Force CSV MIME type
                    )
                except TypeError:
                    # If mime_type is not supported, try without
                    uploaded_file = genai.upload_file(
                        path=file_path,
                        display_name=display_name
                    )
                logger.info(f"File uploaded to Gemini: {uploaded_file.name} (display: {display_name})")
            
            # Detect document type if possible (only if no custom prompt)
            detected_doc_type = None
            doc_rules = None
            file_info = {}
            
            if not custom_prompt:
                # Extract metadata for detection
                from services.file_utils import get_file_info
                
                if hasattr(file, 'read'):
                    # If it's a file object, we must first extract metadata
                    file.seek(0)
                    file_info = get_file_info(file)
                    file.seek(0)
                else:
                    # If it's a path, read metadata
                    file_info = get_file_info(file_path if 'file_path' in locals() else file)
                
                detected_doc_type = self._detect_document_type(file_info)
                
                # Load rules for detected type
                if detected_doc_type and self.financial_rules:
                    doc_rules = self.financial_rules.get("document_types", {}).get(detected_doc_type)
            
            # Build prompt with rules
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._build_enhanced_prompt(detected_doc_type, doc_rules, file_info)
            
            # Add specific warning if total rows are detected
            if file_info.get("has_total_rows"):
                total_warning = f"""

🚨 CRITICAL ATTENTION - TOTAL ROWS DETECTED:
The file contains {file_info.get('total_rows_count', 0)} total row(s) detected at lines: {file_info.get('total_row_indices', [])}

YOU MUST ABSOLUTELY:
1. Exclude these rows from ALL your calculations (sums, averages, etc.)
2. Filter the DataFrame BEFORE any numeric calculation
3. Verify that your results don't contain these total values
4. Mention in your analysis that you excluded total rows

Example code to filter:
```python
# Detect and exclude total rows - CONVERT TO STRING FIRST
df_clean = df[~df.apply(lambda row: any('total' in str(val).lower() for val in row), axis=1)]
```

📅 IMPORTANT REMINDER - DATE HANDLING:
- Use `pd.to_datetime(df['date'], errors='coerce', format='mixed')` to handle French/English dates
- NEVER use `locale.setlocale()` - this doesn't work in the sandbox environment
- NEVER use a fixed format like `format='%b %Y'` - use `format='mixed'` or let pandas detect

🔤 IMPORTANT REMINDER - DATA TYPES:
- ALWAYS convert to string before `.str`: `df['col'].astype(str).str.contains(...)`
- Use `na=False` in string methods to avoid errors with NaN

"""
                prompt = prompt + total_warning
                logger.warning(f"Total rows detected: {file_info.get('total_row_indices', [])}")
            
            logger.info("Sending request to Gemini with Code Execution...")
            logger.debug(f"Prompt used: {prompt[:200]}...")
            
            # Call Gemini with Code Execution
            response = self.model.generate_content(
                contents=[
                    uploaded_file,
                    prompt
                ]
            )
            
            logger.info("Response received from Gemini")
            
            # Extract results in detail
            result = self._extract_results(response)
            
            # Add detected document type to results
            if detected_doc_type:
                result["detected_document_type"] = detected_doc_type
                result["detection_confidence"] = "high" if doc_rules else "medium"
            
            return result
            
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {str(e)}", exc_info=True)
            raise Exception(f"Error during Gemini analysis: {str(e)}")
        finally:
            # Clean up temporary files
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                    logger.info(f"Gemini file deleted: {uploaded_file.name}")
                except Exception as e:
                    logger.warning(f"Error deleting Gemini file: {e}")
            
            # Clean up temporary files
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Temporary file deleted: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Error deleting temporary file: {e}")
            
            if temp_csv_path and os.path.exists(temp_csv_path):
                try:
                    os.unlink(temp_csv_path)
                    logger.info(f"Temporary CSV file deleted: {temp_csv_path}")
                except Exception as e:
                    logger.warning(f"Error deleting temporary CSV file: {e}")
    
    def _extract_results(self, response) -> Dict[str, Any]:
        """
        Extrait et structure toutes les parties de la réponse Gemini
        
        Args:
            response: Réponse de l'API Gemini
            
        Returns:
            Dict structuré avec tous les éléments extraits
        """
        result = {
            "document_type": "Unknown",
            "kpis": [],
            "chart_files": [],
            "summary": "",
            "analysis_text": "",
            "generated_code": [],
            "execution_results": [],
            "execution_outputs": [],
            "raw_response_parts": [],
            "has_code_execution": False,
            "has_charts": False
        }
        
        logger.info("Extracting results from response...")
        
        # Iterate through all response candidates
        if not response.candidates:
            logger.warning("No candidates in response")
            return result
        
        candidate = response.candidates[0]
        
        # Iterate through all response parts
        for idx, part in enumerate(candidate.content.parts):
            part_info = {
                "index": idx,
                "type": type(part).__name__
            }
            
            # Explanatory text
            if hasattr(part, 'text') and part.text:
                text_content = part.text
                result["analysis_text"] += text_content + "\n\n"
                result["summary"] = text_content[:500] + "..." if len(text_content) > 500 else text_content
                part_info["text"] = text_content[:200] + "..." if len(text_content) > 200 else text_content
                logger.info(f"Text part found ({len(text_content)} characters)")
            
            # Generated executable code
            if hasattr(part, 'executable_code') and part.executable_code:
                code_content = part.executable_code.code
                result["generated_code"].append({
                    "code": code_content,
                    "language": getattr(part.executable_code, 'language', 'python')
                })
                result["has_code_execution"] = True
                part_info["code"] = code_content[:200] + "..." if len(code_content) > 200 else code_content
                logger.info(f"Generated code found ({len(code_content)} characters)")
            
            # Code execution results
            if hasattr(part, 'code_execution_result') and part.code_execution_result:
                execution_result = part.code_execution_result
                output = execution_result.output if hasattr(execution_result, 'output') else str(execution_result)
                
                result["execution_results"].append({
                    "output": output,
                    "exit_code": getattr(execution_result, 'exit_code', None)
                })
                result["execution_outputs"].append(output)
                result["has_code_execution"] = True
                part_info["execution_output"] = output[:200] + "..." if len(output) > 200 else output
                logger.info(f"Execution result found ({len(output)} characters)")
            
            # Generated files (charts)
            # Files can be in inline_data or in files uploaded by Gemini
            if hasattr(part, 'inline_data') and part.inline_data:
                inline_data = part.inline_data
                mime_type = getattr(inline_data, 'mime_type', 'unknown')
                data = getattr(inline_data, 'data', None)
                if data and ('image' in mime_type or 'png' in mime_type or 'jpeg' in mime_type):
                    result["chart_files"].append({
                        "mime_type": mime_type,
                        "data": data,
                        "filename": f"chart_{len(result['chart_files'])}.png"
                    })
                    result["has_charts"] = True
                    part_info["chart"] = f"Image {mime_type}"
                    logger.info(f"Chart found ({mime_type})")
            
            # Also check file_data if present
            if hasattr(part, 'file_data') and part.file_data:
                file_data = part.file_data
                mime_type = getattr(file_data, 'mime_type', 'unknown')
                file_uri = getattr(file_data, 'file_uri', None)
                if file_uri and ('image' in mime_type or 'png' in mime_type):
                    # Download file from Gemini
                    try:
                        downloaded_file = genai.get_file(file_uri)
                        result["chart_files"].append({
                            "mime_type": mime_type,
                            "data": downloaded_file.read(),
                            "filename": f"chart_{len(result['chart_files'])}.png",
                            "file_uri": file_uri
                        })
                        result["has_charts"] = True
                        part_info["chart"] = f"Image from URI {mime_type}"
                        logger.info(f"Chart found via file_data ({mime_type})")
                    except Exception as e:
                        logger.warning(f"Unable to download chart file: {e}")
            
            result["raw_response_parts"].append(part_info)
        
        # Essayer d'extraire des informations structurées du texte
        import re
        import json
        
        # Search for document type in text
        doc_type_patterns = [
            r'(?:document type|type detected|type of document)[\s:]+([A-Za-z\s]+)',
            r'(?:this is|it is a|this file is a)[\s]+([A-Za-z\s]+)',
            r'(?:balance sheet|income statement|general ledger|cash flow|portfolio|invoices)',
        ]
        
        for pattern in doc_type_patterns:
            match = re.search(pattern, result["analysis_text"], re.IGNORECASE)
            if match:
                result["document_type"] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Search for KPIs in text or execution results
        # Simple format: "KPI Name: value"
        kpi_pattern = r'([A-Za-z\s]+)[\s:]+([0-9,\.]+)\s*([€$%]?)'
        for output in result["execution_outputs"]:
            matches = re.findall(kpi_pattern, output)
            for match in matches:
                result["kpis"].append({
                    "name": match[0].strip(),
                    "value": match[1],
                    "unit": match[2] if match[2] else ""
                })
        
        logger.info(f"Extraction completed: {len(result['generated_code'])} codes, "
                   f"{len(result['execution_results'])} results, "
                   f"{len(result['chart_files'])} charts")
        
        return result
    
    async def analyze_decision_pass(
        self,
        prompt: str,
        files: List,
        previous_results: Optional[Dict[str, Any]] = None,
        converted_files_cache: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a single analysis pass for decision analysis
        
        Args:
            prompt: Prompt for this analysis pass
            files: List of file objects to analyze
            previous_results: Results from previous passes (for context)
            converted_files_cache: Optional cache of pre-converted CSV files (for optimization)
            
        Returns:
            Extracted results dict
        """
        uploaded_file_refs = []
        temp_files = []
        temp_csv_files = []
        
        try:
            # Upload all files to Gemini
            for file in files:
                if hasattr(file, 'read'):
                    # Check if file is already converted (optimization)
                    if converted_files_cache and file in converted_files_cache:
                        csv_path, display_name = converted_files_cache[file]
                        if csv_path:
                            # Use cached CSV file
                            file_to_upload = csv_path
                            logger.debug(f"Using cached CSV: {display_name}")
                        else:
                            # CSV file - need to save temporarily
                            file.seek(0)
                            original_name = display_name
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                                tmp.write(file.read())
                                temp_file_path = tmp.name
                                temp_files.append(temp_file_path)
                            file.seek(0)
                            file_to_upload = temp_file_path
                    else:
                        # No cache - convert normally
                        file.seek(0)
                        original_name = getattr(file, 'name', 'file.xlsx')
                        suffix = Path(original_name).suffix or '.xlsx'
                        
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(file.read())
                            temp_file_path = tmp.name
                            temp_files.append(temp_file_path)
                        file.seek(0)
                        
                        # Convert to CSV if needed
                        if suffix.lower() in ['.xlsx', '.xls']:
                            csv_path = self._convert_to_csv(temp_file_path, original_name)
                            temp_csv_files.append(csv_path)
                            file_to_upload = csv_path
                            display_name = Path(original_name).stem + '.csv'
                        else:
                            file_to_upload = temp_file_path
                            display_name = original_name
                    
                    # Upload to Gemini
                    uploaded_file = genai.upload_file(
                        path=file_to_upload,
                        display_name=display_name,
                        mime_type='text/csv' if file_to_upload.endswith('.csv') else None
                    )
                    uploaded_file_refs.append(uploaded_file)
            
            # Build prompt with previous results context if available
            full_prompt = prompt
            if previous_results:
                context_text = "\n\nPrevious analysis results:\n"
                for key, value in previous_results.items():
                    if isinstance(value, dict) and "analysis_text" in value:
                        context_text += f"\n{key}:\n{value['analysis_text'][:500]}\n"
                full_prompt = prompt + context_text
            
            # Execute analysis
            contents = uploaded_file_refs + [full_prompt]
            response = self.model.generate_content(contents)
            
            # Extract results
            result = self._extract_results(response)
            
            return result
            
        finally:
            # Cleanup uploaded files
            for ref in uploaded_file_refs:
                try:
                    genai.delete_file(ref.name)
                except Exception as e:
                    logger.warning(f"Error deleting Gemini file: {e}")
            
            # Cleanup temp files
            for temp_file in temp_files + temp_csv_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Error deleting temp file: {e}")
    
    async def analyze_files_structure(
        self,
        prompt: str,
        files: List
    ) -> Dict[str, Any]:
        """
        Analyze files with Gemini normal (no Code Execution)
        Just for understanding structure and content - used in Step 2
        
        Args:
            prompt: Prompt for analysis
            files: List of file objects to analyze
            
        Returns:
            Dict with analysis text (no code execution results)
        """
        uploaded_file_refs = []
        temp_files = []
        
        try:
            # Upload all files to Gemini
            for file in files:
                if hasattr(file, 'read'):
                    file.seek(0)
                    original_name = getattr(file, 'name', 'file.csv')
                    
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                        tmp.write(file.read())
                        temp_file_path = tmp.name
                        temp_files.append(temp_file_path)
                    file.seek(0)
                    
                    # Upload to Gemini
                    uploaded_file = genai.upload_file(
                        path=temp_file_path,
                        display_name=original_name,
                        mime_type='text/csv'
                    )
                    uploaded_file_refs.append(uploaded_file)
                    logger.debug(f"Uploaded file to Gemini normal: {original_name}")
            
            # Use Gemini normal (no Code Execution)
            contents = uploaded_file_refs + [prompt]
            response = self.model_normal.generate_content(contents)
            
            # Extract text response (no code execution results)
            text_content = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content += part.text
            
            logger.info(f"File structure analysis completed ({len(text_content)} characters)")
            
            return {
                "analysis_text": text_content,
                "has_code_execution": False
            }
            
        except Exception as e:
            logger.error(f"Error analyzing files structure: {e}")
            raise
        finally:
            # Cleanup uploaded files
            for ref in uploaded_file_refs:
                try:
                    genai.delete_file(ref.name)
                except Exception as e:
                    logger.warning(f"Error deleting Gemini file: {e}")
            
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Error deleting temp file: {e}")

