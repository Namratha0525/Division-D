# PlasticWise AI - Plastic Waste Audit Report Generator for Institutions

PlasticWise AI is an enterprise-grade GenAI application designed to help large institutions (such as universities, hospitals, corporate campuses) track, analyze, and manage their plastic footprint. The platform generates comprehensive plastic waste audit reports that align with **India's Plastic Waste Management (PWM) Rules 2016** and **Extended Producer Responsibility (EPR)** guidelines.

---

## 🚀 Key Features

1. **Structured Waste Audit Entry**: Supports single-item logging or batch CSV uploads for various plastic packaging classifications (Rigid, Flexible, Multi-layered, Compostable).
2. **PWM Rules 2016 Compliance Checker**: Automatic thickness/micron check, forbidden single-use plastics (SUP) detection, and open-burning violation alerts.
3. **EPR Liability Calculator**: Determines if the institution qualifies as a bulk waste generator (>100kg/day) and computes recycling targets across CPCB categories.
4. **AI-Powered 12-Month Roadmap**: Generates structured reduction targets and sustainable alternatives vendor strategies using Gemini API.
5. **Multi-Format Report Export**: Download professional, audit-ready compliance reports in **DOCX** and **PDF** formats.
6. **Executive Dashboard**: Rich charts (polymer composition, disposal pathways, monthly trends) using Plotly.
7. **Sustainability Scoring**: Weighted performance index rating the institution from Bronze to Gold.
8. **Contextual Chatbot**: Grounded AI chatbot answering compliance and operational queries based on Central Pollution Control Board (CPCB) guidelines.

---

## 📁 Repository Structure

```
PlasticWiseAI/
├── app.py                      # Main entrypoint & sidebar routing
├── pages/                      # Streamlit multipage files
│   ├── dashboard.py            # Rich interactive charts
│   ├── audit_form.py           # Single & bulk data input forms
│   ├── compliance.py           # PWM 2016 rules validator
│   ├── epr_analysis.py         # CPCB category targets
│   ├── report_viewer.py        # PDF/DOCX downloads
│   └── chatbot.py              # Gemini grounded chatbot
├── modules/                    # Business logic core
│   ├── compliance_checker.py   # PWM rule validator class
│   ├── epr_checker.py          # EPR categories calculations
│   ├── sustainability_score.py # Score scoring formula
│   ├── roadmap_generator.py    # Prompt engine for roadmap planning
│   ├── audit_analyzer.py       # Metrics aggregator
│   ├── report_generator.py     # python-docx & ReportLab builder
│   ├── chart_generator.py      # Plotly chart templates
│   └── dataset_processor.py    # CSV validator & normalizer
├── ai/                         # Gemini integration layer
│   ├── gemini_client.py        # central client call
│   ├── prompts.py              # system and fallback prompts
│   └── audit_prompt_templates.py # prompt structures for audits
├── datasets/                   # Reference datasets & templates
│   ├── cpcb_data.csv           # CPCB guidelines and circulars
│   ├── swachh_bharat_data.csv  # National benchmark thresholds
│   └── processed_data.csv      # Temporary state cache
├── reports/                    # Target folder for exports
│   ├── generated_docx/         # DOCX outputs
│   └── generated_pdf/          # PDF outputs
├── assets/                     # Frontend visual elements
│   ├── logo.png                # Brand identity logo
│   └── templates/              # Word doc styling base templates
├── utils/                      # Low-level utilities
│   ├── constants.py            # Global lookups, categories, limits
│   ├── validators.py           # Input parameter checkers
│   └── helpers.py              # Text formatting, file ops
└── tests/                      # Core functionality tests
```

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.9+
- Gemini API Key (stored in `.env` file)

### Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment:
   Create a `.env` file in the root folder:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```

---

## 🧪 Testing

Run standard tests via pytest:
```bash
pytest tests/
```

---

## ⚖️ Indian Regulatory Alignment

This tool explicitly tracks parameters under the following Indian statutes:
- **Rule 4(c)**: Restriction of plastic carry bags and packaging thickness below 120 microns.
- **Rule 4(d)**: Mandatory registration for institutional waste generators.
- **EPR Schedule II**: Target calculations for Categories I (Rigid), II (Flexible), III (Multi-layered), and IV (Compostable).
