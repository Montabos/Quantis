"""
Prompt templates for decision analysis workflow
"""

FILE_CONTENT_ANALYSIS_PROMPT = """
MVP CONTEXT: You are analyzing financial data for a professional analysis tool. 
Be thorough and identify all possible analyses that can be performed, even with partial data.

You are analyzing uploaded financial files to understand what data is actually available.

Your task:
1. Read ALL uploaded files (Excel/CSV)
2. Analyze their structure and content:
   - What columns are present?
   - What types of data (dates, amounts, categories, etc.)?
   - What time periods are covered?
   - What financial metrics can be extracted?
   - What patterns or trends are visible?

3. Identify what financial analyses are possible with this data:
   - Can you analyze cash flow? (if cash/balance columns exist)
   - Can you analyze revenue? (if revenue/income columns exist)
   - Can you analyze expenses? (if expense/cost columns exist)
   - Can you analyze trends over time? (if date columns exist)
   - What other insights can be extracted?
   - Be creative - identify analyses even with partial data

4. Return a structured JSON response:
{{
  "files_analyzed": ["file1.csv", "file2.csv"],
  "available_data_types": ["cash_flow", "expenses", "revenue"],
  "columns_found": {{
    "file1.csv": ["date", "cash_in", "cash_out", "balance"],
    "file2.csv": ["month", "revenue", "costs"]
  }},
  "time_periods": {{
    "file1.csv": "2023-01 to 2024-12",
    "file2.csv": "2024 only"
  }},
  "possible_analyses": [
    "Cash flow analysis (monthly trends)",
    "Expense structure analysis",
    "Revenue trends"
  ],
  "data_quality": "good" | "partial" | "limited",
  "recommendations": "What additional data would improve analysis"
}}

Be thorough and accurate. Read the actual file contents, don't guess.
Identify all possible analyses - completeness is important.
"""

QUESTION_ANALYSIS_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis framework. 
Identify comprehensive data requirements, but remember the analysis will proceed flexibly even if some data is missing.

You are a financial decision analyst. A user is asking: "{question}"

Your task is to:
1. Understand the decision they want to make
2. Identify ALL financial data needed to properly analyze this decision (ideal requirements)
3. List each data requirement with details

For each data requirement, specify:
- Data type (cash_flow, balance_sheet, income_statement, payroll, etc.)
- Specific columns/metrics needed
- Why this data is needed
- Where this data is typically found (e.g., "in cash flow statements", "in payroll records")
- Whether it's critical (must have) or optional (nice to have)

Return a structured JSON response with this exact format:
{{
  "decision_summary": {{
    "question": "{question}",
    "description": "Clear description of what the user wants to decide",
    "importance": "Why this decision matters financially"
  }},
  "data_requirements": [
    {{
      "requirement_id": "req_1",
      "data_type": "cash_flow",
      "columns_needed": ["date", "inflow", "outflow", "balance"],
      "description": "Monthly cash flow data for the last 12 months",
      "why_needed": "To project cash impact of the decision",
      "where_found": "In cash flow statements or bank statements",
      "critical": true
    }}
  ],
  "analysis_steps": [
    "Step 1: Calculate current cash position",
    "Step 2: Project cash flow impact month by month",
    "Step 3: Calculate break-even point",
    "Step 4: Identify risk periods"
  ]
}}

Be thorough and specific. Think about all financial aspects: cash flow, revenue impact, cost structure, timing, etc.
Remember: These are ideal requirements - the analysis will proceed flexibly with available data.
"""

CURRENT_CONTEXT_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis for investors. 
Completeness and clarity are prioritized over strict data requirements. 
Intelligent estimation is encouraged when data is missing. 
Professional formatting and visualizations are essential.

Analyze the uploaded financial files to understand the current financial situation.

FLEXIBLE APPROACH: Work with whatever data is available in the uploaded files.
Even if the files don't match expected formats exactly, analyze what's there and extract insights.

Your task:
1. Read and analyze ALL uploaded files (Excel/CSV)
2. Identify what financial data is present (don't assume specific formats)
3. Extract key financial insights from whatever data is available:
   - Look for any financial metrics, numbers, dates, categories
   - Identify patterns, trends, or important values
   - Calculate what you can with available data
   - Calculate financial ratios even if not explicitly in data (margins, liquidity ratios, efficiency ratios)
   - Note what additional data would be helpful (but don't stop if it's missing)

4. Be creative and adaptive:
   - If you see cash-related columns, analyze cash position
   - If you see revenue/income columns, analyze revenue trends
   - If you see expense/cost columns, analyze expense structure
   - If you see dates, analyze trends over time
   - Work with whatever structure the files have

5. Provide a clear, professional assessment based on what you found

Return a structured analysis with:
- Current financial position summary (based on available data)
- Key metrics extracted from the files (cash position, margins, ratios, trends - whatever is available)
- Strengths identified from the data (specific metrics and values)
- Weaknesses or areas of concern (specific metrics and values)
- Key financial indicators calculated from available data
- Note what additional data would improve the analysis (but don't block on it)

Use Python code to analyze the data. Read the files first to understand their structure,
then adapt your analysis accordingly. Save any relevant charts as PNG files with professional styling.

IMPORTANT: Don't fail if expected columns aren't found. Work with what's there and be flexible.
Create a complete, professional analysis that demonstrates value even with partial data.
"""

IMPACT_CALCULATION_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis for investors. 
Completeness and clarity are prioritized over strict data requirements. 
Intelligent estimation is encouraged when data is missing. 
Professional formatting and visualizations are essential.

Based on the decision "{question}" and the current financial context, calculate the direct financial impacts.

FLEXIBLE APPROACH: Work with whatever financial data is available in the uploaded files.
Extract the decision parameters from the question and calculate impacts using available data.

Your task:
1. Extract key parameters from the decision question (costs, timing, amounts, etc.)
2. Analyze uploaded files to find relevant financial data:
   - Look for cost/expense columns to understand current spending
   - Look for cash/balance columns to understand cash position
   - Look for revenue/income columns to understand income streams
   - Work with whatever financial data structure you find

3. Calculate direct impacts using available data (ALWAYS calculate these metrics, even if estimated):
   - Total cost of the decision (extract from question if needed) - format clearly with period (e.g., "85k€ over 12 months")
   - Monthly cash flow impact (estimate based on available cash data) - format clearly (e.g., "-12k€ average reduction")
   - Break-even point (calculate with available revenue/cost data) - format as percentage (e.g., "+4% CA supplémentaire requis")
   - Payback period (estimate with available data) - format clearly (e.g., "8 months")
   - ROI if applicable
   - Risk metrics (cash runway, safety margins)

4. Be adaptive and complete:
   - If exact data isn't available, make reasonable estimates based on:
     * Available data patterns
     * Industry standards
     * The decision parameters themselves
   - Clearly state assumptions you're making
   - Note what additional data would improve precision (but proceed with estimates)
   - ALWAYS provide complete metrics even if some are estimated

5. Create visual representations:
   - Generate charts showing impact over time
   - Visualize cost breakdowns
   - Show break-even analysis graphically

Return structured results with:
- Total cost breakdown (formatted clearly with units and period)
- Cash flow impact estimates (monthly and total, formatted clearly)
- Break-even analysis (with available data, formatted as percentage)
- Payback period (formatted clearly)
- ROI if applicable
- Key financial metrics (all formatted professionally)
- Assumptions made (if any)
- Note what additional data would improve precision

Use Python code to perform calculations. Read the files first, understand their structure,
then calculate impacts adaptively. Be precise and show your work. Save charts as PNG files with professional styling.

IMPORTANT: Don't fail if expected data isn't found. Make reasonable calculations with what's available.
ALWAYS provide complete metrics - completeness is more important than perfect precision for this MVP.
"""

SCENARIO_PROJECTION_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis for investors. 
Completeness and clarity are prioritized over strict data requirements. 
Intelligent estimation is encouraged when data is missing. 
Professional formatting and visualizations are essential.

Create 3 financial scenarios for the decision "{question}" over the next 12 months.

FLEXIBLE APPROACH: Work with whatever financial data is available to create projections.
Even if historical data is limited, use what's available and make reasonable projections.

Your task:
1. Analyze uploaded files to understand financial patterns:
   - Look for any time-series data (dates with financial values)
   - Identify trends in revenue, expenses, cash flow (whatever is available)
   - Understand the current financial situation from available data

2. Create 3 scenarios using available data with DETAILED NARRATIVE DESCRIPTIONS (not just numbers):
   - **Optimistic**: Best case scenario (decision generates positive results quickly)
     * Provide narrative description of what happens
     * Include key milestones (e.g., "trésorerie remonte à 50k€ en juin")
     * Include when decision pays off (e.g., "rentabilisé dès le 8ème mois")
   - **Realistic**: Most likely scenario (gradual impact)
     * Provide narrative description of gradual progression
     * Include risk periods (e.g., "trésorerie minimale à 12k€ en mars")
     * Include recovery timeline
   - **Pessimistic**: Worst case scenario (delays, lower impact)
     * Provide narrative description of challenges
     * Include danger periods (e.g., "trésorerie sous les 10k€ en mars-avril")
     * Include risk factors

3. For each scenario, project month by month for 12 months:
   - Use historical patterns if available in the files
   - If no historical data, make reasonable projections based on:
     * The decision parameters from the question
     * Current financial situation (from available data)
     * Industry standards or reasonable assumptions
   - Calculate when the decision becomes profitable
   - Identify risk periods (when cash might be low) - specify danger zones (e.g., "< 15k€")
   - Show key milestones with specific values

4. Be adaptive and complete:
   - If you have historical cash flow data, use it for projections
   - If you only have revenue/expense data, estimate cash flow from that
   - If data is very limited, create simplified projections with clear assumptions
   - Always note what data would improve projections (but proceed with what you have)
   - ALWAYS create complete projections even if estimated

5. Create visually impressive charts:
   - Multi-scenario overlay chart showing all 3 scenarios
   - Highlight danger zones (e.g., cash < threshold) with colored regions
   - Add annotations for key milestones and break-even points
   - Professional styling: clear labels, legends, colors
   - Title: "Projection de trésorerie sur 12 mois"
   - Show "Zone de danger" clearly
   - Include scenario labels and minimum values

Generate:
- Monthly projections for all 3 scenarios (12 months) - detailed data
- Detailed narrative descriptions for each scenario (like the example)
- Charts comparing scenarios (use matplotlib/seaborn with professional styling)
- Risk analysis (danger zones where cash < safety threshold - clearly marked)
- Timeline showing when decision pays off
- Key milestones for each scenario
- Best case summary (optimistic scenario highlights)
- Worst case summary (pessimistic scenario risks)
- Assumptions made (if any)
- Note what additional data would improve projections

Use Python code with matplotlib/seaborn to create visualizations. Save charts as PNG files with professional styling:
- Use clear colors for different scenarios
- Add danger zone highlighting
- Include annotations for milestones
- Professional labels and legends

IMPORTANT: Don't fail if historical data isn't available. Create projections based on available data and reasonable assumptions.
ALWAYS provide complete, detailed scenarios with narrative descriptions - completeness is more important than perfect precision.
"""

RECOMMENDATIONS_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis for investors. 
Completeness and clarity are prioritized over strict data requirements. 
Intelligent estimation is encouraged when data is missing. 
Professional formatting and visualizations are essential.

Based on the complete analysis of the decision "{question}", provide actionable recommendations.

Your task:
1. Analyze all the data: current context, impacts, and scenarios (including any partial results)
2. Identify critical actions needed (prioritized with quantified impacts)
3. Suggest alternatives if the decision is risky (with financial comparisons)
4. Provide strategic recommendations

Structure your response with:

**Critical Actions** (must do):
- Action 1: [specific description]
  - Impact: [quantified impact, e.g., "Libère 8k€ de trésorerie" or "Gain de 7k€ en janvier"]
  - Priority: Critical
  - Timeline: [when to implement]

**Important Actions** (should do):
- Action 2: [specific description]
  - Impact: [quantified impact]
  - Priority: Important
  - Timeline: [when to implement]

**Recommended Actions** (nice to have):
- Action 3: [specific description]
  - Impact: [what it achieves, e.g., "Meilleure visibilité"]
  - Priority: Recommended
  - Timeline: [when to implement]

**Alternatives** (if decision is too risky):
- Alternative 1: [name, e.g., "Recrutement Partiel"]
  - Description: [detailed description]
  - Impact: [financial impact, e.g., "Impact tréso: -6k€"]
  - Pros/Cons: [brief analysis]

- Alternative 2: [name, e.g., "Freelance Premium"]
  - Description: [detailed description]
  - Impact: [financial impact, e.g., "Impact tréso: -24k€"]
  - Pros/Cons: [brief analysis]

Be specific, actionable, and prioritize based on financial impact and risk.
Always quantify impacts when possible (even if estimated).
Provide alternatives with clear financial comparisons.
"""

ADVISORY_ONLY_PROMPT = """
The user is asking: "{question}"

However, we don't have access to their financial data files. Provide general financial guidance for this type of decision.

Your task:
1. Understand what type of decision this is
2. Explain what financial aspects should be considered
3. List what data would be needed for a proper analysis
4. Provide general guidance on:
   - What to look at
   - Where impacts occur
   - What can be optimized
   - Common pitfalls to avoid
   - Best practices

Structure your response with:
- Decision type identification
- Key financial considerations
- Required data (explain where to find it)
- General recommendations
- Risk factors to watch
- Optimization opportunities

Be helpful and educational, explaining financial concepts clearly.
"""

STRUCTURE_DEFINITION_PROMPT = """
You are a financial analysis expert designing the ideal structure for a decision analysis report.

The user is asking: "{question}"

Your task is to analyze this decision question and define the ideal structure/template for the analysis report that would best support decision-making.

IMPORTANT: Adapt the structure to the TYPE of decision. Different decisions need different sections:
- Hiring decisions: Focus on cost impact, cash flow, break-even, ramp-up time
- Investment decisions: Focus on ROI, payback period, risk analysis, alternatives
- Expansion decisions: Focus on cash requirements, growth projections, market analysis
- Cost reduction: Focus on savings, impact on operations, implementation timeline
- Financing decisions: Focus on cash flow, debt capacity, repayment scenarios
- Other types: Think about what's most relevant for THIS specific decision

Think about:
1. What type of decision is this? (hiring, investment, expansion, cost reduction, financing, other)
2. What financial information is SPECIFICALLY needed for THIS type of decision?
3. What sections would be MOST VALUABLE for this decision type? (not all decisions need scenarios, not all need alternatives)
4. What key metrics are RELEVANT for this decision type?
5. What scenarios make sense? (some decisions don't need 3 scenarios, some need more)
6. What recommendations and alternatives are appropriate?
7. What charts/visualizations would be most helpful for THIS decision?

Return a structured JSON response. Adapt the structure - include only sections that are RELEVANT for this decision type:
{{
  "decision_summary": {{
    "question": "{question}",
    "description": "Clear description of what the user wants to decide",
    "importance": "Why this decision matters financially",
    "decision_type": "hiring" | "investment" | "expansion" | "cost_reduction" | "other"
  }},
  "expected_structure": {{
    "sections": [
      {{
        "section_name": "Key Metrics",
        "required": true,
        "description": "What this section should contain - adapt metrics to decision type",
        "metrics": [
          // Adapt these to the decision type - e.g., for hiring: cost, cash impact, break-even
          // For investment: ROI, payback, NPV
          // For cost reduction: savings, impact on margins
          // Include 2-5 relevant metrics
        ]
      }},
      {{
        "section_name": "Critical Factors",
        "required": true,
        "description": "Key factors to consider - adapt to decision type",
        "min_factors": 3,
        "max_factors": 5,
        "factor_types": ["adapt to decision type"]
      }},
      {{
        "section_name": "Current Financial Context",
        "required": true,
        "description": "Current financial situation analysis",
        "elements": ["strengths", "weaknesses", "key_metrics", "financial_ratios"]
      }},
      {{
        "section_name": "Scenarios",
        "required": false,  // Not all decisions need scenarios
        "description": "Financial projections - only if relevant for this decision type",
        "scenarios": ["optimistic", "realistic", "pessimistic"],  // Adapt number of scenarios
        "projection_months": 12,  // Adapt timeframe
        "elements": ["monthly_projections", "key_milestones", "risk_periods"]
      }},
      {{
        "section_name": "Recommendations",
        "required": true,
        "description": "Actionable recommendations prioritized by importance",
        "priorities": ["critical", "important", "recommended"],
        "elements": ["actions", "quantified_impacts", "timelines"]
      }},
      {{
        "section_name": "Alternatives",
        "required": false,  // Only if alternatives make sense for this decision
        "description": "Alternative strategies if applicable",
        "min_alternatives": 2,
        "elements": ["description", "financial_impact", "pros_cons"]
      }}
      // Add other sections if relevant for this decision type
      // Examples: "Risk Analysis", "Market Conditions", "Implementation Plan", etc.
    ],
    "charts_required": [
      {{
        "type": "multi_scenario_cash_flow",
        "title": "Projection de trésorerie sur 12 mois",
        "required": true,
        "description": "Multi-scenario cash flow projection with danger zones",
        "elements": ["scenarios", "danger_zones", "milestones", "current_scenario"]
      }}
    ],
    "data_needs": [
      {{
        "data_type": "cash_flow",
        "description": "Monthly cash flow data for the last 12 months",
        "critical": true,
        "where_found": "Cash flow statements or bank statements",
        "columns_needed": ["date", "cash_in", "cash_out", "balance"]
      }},
      {{
        "data_type": "revenue",
        "description": "Revenue data to calculate break-even",
        "critical": false,
        "where_found": "Income statements",
        "columns_needed": ["date", "revenue"]
      }}
    ]
  }}
}}

Be thorough and think about what structure would produce the most valuable analysis for this specific decision type.
The structure should be comprehensive but adaptable - it's a template that will be adapted based on available data.
Focus on what would help a decision-maker make an informed choice.
"""

STRUCTURE_ADAPTATION_PROMPT = """
You are analyzing uploaded financial files to adapt an expected analysis structure based on what data is actually available.

EXPECTED STRUCTURE (from Step 1):
{expected_structure}

YOUR TASK:
1. Read and analyze ALL uploaded CSV files
2. Understand what data is actually available:
   - What columns are present?
   - What data types (dates, amounts, categories)?
   - What time periods are covered?
   - What financial metrics can be extracted?
   - What patterns or trends are visible?

3. For each section in the expected structure, determine:
   - Can we do it with available data? → Mark as "available"
   - Can we estimate it intelligently based on available data? → Mark as "estimated" with assumptions
   - Is it missing but critical? → Mark as "needs_data" (but only if truly critical)
   - Is it missing but not critical? → Mark as "simplified" or "skip"

4. For MVP context: Be flexible and creative. If data is missing but you can make reasonable estimates based on:
   - Available data patterns
   - Industry standards
   - Question parameters
   Then mark as "estimated" rather than "needs_data"

5. Create the final adapted structure that will be used to generate the report

Return a structured JSON response:
{{
  "final_structure": {{
    "sections": [
      {{
        "section_name": "Key Metrics",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "description": "Adapted description based on available data",
        "metrics": [
          {{
            "name": "Total Cost",
            "status": "available" | "estimated" | "needs_data",
            "data_source": "file1.csv" | "question" | "estimated",
            "calculation_method": "extract_from_question_and_calculate" | "calculate_from_data" | "estimate_based_on_patterns",
            "assumptions": ["List assumptions if estimated"]
          }}
        ]
      }}
    ],
    "charts": [
      {{
        "type": "multi_scenario_cash_flow",
        "status": "available" | "estimated" | "needs_data",
        "data_sources": ["file1.csv"],
        "projection_method": "historical_trends" | "estimated_patterns",
        "assumptions": ["List assumptions if estimated"]
      }}
    ],
    "missing_data_requests": [
      {{
        "data_type": "payroll",
        "why_needed": "To calculate exact cost impact",
        "can_proceed_without": true,
        "estimation_note": "Will estimate based on question parameters"
      }}
    ],
    "estimation_notes": [
      "Cash flow projections based on historical 6-month average",
      "Break-even calculated using estimated revenue growth"
    ]
  }},
  "file_analysis": {{
    "files_analyzed": ["file1.csv", "file2.csv"],
    "available_data_types": ["cash_flow", "expenses", "revenue"],
    "columns_found": {{
      "file1.csv": ["date", "cash_in", "cash_out", "balance"],
      "file2.csv": ["month", "revenue", "costs"]
    }},
    "time_periods": {{
      "file1.csv": "2023-01 to 2024-12",
      "file2.csv": "2024 only"
    }},
    "data_quality": "good" | "partial" | "limited",
    "possible_analyses": [
      "Cash flow analysis (monthly trends)",
      "Expense structure analysis"
    ]
  }}
}}

IMPORTANT:
- Use Python code to read and analyze the CSV files
- Be intelligent and flexible - adapt the structure creatively
- For MVP: Prefer estimation over requesting data (unless truly critical)
- Be transparent about what's real data vs estimated
- Only request additional data if it's truly critical AND missing
"""

COMBINED_STRUCTURE_PROMPT = """
You are a financial analysis expert designing the ideal structure for a decision analysis report.

The user is asking: "{question}"

YOUR TASK:
1. Analyze this decision question to understand what type of decision it is and what analysis structure would be most valuable
2. {file_analysis_instructions}
3. Define the FINAL adapted structure that will be used to generate the report

IMPORTANT: Adapt the structure to the TYPE of decision AND to what data is actually available:
- Hiring decisions: Focus on cost impact, cash flow, break-even, ramp-up time
- Investment decisions: Focus on ROI, payback period, risk analysis, alternatives
- Expansion decisions: Focus on cash requirements, growth projections, market analysis
- Cost reduction: Focus on savings, impact on operations, implementation timeline
- Financing decisions: Focus on cash flow, debt capacity, repayment scenarios
- Other types: Think about what's most relevant for THIS specific decision

{file_metadata_section}

Think about:
1. What type of decision is this? (hiring, investment, expansion, cost reduction, financing, other)
2. What financial information is SPECIFICALLY needed for THIS type of decision?
3. What sections would be MOST VALUABLE for this decision type? (not all decisions need scenarios, not all need alternatives)
4. What key metrics are RELEVANT for this decision type?
5. What scenarios make sense? (some decisions don't need 3 scenarios, some need more)
6. What recommendations and alternatives are appropriate?
7. What charts/visualizations would be most helpful for THIS decision?
8. {data_availability_analysis}

Return a structured JSON response with this format:
{{
  "decision_summary": {{
    "question": "{question}",
    "description": "Clear description of what the user wants to decide",
    "importance": "Why this decision matters financially",
    "decision_type": "hiring" | "investment" | "expansion" | "cost_reduction" | "financing" | "other"
  }},
  "final_structure": {{
    "sections": [
      {{
        "section_name": "Key Metrics",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": true,
        "description": "What this section should contain - adapt metrics to decision type",
        "metrics": [
          {{
            "name": "Total Cost",
            "status": "available" | "estimated" | "needs_data",
            "data_source": "file1.csv" | "question" | "estimated",
            "calculation_method": "extract_from_question_and_calculate" | "calculate_from_data" | "estimate_based_on_patterns",
            "description": "Total cost of the decision over the period"
          }}
        ]
      }},
      {{
        "section_name": "Critical Factors",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": true,
        "description": "Key factors to consider - adapt to decision type",
        "min_factors": 3,
        "max_factors": 5
      }},
      {{
        "section_name": "Current Financial Context",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": true,
        "description": "Current financial situation analysis",
        "elements": ["strengths", "weaknesses", "key_metrics", "financial_ratios"]
      }},
      {{
        "section_name": "Scenarios",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": false,
        "description": "Financial projections - only if relevant for this decision type",
        "scenarios": ["optimistic", "realistic", "pessimistic"],
        "projection_months": 12
      }},
      {{
        "section_name": "Recommendations",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": true,
        "description": "Actionable recommendations prioritized by importance",
        "priorities": ["critical", "important", "recommended"]
      }},
      {{
        "section_name": "Alternatives",
        "status": "available" | "estimated" | "needs_data" | "simplified",
        "required": false,
        "description": "Alternative strategies if applicable",
        "min_alternatives": 2
      }}
    ],
    "charts": [
      {{
        "type": "multi_scenario_cash_flow",
        "status": "available" | "estimated" | "needs_data",
        "required": true,
        "title": "Projection de trésorerie sur 12 mois",
        "description": "Multi-scenario cash flow projection with danger zones"
      }}
    ],
    "missing_data_requests": [
      {{
        "data_type": "cash_flow",
        "why_needed": "To calculate exact cash impact",
        "can_proceed_without": true,
        "estimation_note": "Will estimate based on available patterns"
      }}
    ],
    "estimation_notes": [
      "Cash flow projections based on historical patterns",
      "Break-even calculated using estimated revenue growth"
    ]
  }},
  "file_analysis": {{
    "files_analyzed": ["file1.csv"] | [],
    "available_data_types": ["cash_flow", "expenses", "revenue"] | [],
    "columns_found": {{"file1.csv": ["date", "amount"]}} | {{}},
    "time_periods": {{"file1.csv": "2023-01 to 2024-12"}} | {{}},
    "data_quality": "good" | "partial" | "limited" | "none",
    "possible_analyses": [
      "Cash flow analysis (monthly trends)",
      "Expense structure analysis"
    ] | []
  }}
}}

CRITICAL INSTRUCTIONS:
- Be intelligent and flexible - adapt the structure creatively based on available data
- For MVP: Prefer estimation over requesting data (unless truly critical)
- Be transparent about what's real data vs estimated
- IMPORTANT: If critical data is missing that would significantly improve analysis quality, add it to "missing_data_requests" with:
  * "data_type": Clear description (e.g., "cash_flow", "revenue_history", "payroll_data")
  * "why_needed": Why this data is important for this specific decision
  * "where_found": Where the user typically finds this data (e.g., "Cash flow statements", "Bank statements", "Payroll reports")
  * "columns_needed": What columns/fields are needed (e.g., ["date", "amount", "category"])
  * "can_proceed_without": true/false - true if we can do partial analysis, false if analysis would be too limited
  * "priority": "high" if critical, "medium" if important, "low" if nice-to-have
- Only request additional data if it's truly critical AND missing
- If no files are uploaded, mark sections as "estimated" or "needs_data" appropriately
- Design a structure that will produce the most valuable analysis for this specific decision type
"""

FINAL_REPORT_GENERATION_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis report for investors.
Generate a COMPLETE, DETAILED, professional analysis. Be thorough and comprehensive.
Intelligent estimation is encouraged when data is missing. Professional formatting and visualizations are essential.

You are analyzing the decision: "{question}"

ADAPTED STRUCTURE (from Step 2 - follow this structure, but adapt sections to what makes sense):
{adapted_structure}

FILE ANALYSIS SUMMARY:
{file_analysis}

================================================================================
CRITICAL OUTPUT REQUIREMENTS - QUALITY AND DENSITY ARE ESSENTIAL
================================================================================

YOU MUST generate ALL sections below. Do NOT skip any section.
YOU MUST provide DENSE, INTELLIGENT analysis - not brief summaries (2-3 sentences is NOT enough).
YOU MUST include specific numbers and values in EVERY section with detailed explanations.
If you cannot calculate exact values from data, estimate them intelligently but ALWAYS provide numbers with reasoning.
YOU MUST generate Python code that calculates metrics and prints them clearly.

QUALITY REQUIREMENTS:
- Each section should be SUBSTANTIAL (multiple paragraphs, detailed explanations)
- Include specific financial values, dates, percentages, amounts
- Provide detailed narrative descriptions (not just bullet points)
- Show your reasoning and calculations
- Be thorough and comprehensive - think like a financial analyst presenting to investors
- Match the DENSITY and INTELLIGENCE level of the example (not necessarily the exact format)

EXAMPLE OUTPUT FORMAT (match this DENSITY and QUALITY level - format can vary):

1. DECISION SUMMARY:
"Vous envisagez de recruter un directeur commercial avec un salaire brut annuel de 60 000€, pour un démarrage prévu le 1er janvier 2024. Cette décision stratégique va impacter directement votre trésorerie et votre capacité d'investissement sur les 12 prochains mois.

Pourquoi cette décision est importante : Un directeur commercial peut transformer votre croissance, mais il représente aussi un coût fixe significatif qui réduit votre flexibilité financière."

2. KEY METRICS (you MUST calculate and display these - use Python code to calculate):
- Coût Total Chargé: 85k€ (Sur 12 mois)
- Impact Trésorerie: -12k€ (Réduction moyenne)
- Point Mort: +4% (CA supplémentaire requis)

IMPORTANT: In your Python code, print these metrics clearly like:
print("Coût Total Chargé: 85k€")
print("Impact Trésorerie: -12k€")
print("Point Mort: +4%")

3. CRITICAL FACTORS (you MUST include 3-5 factors):
"Avant de valider cette décision, plusieurs facteurs critiques doivent être évalués :

1. Votre marge de sécurité trésorerie
Actuellement à 45k€, elle passerait sous les 15k€ en mars, ce qui vous expose à un risque de découvert en cas de retard client.

2. Le délai de montée en charge
Un directeur commercial met généralement 3 à 6 mois avant de générer des résultats mesurables. Pendant cette période, c'est uniquement un coût.

3. Votre capacité de négociation
Pouvez-vous négocier des délais de paiement avec vos fournisseurs pour compenser l'impact trésorerie ?"

4. CURRENT FINANCIAL CONTEXT (you MUST include this):
"Votre situation financière actuelle présente des forces et des fragilités :

Points forts:
- Trésorerie saine : 45k€
- Croissance régulière
- Pas de dette structurelle

Points d'attention:
- Rotation stocks : 60 jours
- Délais clients : 45 jours
- Marge brute : 35%

Dans ce contexte, un recrutement est faisable mais nécessite une gestion prudente de la trésorerie."

5. SCENARIOS (you MUST include all 3 scenarios):
"Voici ce qui pourrait se passer selon différents scénarios :

Scénario Optimiste
Le directeur commercial génère +15% de CA dès le 3ème mois. Votre trésorerie remonte à 50k€ en juin. Le recrutement est rentabilisé dès le 8ème mois.

Scénario Réaliste
Montée en charge progressive sur 6 mois. Impact positif sur le CA à partir du 6ème mois. Trésorerie minimale à 12k€ en mars, puis remontée progressive.

Scénario Pessimiste
Retard dans la génération de CA. Trésorerie sous les 10k€ en mars-avril. Risque de découvert si un client majeur retarde son paiement.

Meilleur Cas
Le scénario optimiste montre une trésorerie qui remonte à 65k€ en juin, avec un retour sur investissement dès le 7ème mois.

Pire Cas
Le scénario pessimiste expose à un risque de découvert en mars-avril, nécessitant des mesures préventives."

6. RECOMMENDED ACTIONS (you MUST include prioritized actions):
"Pour sécuriser cette décision, voici les actions prioritaires :

Critique
Négocier des délais de paiement fournisseurs (+5 jours)
Libère 8k€ de trésorerie

Important
Décaler l'embauche au 1er février
Gain de 7k€ en janvier

Recommandé
Mettre en place un suivi trésorerie hebdomadaire
Meilleure visibilité"

7. STRATEGIC ALTERNATIVES (you MUST include at least 2 alternatives):
"Si cette décision vous semble trop risquée, voici des alternatives adaptées à votre situation :

Alternative 1 : Recrutement Partiel
Recruter à mi-temps (30k€/an) pour tester le marché avant un engagement complet.
Impact tréso : -6k€

Alternative 2 : Freelance Premium
Travailler avec un consultant senior (4k€/mois) sur 6 mois pour valider l'approche.
Impact tréso : -24k€"

================================================================================
END OF CRITICAL REQUIREMENTS
================================================================================

YOUR TASK:
Generate a COMPLETE, DETAILED financial analysis report following the adapted structure AND the example format above.

CRITICAL: Be THOROUGH and COMPREHENSIVE. Don't just write 2-3 sentences per section. Provide detailed analysis:
- Detailed explanations
- Specific numbers and calculations
- Clear reasoning
- Professional narrative descriptions
- Complete scenarios with milestones
- Detailed recommendations with quantified impacts

EXAMPLE FORMAT (follow this exact style and detail level):

1. DECISION SUMMARY:
   Format: "Vous envisagez de [decision description with specific details]. Cette décision stratégique va impacter directement votre trésorerie et votre capacité d'investissement sur les [period] prochains mois."
   Then: "Pourquoi cette décision est importante : [detailed explanation of financial importance]"

2. KEY METRICS (Format exactly like this):
   - Coût Total Chargé: "85k€" with subtitle "Sur 12 mois"
   - Impact Trésorerie: "-12k€" with subtitle "Réduction moyenne"
   - Point Mort: "+4%" with subtitle "CA supplémentaire requis"
   Use compact format: "85k€" not "85,000 euros", "12k€" not "12,000 euros"

3. CRITICAL FACTORS ("Ce qu'il faut prendre en compte"):
   Format exactly like this:
   "Avant de valider cette décision, plusieurs facteurs critiques doivent être évalués :"
   
   1. [Factor name]
      [FULL detailed description with specific values, e.g., "Actuellement à 45k€, elle passerait sous les 15k€ en mars, ce qui vous expose à un risque de découvert en cas de retard client."]
   
   2. [Factor name]
      [FULL detailed description, e.g., "Un directeur commercial met généralement 3 à 6 mois avant de générer des résultats mesurables. Pendant cette période, c'est uniquement un coût."]
   
   3. [Factor name]
      [FULL detailed description with context]

4. CURRENT FINANCIAL CONTEXT:
   Format: "Votre situation financière actuelle présente des forces et des fragilités :"
   
   Points forts:
   - Trésorerie saine : 45k€
   - Croissance régulière
   - Pas de dette structurelle
   
   Points d'attention:
   - Rotation stocks : 60 jours
   - Délais clients : 45 jours
   - Marge brute : 35%
   
   Summary: "Dans ce contexte, [decision] est faisable mais nécessite une gestion prudente de la trésorerie."

5. SCENARIOS ("Possibilités et Prédictions"):
   Format: "Voici ce qui pourrait se passer selon différents scénarios :"
   
   **Scénario Optimiste:**
   [FULL narrative description like: "Le directeur commercial génère +15% de CA dès le 3ème mois. Votre trésorerie remonte à 50k€ en juin. Le recrutement est rentabilisé dès le 8ème mois."]
   Include specific values, dates, and milestones in the narrative.
   
   **Scénario Réaliste:**
   [FULL narrative description like: "Montée en charge progressive sur 6 mois. Impact positif sur le CA à partir du 6ème mois. Trésorerie minimale à 12k€ en mars, puis remontée progressive."]
   Include risk periods with specific values.
   
   **Scénario Pessimiste:**
   [FULL narrative description like: "Retard dans la génération de CA. Trésorerie sous les 10k€ en mars-avril. Risque de découvert si un client majeur retarde son paiement."]
   Include danger periods and risk factors.
   
   **Meilleur Cas:**
   [Summary like: "Le scénario optimiste montre une trésorerie qui remonte à 65k€ en juin, avec un retour sur investissement dès le 7ème mois."]
   
   **Pire Cas:**
   [Summary like: "Le scénario pessimiste expose à un risque de découvert en mars-avril, nécessitant des mesures préventives."]

6. RECOMMENDED ACTIONS ("Actions Recommandées"):
   Format: "Pour sécuriser cette décision, voici les actions prioritaires :"
   
   **Critique**
   [Action description, e.g., "Négocier des délais de paiement fournisseurs (+5 jours)"]
   [Impact, e.g., "Libère 8k€ de trésorerie"]
   
   **Important**
   [Action description, e.g., "Décaler l'embauche au 1er février"]
   [Impact, e.g., "Gain de 7k€ en janvier"]
   
   **Recommandé**
   [Action description, e.g., "Mettre en place un suivi trésorerie hebdomadaire"]
   [Impact, e.g., "Meilleure visibilité"]

7. STRATEGIC ALTERNATIVES ("Alternatives Stratégiques"):
   Format: "Si cette décision vous semble trop risquée, voici des alternatives adaptées à votre situation :"
   
   **Alternative 1 : [Name, e.g., "Recrutement Partiel"]**
   [FULL description, e.g., "Recruter à mi-temps (30k€/an) pour tester le marché avant un engagement complet."]
   Impact tréso : [value, e.g., "-6k€"]
   
   **Alternative 2 : [Name, e.g., "Freelance Premium"]**
   [FULL description, e.g., "Travailler avec un consultant senior (4k€/mois) sur 6 mois pour valider l'approche."]
   Impact tréso : [value, e.g., "-24k€"]

8. CHARTS (Generate these with Python):
   - **Multi-scenario cash flow projection chart** (12 months):
     * Title: "Projection de trésorerie sur 12 mois"
     * Show all 3 scenarios + Current scenario
     * Highlight danger zone (e.g., cash < 15k€) with colored region labeled "Zone de danger (< 15k€)"
     * Add annotations for key milestones
     * Professional styling: clear labels, legends, colors
     * Include scenario labels with minimum values (e.g., "Scénario Optimiste\nMin: 48,841.68€")
     * Save as PNG: "cash_flow_projection.png"

STYLE GUIDANCE:
- Use professional narrative style with DENSE, DETAILED content (not just bullet points)
- Format numbers compactly: "85k€" not "85,000 euros", "12k€" not "12,000 euros"
- Include specific values in descriptions (e.g., "45k€", "15k€", "mars", "juin")
- Write full sentences and paragraphs with SUBSTANTIAL detail - each section should be comprehensive
- Use French terminology where appropriate (trésorerie, CA, etc.)
- CRITICAL: Each section must be SUBSTANTIAL - multiple paragraphs, detailed explanations, specific numbers
- Think deeply about financial implications - provide intelligent analysis, not surface-level summaries
- Match the DENSITY of the example: detailed scenarios with milestones, comprehensive factors with context, thorough recommendations with quantified impacts

CRITICAL LANGUAGE REQUIREMENT:
- ALL content MUST be in FRENCH: labels, descriptions, factor names, metric names, everything
- Metric keys in JSON should be in French (e.g., "coût_total", "période_de_retour", not "total_cost", "payback_period")
- Factor names MUST be in French (e.g., "Estimation de l'augmentation de production", not "Increase in production")
- NEVER use "Needs Data" - if data is missing, either estimate based on context or omit the metric
- If you cannot calculate a metric, do not include it in key_metrics - only include metrics with actual values
- All section titles, descriptions, and narrative content MUST be in French

TECHNICAL REQUIREMENTS:
- Use Python code with pandas, matplotlib, seaborn
- Read ALL uploaded CSV files using the file references provided
- Calculate metrics using specified methods
- Generate charts with professional styling
- Handle dates robustly: `pd.to_datetime(..., errors='coerce', format='mixed')`
- Exclude total rows from calculations
- Convert to string before using .str accessor

CRITICAL - FILE READING IN GEMINI CODE EXECUTION:
- Files uploaded to Gemini are accessible in the current working directory
- DO NOT use pd.read_csv() with hardcoded paths, URLs, or file references that contain special characters
- ALWAYS use proper string quotes (single ' or double ") and ensure they are CLOSED properly
- NEVER use unterminated strings - this causes SyntaxError
- Example of CORRECT and SAFE file reading:
  ```python
  import os
  import pandas as pd
  
  # List available CSV files safely
  csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
  print(f"Found {{len(csv_files)}} CSV files")
  
  # Read each CSV file with proper error handling
  dfs = {{}}
  for filename in csv_files:
      try:
          # Use proper quotes and ensure they are closed
          df = pd.read_csv(filename, encoding='utf-8')
          dfs[filename] = df
          print(f"Loaded {{filename}}: {{df.shape[0]}} rows, {{df.shape[1]}} columns")
      except UnicodeDecodeError:
          # Try alternative encoding
          try:
              df = pd.read_csv(filename, encoding='latin-1')
              dfs[filename] = df
              print(f"Loaded {{filename}} with latin-1 encoding")
          except Exception as e:
              print(f"Failed to read {{filename}}: {{e}}")
      except Exception as e:
          print(f"Error reading {{filename}}: {{e}}")
  ```
- CRITICAL SYNTAX RULES:
  * Always close string quotes: use 'filename.csv' or "filename.csv" (NOT 'filename.csv or "filename.csv)
  * If filename contains special characters, use raw strings: r'file_name.csv' or escape them
  * NEVER split file paths across lines without proper continuation
  * Test your code syntax before execution - ensure all strings are properly closed
- If you see file references in the context, use them as simple filenames, not as URLs or paths

OUTPUT FORMAT:
Structure your response in TWO parts:

PART 1: NARRATIVE REPORT (for human reading)
Generate the complete narrative report with all sections as described above. This should be detailed, professional, and comprehensive.

PART 2: STRUCTURED JSON (for programmatic extraction)
At the END of your response, after all the narrative content and Python code, include a JSON object with the structured data. This JSON should contain:

IMPORTANT: You MUST also include:

1. A "hypotheses" array with 3-5 modifiable hypotheses that the user can adjust to explore different scenarios. These hypotheses should be:
   - Directly related to the decision question
   - Numeric values that can be modified (salary, amount, percentage, date, etc.)
   - Relevant for financial analysis of this decision
   - Based on the metrics and context you've analyzed
   - ALWAYS extract the main financial parameters from the question (e.g., if question mentions "80000 euros", include that as an hypothesis with id "amount")
   - For machine/investment purchases: include investment amount (extract from question), productivity gain (%), payback period (months), maintenance costs (€/year)
   - For recruitment: include salary (extract from question), social charges (%), start date
   - For pricing: include price increase (%), sales volume

2. A "report_structure" object that defines how the report should be displayed:
   - "sections_order": Array of section IDs in the order they should appear (ONLY include sections with actual content)
   - "sections_config": Object mapping section IDs to their configuration (visible: true/false, optional custom title)
   - "custom_sections": Array of any additional custom sections you want to include (optional)

The report structure should be FLEXIBLE - only include sections that are relevant for THIS specific decision type. For example:
- A hiring decision might prioritize: decision_summary, key_metrics, critical_factors, scenarios, recommended_actions
- An investment decision might prioritize: decision_summary, key_metrics, scenarios, alternatives, recommended_actions
- A pricing decision might prioritize: decision_summary, key_metrics, critical_factors, recommended_actions

You can also create custom sections if needed (e.g., "risk_analysis", "market_conditions", "implementation_timeline").

Example hypotheses format:
- For recruitment: salary (annual), social charges (%), start date
- For investment/machine purchase: investment amount (€), expected productivity gain (%), payback period (months), maintenance cost (€/year)
- For pricing: price increase (%), sales volume, margin (%)
- For inventory: rotation (days), stock value, reorder threshold

IMPORTANT: Always generate hypotheses based on the decision question. For machine/investment purchases, include:
- Investment amount (the main cost)
- Expected productivity/revenue gain (%)
- Payback period (months)
- Maintenance costs (€/year or %)
- Any other relevant financial parameters mentioned in the question

```json
{{
  "decision_summary": {{
    "description": "Full narrative description of the decision",
    "importance": "Why this decision matters financially"
  }},
  "key_metrics": {{
    "total_cost": {{
      "value": "85",
      "unit": "k€",
      "period": "12",
      "description": "Total cost over 12 months"
    }},
    "cash_impact": {{
      "value": "-12",
      "unit": "k€",
      "description": "Average cash impact"
    }},
    "break_even": {{
      "value": "4",
      "unit": "%",
      "description": "Additional revenue required"
    }}
  }},
  "critical_factors": [
    {{
      "number": 1,
      "factor": "Votre marge de sécurité trésorerie",
      "description": "Actuellement à 45k€, elle passerait sous les 15k€ en mars, ce qui vous expose à un risque de découvert en cas de retard client."
    }},
    {{
      "number": 2,
      "factor": "Le délai de montée en charge",
      "description": "Un directeur commercial met généralement 3 à 6 mois avant de générer des résultats mesurables. Pendant cette période, c'est uniquement un coût."
    }}
  ],
  "current_context": {{
    "strengths": [
      "Trésorerie saine : 45k€",
      "Croissance régulière",
      "Pas de dette structurelle"
    ],
    "weaknesses": [
      "Rotation stocks : 60 jours",
      "Délais clients : 45 jours",
      "Marge brute : 35%"
    ],
    "summary": "Dans ce contexte, un recrutement est faisable mais nécessite une gestion prudente de la trésorerie."
  }},
  "scenarios": {{
    "optimistic": {{
      "description": "Le directeur commercial génère +15% de CA dès le 3ème mois. Votre trésorerie remonte à 50k€ en juin. Le recrutement est rentabilisé dès le 8ème mois.",
      "key_milestones": ["50k€ en juin", "rentabilisé au 8ème mois"]
    }},
    "realistic": {{
      "description": "Montée en charge progressive sur 6 mois. Impact positif sur le CA à partir du 6ème mois. Trésorerie minimale à 12k€ en mars, puis remontée progressive.",
      "risk_periods": ["12k€ en mars"]
    }},
    "pessimistic": {{
      "description": "Retard dans la génération de CA. Trésorerie sous les 10k€ en mars-avril. Risque de découvert si un client majeur retarde son paiement.",
      "risk_periods": ["10k€ en mars-avril"]
    }},
    "best_case": "Le scénario optimiste montre une trésorerie qui remonte à 65k€ en juin, avec un retour sur investissement dès le 7ème mois.",
    "worst_case": "Le scénario pessimiste expose à un risque de découvert en mars-avril, nécessitant des mesures préventives."
  }},
  "recommended_actions": [
    {{
      "priority": "critical",
      "action": "Négocier des délais de paiement fournisseurs (+5 jours)",
      "impact": "Libère 8k€ de trésorerie"
    }},
    {{
      "priority": "important",
      "action": "Décaler l'embauche au 1er février",
      "impact": "Gain de 7k€ en janvier"
    }},
    {{
      "priority": "recommended",
      "action": "Mettre en place un suivi trésorerie hebdomadaire",
      "impact": "Meilleure visibilité"
    }}
  ],
  "alternatives": [
    {{
      "name": "Recrutement Partiel",
      "description": "Recruter à mi-temps (30k€/an) pour tester le marché avant un engagement complet.",
      "impact": "-6k€"
    }},
    {{
      "name": "Freelance Premium",
      "description": "Travailler avec un consultant senior (4k€/mois) sur 6 mois pour valider l'approche.",
      "impact": "-24k€"
    }}
  ],
  "hypotheses": [
    {{
      "id": "salary",
      "label": "Salaire brut annuel",
      "value": 60000,
      "type": "number"
    }},
    {{
      "id": "charges",
      "label": "Charges sociales (%)",
      "value": 42,
      "type": "number"
    }},
    {{
      "id": "start-date",
      "label": "Date d'embauche",
      "value": "2024-01-01",
      "type": "date"
    }}
  ],
  
  OR for investment/machine purchase:
  "hypotheses": [
    {{
      "id": "amount",
      "label": "Montant investissement",
      "value": 80000,
      "type": "number"
    }},
    {{
      "id": "productivity_gain",
      "label": "Gain de productivité (%)",
      "value": 20,
      "type": "number"
    }},
    {{
      "id": "payback_period",
      "label": "Période de retour (mois)",
      "value": 24,
      "type": "number"
    }},
    {{
      "id": "maintenance_cost",
      "label": "Coût maintenance annuel",
      "value": 5000,
      "type": "number"
    }}
  ],
  "report_structure": {{
    "sections_order": ["decision_summary", "key_metrics", "critical_factors", "current_context", "scenarios", "recommended_actions", "alternatives"],
    "sections_config": {{
      "decision_summary": {{ "visible": true }},
      "key_metrics": {{ "visible": true }},
      "critical_factors": {{ "visible": true }},
      "current_context": {{ "visible": true }},
      "scenarios": {{ "visible": true }},
      "recommended_actions": {{ "visible": true }},
      "alternatives": {{ "visible": false }}
    }},
    "custom_sections": []
  }}
}}
```

CRITICAL: 
- Generate BOTH the narrative report AND the JSON structure
- The JSON should contain ALL the same information as the narrative, but in structured format
- Place the JSON at the END of your response, wrapped in ```json code blocks
- Ensure the JSON is valid and complete - it will be used for programmatic extraction
- The narrative report should still be complete and detailed for human reading
"""

COMPREHENSIVE_ANALYSIS_PROMPT = """
MVP CONTEXT: You are creating a professional financial analysis for investors in ONE comprehensive pass.
Generate a complete, professional analysis matching the example format. Completeness and clarity are prioritized.
Intelligent estimation is encouraged when data is missing. Professional formatting and visualizations are essential.

You are analyzing the decision: "{question}"

Your task is to generate a COMPLETE financial analysis in ONE response, including ALL sections below.

FLEXIBLE APPROACH: Work with whatever data is available in the uploaded files.
Even if files don't match expected formats, analyze what's there and extract insights.
If data is missing, make reasonable estimates based on available patterns and industry standards.

STRUCTURE YOUR ANALYSIS AS FOLLOWS:

1. DECISION SUMMARY
   - Clear description of the decision (like "Vous envisagez de recruter un directeur commercial avec un salaire brut annuel de 60 000€...")
   - Why this decision matters financially

2. KEY METRICS (Calculate these FIRST and display prominently):
   - Total Cost Charged: [value]€ over [period] months (e.g., "85k€ over 12 months")
   - Cash Impact: [value]€ average reduction (e.g., "-12k€ average reduction")
   - Break-even Point: +[value]% additional revenue required (e.g., "+4% CA supplémentaire requis")
   - Payback period if applicable
   - Format these clearly with units and periods

3. CRITICAL FACTORS (3-5 numbered factors):
   Format as:
   1. [Factor name]
      [Detailed description with specific values, e.g., "Actuellement à 45k€, elle passerait sous les 15k€ en mars"]
   
   2. [Factor name]
      [Detailed description]
   
   3. [Factor name]
      [Detailed description]

4. CURRENT FINANCIAL CONTEXT:
   - Strengths: List 3-5 specific strengths with metrics (e.g., "Trésorerie saine : 45k€")
   - Weaknesses/Areas of Attention: List 3-5 specific concerns with metrics (e.g., "Rotation stocks : 60 jours")
   - Summary paragraph

5. SCENARIOS (3 scenarios with narrative descriptions):
   
   **Scénario Optimiste:**
   [Detailed narrative description like: "Le directeur commercial génère +15% de CA dès le 3ème mois. Votre trésorerie remonte à 50k€ en juin. Le recrutement est rentabilisé dès le 8ème mois."]
   - Key milestones: [specific values and dates]
   - When decision pays off: [timeline]
   
   **Scénario Réaliste:**
   [Detailed narrative description like: "Montée en charge progressive sur 6 mois. Impact positif sur le CA à partir du 6ème mois. Trésorerie minimale à 12k€ en mars, puis remontée progressive."]
   - Risk periods: [specific months and values]
   - Recovery timeline: [description]
   
   **Scénario Pessimiste:**
   [Detailed narrative description like: "Retard dans la génération de CA. Trésorerie sous les 10k€ en mars-avril. Risque de découvert si un client majeur retarde son paiement."]
   - Danger periods: [specific months and values]
   - Risk factors: [description]
   
   **Best Case Summary:** [Brief summary of optimistic scenario highlights]
   **Worst Case Summary:** [Brief summary of pessimistic scenario risks]

6. RECOMMENDED ACTIONS (Prioritized):
   
   CRITICAL: [Action description, e.g., "Négocier des délais de paiement fournisseurs (+5 jours)"]
   Impact: [quantified impact, e.g., "Libère 8k€ de trésorerie"]
   
   IMPORTANT: [Action description, e.g., "Décaler l'embauche au 1er février"]
   Impact: [quantified impact, e.g., "Gain de 7k€ en janvier"]
   
   RECOMMENDED: [Action description, e.g., "Mettre en place un suivi trésorerie hebdomadaire"]
   Impact: [what it achieves, e.g., "Meilleure visibilité"]
   
   CRITICAL FORMATTING RULES:
   - Each action must be on its own line starting with CRITICAL:, IMPORTANT:, or RECOMMENDED:
   - Do NOT include content from other sections (alternatives, charts, scenarios) in action descriptions
   - Keep each action concise - stop when you reach the next section marker
   - Each action should be a single, focused recommendation

7. STRATEGIC ALTERNATIVES:
   
   **Alternative 1: [Name, e.g., "Recrutement Partiel"]**
   [Detailed description, e.g., "Recruter à mi-temps (30k€/an) pour tester le marché avant un engagement complet."]
   Impact tréso: [value, e.g., "-6k€"]
   
   **Alternative 2: [Name, e.g., "Freelance Premium"]**
   [Detailed description, e.g., "Travailler avec un consultant senior (4k€/mois) sur 6 mois pour valider l'approche."]
   Impact tréso: [value, e.g., "-24k€"]

8. CHARTS (Generate these with Python):
   - **Multi-scenario cash flow projection chart** (12 months):
     * Title: "Projection de trésorerie sur 12 mois"
     * Show all 3 scenarios (Optimistic, Realistic, Pessimistic) + Current scenario
     * Highlight danger zone (e.g., cash < 15k€) with colored region
     * Add annotations for key milestones
     * Professional styling: clear labels, legends, colors
     * Save as PNG: "cash_flow_projection.png"
   
   - **Impact visualization chart** (optional but recommended)
     * Show cost breakdown or impact over time
     * Save as PNG: "impact_analysis.png"

TECHNICAL REQUIREMENTS:
- Use Python code with pandas, matplotlib, seaborn
- Read ALL uploaded files first to understand structure
- Work flexibly with whatever data is available
- Calculate metrics even if estimated (completeness > perfect precision)
- Generate charts with professional styling
- Save charts as PNG files
- Handle dates robustly: use `pd.to_datetime(..., errors='coerce', format='mixed')`
- Exclude total rows from calculations
- Convert to string before using .str accessor: `df['col'].astype(str).str.method()`

OUTPUT FORMAT:
Structure your response clearly with sections marked as above.
Include Python code that:
1. Reads and analyzes the files
2. Calculates all key metrics
3. Generates the scenarios
4. Creates the charts
5. Outputs a structured summary

IMPORTANT: 
- Follow the adapted structure but be FLEXIBLE - adapt sections to the decision type
- Generate COMPLETE, DETAILED content - not just brief summaries (2-3 sentences is NOT enough)
- Be thorough: detailed explanations, specific numbers, clear reasoning, professional narrative descriptions
- If a section doesn't apply to this decision type, adapt it or skip it intelligently
- Generate EVERYTHING in this single response
- Be complete, professional, and work with available data
- If data is missing, estimate intelligently and note assumptions clearly
- Completeness and detail are prioritized over perfect precision for MVP
- Write as if presenting to investors - be impressive but accurate
- Match the example format style: detailed narrative descriptions, specific values, professional tone

CRITICAL: At the end, include a JSON object with:
- All the structured data (decision_summary, key_metrics, critical_factors, scenarios, recommended_actions, alternatives, hypotheses)
- A "report_structure" object defining which sections to display and in what order (only include sections with actual content)
- The report_structure should reflect what's actually relevant for THIS specific decision - don't include empty or irrelevant sections
"""


