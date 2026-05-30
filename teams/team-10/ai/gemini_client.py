import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiClient")

# Get Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY environment variable is not set. AI modules will fall back to mockup mock outputs.")

class GeminiClient:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the Gemini Client configuration.
        """
        self.model_name = model_name
        self.api_enabled = api_key is not None

    def query_gemini(self, system_instruction: str, prompt: str, schema: dict = None) -> str:
        """
        Queries the Gemini generative AI model with instructions and a prompt.
        
        Args:
            system_instruction (str): System prompt grounding instructions.
            prompt (str): Prompt detailing tasks or audit data parameters.
            schema (dict, optional): Output JSON schema specification.
            
        Returns:
            str: Returns raw response text or JSON string matching requested schema.
        """
        if not self.api_enabled:
            logger.info("API Key not found; running simulated backup response.")
            return self._generate_fallback_response(prompt, schema)

        try:
            # Model configuration params
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            if schema:
                # Forces output to match a structured JSON format
                generation_config["response_mime_type"] = "application/json"
                generation_config["response_schema"] = schema

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error querying Gemini API: {e}. Falling back to default data structure.")
            return self._generate_fallback_response(prompt, schema)

    def _generate_fallback_response(self, prompt: str, schema: dict) -> str:
        """Generates realistic mock values for offline/fallback modes during hackathons."""
        # Simple mock objects based on schema detection
        if schema:
            # Look for indicators of roadmap vs compliance recs
            if "roadmap" in prompt.lower() or "month" in prompt.lower():
                return json.dumps({
                    "roadmap": [
                        {"month": "Month 1-3: Policy & Audit Setup", "target": "Eliminate Single-Use Plastic Water Bottles", "impact": "30% reduction in PET waste"},
                        {"month": "Month 4-6: Sourcing Alternatives", "target": "Swap to Compostable or Steel Cutlery", "impact": "15% reduction in category IV weight"},
                        {"month": "Month 7-9: Logistics & Training", "target": "Establish sorting lines for separation at source", "impact": "50% recycling rate improvement"},
                        {"month": "Month 10-12: External Audits", "target": "Apply for Zero Waste to Landfill Certification", "impact": "90% diversion from landfills"}
                    ],
                    "sustainability_metrics": {
                        "estimated_co2_saved_kg": 2400.0,
                        "suggested_grade_upgrade": "Gold"
                    }
                })
            else:
                return json.dumps({
                    "violations": [
                        {"rule_id": "PWM_SUP_BAN", "severity": "CRITICAL", "description": "Single-use cups found in cafeteria audit exceed thickness regulations.", "action_required": "Replace cafeteria plastic cups with ceramic mugs or compostable alternatives."}
                    ],
                    "recommendations": [
                        "Conduct weekly training sessions for sanitation staff on waste source-separation.",
                        "Register bulk waste volume status with State Pollution Control Board."
                    ]
                })
        else:
            # Check prompt keywords for interactive Chatbot advisor simulated responses
            q = prompt.lower()
            if "epr" in q:
                return (
                    "Extended Producer Responsibility (EPR) obligations under CPCB Schedule II mandate that "
                    "bulk generators track their plastic packaging. Based on CPCB categories:\n"
                    "- **Category I (Rigid)**: 70% recycling target. PET bottles must be sent to registered recyclers.\n"
                    "- **Category II (Flexible)**: Encompasses single-layer and multi-layer films.\n"
                    "- **Category III (Multilayered)**: Packaging with at least one layer of plastic and paper/foil.\n"
                    "Ensure you compile Form I filings for annual returns to stay compliant."
                )
            elif "micron" in q or "thickness" in q:
                return (
                    "Under Rule 4(c) of the Plastic Waste Management Rules 2016, carry bags and sheets made of "
                    "plastic must have a thickness of **not less than 120 microns**. Packaging below this limit is "
                    "classified as prohibited single-use plastic (SUP) and subject to seizure and penalties under Rule 15."
                )
            elif "violation" in q or "ban" in q or "rule" in q:
                return (
                    "Your audit identifies potential statutory gaps under the PWM Rules 2016:\n"
                    "1. **Rule 4(c)**: Micron thickness limit (120 microns for carry bags).\n"
                    "2. **Rule 15**: General ban on single-use plastics like polystyrene cups and cutlery.\n"
                    "3. **Rule 16**: Strict prohibition on open burning of municipal waste, which violates NGT directives.\n"
                    "Remediation requires shifting to paper/wood cutlery or compostable polymers certified under IS/ISO 17088."
                )
            elif "segregat" in q or "color" in q or "bin" in q:
                return (
                    "Institutional waste generators are required under Rule 6 to perform segregation at source:\n"
                    "- **Blue Bins**: Clean dry recyclables (PET bottles, clean LDPE films, PP containers).\n"
                    "- **Green Bins**: Biodegradable/wet wastes.\n"
                    "- **Black/Red Bins**: Reject waste and domestic hazardous items.\n"
                    "Ensure separate collection logs are maintained to verify disposal pathways."
                )
            else:
                return (
                    "Based on the Plastic Waste Management Rules 2016 (amended 2022/2023), institutions "
                    "must establish source segregation guidelines, registers for Dry Waste collection, and "
                    "verify that all collection contractors are registered with the State Pollution Control Board (SPCB).\n\n"
                    "How can I assist you further with your CPCB category targets or compliance gap audits?"
                )
