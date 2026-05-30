import json
import pandas as pd
from utils.constants import MICRON_LIMIT
from ai.gemini_client import GeminiClient
from ai.prompts import COMPLIANCE_EXPERT_SYSTEM_PROMPT
from ai.audit_prompt_templates import get_compliance_check_prompt
from modules.advanced_dataset_analyzer import AdvancedDatasetAnalyzer

class ComplianceChecker:
    def __init__(self, gemini_client: GeminiClient = None):
        self.client = gemini_client or GeminiClient()
        self.analyzer = AdvancedDatasetAnalyzer()

    def check_violations(self, df: pd.DataFrame) -> list:
        """
        Runs local rule checks on the waste dataset.
        """
        violations = []

        # 1. Check Micron Thickness Violation (Carry bags / sheets < 120 microns)
        thin_plastics = df[(df["thickness_microns"] > 0) & (df["thickness_microns"] < MICRON_LIMIT)]
        if not thin_plastics.empty:
            total_thin_weight = thin_plastics["weight_kg"].sum()
            violations.append({
                "rule_id": "PWM_RULE_4C_MICRONS",
                "title": "Thickness Limit Breach",
                "severity": "CRITICAL",
                "description": f"Detected carry bags/packaging sheets with thickness below the legal limit of {MICRON_LIMIT} microns (Total: {total_thin_weight:.1f} kg).",
                "affected_weight_kg": float(total_thin_weight)
            })

        # 2. Check Open Burning Violation (Environmental breach)
        burning_records = df[df["disposal_method"] == "OPEN_BURNT"]
        if not burning_records.empty:
            total_burned_weight = burning_records["weight_kg"].sum()
            violations.append({
                "rule_id": "NGT_OPEN_BURNING_BAN",
                "title": "Illegal Open Burning",
                "severity": "CRITICAL",
                "description": f"Plastic waste is being incinerated via open burning, which is prohibited under NGT directives and PWM Rule 16 (Total: {total_burned_weight:.1f} kg).",
                "affected_weight_kg": float(total_burned_weight)
            })

        # 3. Check Single Use Plastic (SUP) Forbidden Items (RIC 6 - PS or general non-recycled packaging)
        sup_records = df[(df["resin_code"] == 6) & (df["disposal_method"] != "RECYCLED")]
        if not sup_records.empty:
            total_sup_weight = sup_records["weight_kg"].sum()
            violations.append({
                "rule_id": "PWM_SUP_BAN_2022",
                "title": "Banned Single-Use Plastic Usage",
                "severity": "HIGH",
                "description": f"Usage of banned polystyrene (RIC 6) or un-recycled single-use items detected in cafeteria/facilities (Total: {total_sup_weight:.1f} kg).",
                "affected_weight_kg": float(total_sup_weight)
            })

        return violations

    def get_ai_compliance_report(self, df: pd.DataFrame, state_name: str = "Maharashtra", district_name: str = "Mumbai City") -> dict:
        """
        Runs local check rules, computes compliance metrics, and queries Gemini
        or falls back to mock recommendations grounded in Rajya Sabha, polymer and application trends.
        """
        from modules.data_downloader import DataDownloader
        violations = self.check_violations(df)
        
        # Calculate stats
        total_weight = float(df["weight_kg"].sum()) if not df.empty else 0.0
        affected_weight = sum(v["affected_weight_kg"] for v in violations)
        compliance_percentage = round(max(0.0, ((total_weight - affected_weight) / total_weight * 100)), 1) if total_weight > 0 else 100.0
        
        number_of_violations = len(violations)
        critical_violations = sum(1 for v in violations if v["severity"] == "CRITICAL")
        
        if compliance_percentage == 100.0:
            overall_compliance_rating = "EXCELLENT"
        elif compliance_percentage >= 90.0:
            overall_compliance_rating = "GOOD"
        elif compliance_percentage >= 75.0:
            overall_compliance_rating = "ATTENTION REQUIRED"
        else:
            overall_compliance_rating = "NON-COMPLIANT"

        # Load local benchmarks context
        downloader = DataDownloader()
        bench = downloader.load_benchmark_data(state_name, district_name)
        
        # Calculate monthly average institutional waste
        daily_totals = df.groupby(df["date"].dt.date)["weight_kg"].sum() if not df.empty else pd.Series()
        avg_daily = daily_totals.mean() if not daily_totals.empty else 0.0
        inst_monthly_avg = avg_daily * 30.0
        
        # Retrieve national polymer & application trends
        poly_trends = self.analyzer.analyze_polymer_trends(2026)
        app_trends = self.analyzer.analyze_application_usage(2026)
        
        # Identify high-risk polymers and alternative recommendations from datasets
        high_risk_polymers = ["PS (Polystyrene)", "PVC (Polyvinyl Chloride)", "LDPE (Low-Density Polyethylene) < 120 microns"]
        
        # Single-use dependency
        sup_weight = df[df["resin_code"].isin([6]) | ((df["thickness_microns"] > 0) & (df["thickness_microns"] < MICRON_LIMIT))]["weight_kg"].sum() if not df.empty else 0.0
        sup_dependency_pct = round((sup_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0
        
        alt_materials = [
            {"polymer": "PET (RIC 1)", "alternative": "Stainless steel containers, glass bottles, or multi-use dispensers."},
            {"polymer": "LDPE (RIC 4)", "alternative": "Certified compostable bags (IS/ISO 17088), cotton/jute bags, or paper bags."},
            {"polymer": "PS (RIC 6)", "alternative": "Bagasse plates/cups, bamboo cutlery, or ceramic wares."}
        ]

        summary = {
            "total_records": len(df),
            "total_weight_kg": total_weight,
            "categories_found": list(df["polymer_desc"].unique()) if not df.empty else [],
            "sup_dependency_pct": sup_dependency_pct,
            "benchmark_context": {
                "state_name": state_name,
                "district_name": district_name,
                "institution_monthly_avg_kg": round(inst_monthly_avg, 1),
                "district_monthly_avg_kg": bench.get("district_monthly_avg_kg", 180.0),
                "state_monthly_avg_kg": bench.get("state_monthly_avg_kg", 220.0),
                "source_citation": bench.get("source_citation")
            }
        }
        
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "violations_analysis": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "rule_id": {"type": "STRING"},
                            "legal_citation": {"type": "STRING"},
                            "legal_consequence": {"type": "STRING"},
                            "corrective_actions": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        },
                        "required": ["rule_id", "legal_citation", "legal_consequence", "corrective_actions"]
                    }
                },
                "general_recommendations": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["violations_analysis", "general_recommendations"]
        }

        # Query Gemini API with integrated benchmark facts
        prompt = get_compliance_check_prompt(json.dumps(summary), json.dumps(violations))
        ai_response_raw = self.client.query_gemini(
            system_instruction=COMPLIANCE_EXPERT_SYSTEM_PROMPT,
            prompt=prompt,
            schema=json_schema
        )

        try:
            ai_data = json.loads(ai_response_raw)
            if "violations_analysis" not in ai_data or "general_recommendations" not in ai_data:
                raise KeyError("Missing required compliance schema keys")
        except Exception:
            # Safe parsing backup
            ai_data = {
                "violations_analysis": [
                    {
                        "rule_id": v["rule_id"],
                        "legal_citation": "Rule 4, India Plastic Waste Management Rules 2016",
                        "legal_consequence": "Fines, confiscation of banned items, or sealing of facility spaces.",
                        "corrective_actions": [
                            v["description"],
                            "Shift to sustainable alternatives and enforce audits.",
                            f"Recommend transitioning away from high-risk polymers: {', '.join(high_risk_polymers)}."
                        ]
                    } for v in violations
                ],
                "general_recommendations": [
                    f"Target institutional waste reduction below the regional {district_name} average of {bench.get('district_monthly_avg_kg')} kg/month.",
                    f"Implement alternative material policies focusing on replacing single-use items (Current single-use dependency: {sup_dependency_pct}%).",
                    f"Align procurement policies with national CPCB polymer trends (Top national polymer: {poly_trends.get('top_polymers', [['PP', 0]])[0][0]}).",
                    "Establish a green campus steering committee to log packaging audits."
                ]
            }

        # Inject extra polymer/application stats into ai_analysis
        ai_data["high_risk_polymers"] = high_risk_polymers
        ai_data["sup_dependency_pct"] = sup_dependency_pct
        ai_data["alt_materials"] = alt_materials

        return {
            "violations": violations,
            "compliance_percentage": compliance_percentage,
            "number_of_violations": number_of_violations,
            "critical_violations": critical_violations,
            "overall_compliance_rating": overall_compliance_rating,
            "ai_analysis": ai_data
        }
