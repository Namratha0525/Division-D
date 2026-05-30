import json
from ai.gemini_client import GeminiClient
from ai.prompts import COMPLIANCE_EXPERT_SYSTEM_PROMPT
from ai.audit_prompt_templates import get_roadmap_generation_prompt

class RoadmapGenerator:
    def __init__(self, gemini_client: GeminiClient = None):
        self.client = gemini_client or GeminiClient()

    def generate_12_month_roadmap(self, audit_summary: dict, score_details: dict) -> dict:
        """
        Queries Gemini to construct a structured 12-month step-by-step reduction strategy.
        
        Args:
            audit_summary (dict): Dictionary from AuditAnalyzer.
            score_details (dict): Dictionary from SustainabilityScorer.
            
        Returns:
            dict: Structured roadmap phases list and CO2 equivalent estimates.
        """
        # Prepare text representation of waste metrics
        summary_payload = {
            "total_annual_volume_kg": audit_summary.get("total_weight_kg", 0.0),
            "dominant_polymer": audit_summary.get("dominant_polymer_type", "N/A"),
            "recycling_rate_pct": audit_summary.get("recycling_rate_pct", 0.0),
            "violations_count": score_details.get("metrics", {}).get("active_violations_count", 0)
        }

        # Prompt schema constraint
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "phases": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "phase_title": {"type": "STRING"},
                            "months": {"type": "STRING"},
                            "action_items": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "reduction_target_pct": {"type": "NUMBER"},
                            "alternatives_suggested": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        },
                        "required": ["phase_title", "months", "action_items", "reduction_target_pct", "alternatives_suggested"]
                    }
                },
                "estimated_annual_co2_saving_kg": {"type": "NUMBER"},
                "governance_tips": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["phases", "estimated_annual_co2_saving_kg", "governance_tips"]
        }

        # Formulate query prompt
        prompt = get_roadmap_generation_prompt(
            json.dumps(summary_payload),
            score_details.get("score", 0.0)
        )

        ai_response_raw = self.client.query_gemini(
            system_instruction=COMPLIANCE_EXPERT_SYSTEM_PROMPT,
            prompt=prompt,
            schema=json_schema
        )

        try:
            roadmap_data = json.loads(ai_response_raw)
        except Exception:
            # Structurally valid fallback roadmap configuration
            roadmap_data = {
                "phases": [
                    {
                        "phase_title": "Phase 1: Compliance Base & Single-Use Ban",
                        "months": "Months 1 - 3",
                        "action_items": [
                            "Audit all catering contractors to enforce Rule 15 SUP prohibitions.",
                            "Replace all plastic catering glasses and water bags with steel or glassware alternatives."
                        ],
                        "reduction_target_pct": 15.0,
                        "alternatives_suggested": ["Stainless steel pitchers", "Clay cups/Kulhads for warm beverages"]
                    },
                    {
                        "phase_title": "Phase 2: Source Segregation & Staff Training",
                        "months": "Months 4 - 6",
                        "action_items": [
                            "Set up color-coded recycling collection centers across campus facilities.",
                            "Host training webinars for campus sanitary workers on segregation of recyclable sheets."
                        ],
                        "reduction_target_pct": 20.0,
                        "alternatives_suggested": ["Bin liners made of compostable starch-based polymers (Rule 4g)"]
                    },
                    {
                        "phase_title": "Phase 3: SPCB & Vendor Integration",
                        "months": "Months 7 - 9",
                        "action_items": [
                            "Form partnership agreements with registered local plastic waste collectors.",
                            "Formalize tracking spreadsheets for weight logs sent for recycling."
                        ],
                        "reduction_target_pct": 25.0,
                        "alternatives_suggested": ["Returnable crate programs for delivery items"]
                    },
                    {
                        "phase_title": "Phase 4: Circular Economy Certification",
                        "months": "Months 10 - 12",
                        "action_items": [
                            "Establish dry waste sorting micro-centers.",
                            "Submit audit sheets to State Pollution Control Board for Zero Waste Green campus recognition."
                        ],
                        "reduction_target_pct": 30.0,
                        "alternatives_suggested": ["Reusable bags made from recycled fabric scraps"]
                    }
                ],
                "estimated_annual_co2_saving_kg": round(audit_summary.get("total_weight_kg", 0.0) * 2.52 * 0.5, 1),
                "governance_tips": [
                    "Form a core sustainability student/employee panel.",
                    "Include green terms in vendor request forms."
                ]
            }

        return roadmap_data
