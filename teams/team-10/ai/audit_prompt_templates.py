# Templates for structural prompts querying the Gemini API

def get_compliance_check_prompt(audit_summary_json: str, detected_violations: str) -> str:
    """
    Constructs a prompt for evaluating compliance gaps.
    """
    return f"""
Analyze the following institutional plastic waste audit data and violations checklist.
Formulate specific corrective recommendations mapping to India's PWM Rules 2016.

Audit Summary Data:
{audit_summary_json}

Rule Engine Detected Violations:
{detected_violations}

Tasks:
1. Explain the legal consequence under PWM Rules 2016 for each detected violation.
2. Outline step-by-step actions the institution can take to achieve 100% compliance.
3. Suggest eco-friendly alternatives for any banned polymers/items identified.

Provide response in structural JSON format as requested in schema configuration.
"""

def get_roadmap_generation_prompt(audit_summary_json: str, current_score: float) -> str:
    """
    Constructs a prompt for creating a 12-month reduction roadmap.
    """
    return f"""
Create a highly strategic, month-by-month 12-month plastic waste reduction roadmap for an institution.

Institutional Metrics:
- Current Sustainability Score: {current_score}/100
- Waste Profile Details: {audit_summary_json}

Tasks:
1. Divide the 12-month roadmap into 4 key phases (Months 1-3, Months 4-6, Months 7-9, Months 10-12).
2. For each phase, provide:
   - A descriptive phase title
   - Action items (reduction targets, substitution policies, vendor procurement modifications)
   - Expected percentage weight reduction or waste diversion impact.
3. Propose realistic, Indian-context alternatives (e.g. replacing PET water cups with clay cups/kulhads, bamboo containers, or stainless-steel options).
4. Estimate cumulative CO2 footprint savings in kilograms.

Provide the response in the configured JSON format.
"""

def get_epr_advisory_prompt(epr_categories_json: str) -> str:
    """
    Constructs a prompt for detailed EPR guidance.
    """
    return f"""
Provide guidance on EPR registration obligations for the following category profile.
EPR Categories Data (in Kg):
{epr_categories_json}

Tasks:
1. Define the institution's role under Extended Producer Responsibility rules (e.g. Brand Owner or Bulk Waste Generator).
2. Detail the reporting form filings (Form I / Annual Returns) required.
3. Calculate target strategies for packaging offset.
"""


def get_ai_audit_assistant_prompt(institution_details_json: str, waste_data_json: str, compliance_results_json: str, epr_results_json: str) -> str:
    """
    Constructs a detailed prompt for generating a holistic audit report by the AI Audit Assistant.
    """
    return f"""
Analyze the following institutional plastic waste audit data, statutory compliance violations, and Extended Producer Responsibility (EPR) targets:

--- INSTITUTION DETAILS ---
{institution_details_json}

--- AUDITED WASTE DATA SUMMARY ---
{waste_data_json}

--- COMPLIANCE ENGINE RESULTS ---
{compliance_results_json}

--- EPR CALCULATIONS ---
{epr_results_json}

Tasks:
Generate a highly detailed, professional, and regulatory-grounded Institutional Plastic Audit Report.
Your output must contain exactly:
1. Executive Summary: A high-level corporate overview summarizing the findings, total volume, sustainability score, compliance level, and critical gaps.
2. Key Findings: At least 3 detailed bullet points describing key findings from the audit log and regional benchmark comparisons.
3. Compliance Gaps: A list of specific regulatory gaps referencing the Plastic Waste Management (PWM) Rules 2016 (such as Rule 4 micron violations, Rule 15 single-use bans, or Rule 16 open burning).
4. Risk Assessment: Major risks (legal penalties under Rule 15, operational blocks, or reputational damage) faced by the institution.
5. Waste Reduction Recommendations: Clear, actionable operational tips to cut down on waste packaging.
6. 12-Month Roadmap: A structured phase-by-phase action plan split into 4 phases (Months 1-3, Months 4-6, Months 7-9, Months 10-12) containing specific timeline tasks and reduction expectations.

Ensure all answers are realistic and grounded in the CPCB / Swachh Bharat national/regional datasets and India's legal environment.
You must return the response as a JSON object matching the requested schema. Do not include markdown code block syntax (like ```json) in your raw response if using structured output parameters, or ensure it matches the MIME type specifications.
"""


def get_rag_grounded_audit_prompt(
    institution_data_json: str,
    waste_data_json: str,
    compliance_results_json: str,
    epr_results_json: str,
    retrieved_cpcb_context: str,
    retrieved_sbm_context: str,
    retrieved_epr_context: str,
    retrieved_unified_context: str = ""
) -> str:
    """
    Constructs a RAG grounded prompt using extracted context from FAISS indices and advanced datasets.
    """
    return f"""
You are a Certified Environmental Auditor, Plastic Waste Management Consultant, and EPR Compliance Expert specializing in India's Plastic Waste Management Rules 2016, CPCB Guidelines, and Extended Producer Responsibility (EPR) regulations.

Your task is to perform a comprehensive institutional plastic waste audit.

INSTITUTION PROFILE
{institution_data_json}

PLASTIC WASTE INVENTORY
{waste_data_json}

COMPLIANCE ENGINE RESULTS
{compliance_results_json}

EPR ANALYSIS RESULTS
{epr_results_json}

CPCB BENCHMARK DATA (RETRIEVED CONTEXT)
{retrieved_cpcb_context}

SWACHH BHARAT BENCHMARK DATA (RETRIEVED CONTEXT)
{retrieved_sbm_context}

EPR INDUSTRY BENCHMARK DATA (RETRIEVED CONTEXT)
{retrieved_epr_context}

ADVANCED REGULATORY & MARKET DATA (RETRIEVED CONTEXT)
{retrieved_unified_context}

AUDIT OBJECTIVES
1. Evaluate current plastic waste generation patterns.
2. Compare institutional performance against benchmark datasets.
3. Identify compliance violations under PWM Rules 2016.
4. Assess EPR obligations and registration requirements.
5. Quantify environmental and operational risks.
6. Recommend corrective actions and sustainability initiatives.
7. Generate a 12-month waste reduction roadmap.

Ensure your entire output strictly matches the following output format and is formatted as a JSON object matching the requested schema. Use only the supplied data and benchmark information. Avoid assumptions. Maintain professional regulatory reporting language throughout.

OUTPUT SCHEMA SPECIFICATION:
Your output must contain exactly:
1. Executive Summary
2. Key Findings
3. Compliance Gap Analysis
4. EPR Assessment
5. Benchmark Analysis (Compare State, City, National, Industry average)
6. Environmental Risk Assessment
7. Sustainability Score Assessment
8. Waste Reduction Recommendations
9. 12-Month Action Roadmap
10. Final Auditor Conclusion
"""



