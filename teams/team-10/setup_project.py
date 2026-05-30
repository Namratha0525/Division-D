import os
import sys
import logging

# Ensure project root is in path for modules import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProjectSetup")

def print_banner():
    banner = """
========================================================================
[RECYCLE]  PLASTICWISE AI - REVOLUTIONIZING INSTITUTIONAL PLASTIC MANAGEMENT  [RECYCLE]
========================================================================
   Establishing repository structures, downloading datasets & benchmark indices...
========================================================================
    """
    print(banner)

def create_folders():
    print("[1/5] Scaffolding repository directory structures...")
    directories = [
        "pages",
        "modules",
        "ai",
        "datasets",
        "datasets/raw",
        "datasets/processed",
        "reports",
        "reports/generated_docx",
        "reports/generated_pdf",
        "assets",
        "assets/templates",
        "utils",
        "tests"
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f" [OK] Created folder: {directory}")
        else:
            print(f" [INFO] Directory already exists: {directory}")

def check_dependencies():
    print("\n[2/5] Inspecting python ecosystem requirements...")
    libraries = ["streamlit", "pandas", "plotly", "docx", "reportlab", "google.generativeai"]
    all_ok = True
    
    for lib in libraries:
        try:
            __import__(lib)
            print(f" [OK] Package verified: {lib}")
        except ImportError:
            print(f" [ERROR] Missing package dependency: {lib}")
            all_ok = False
            
    if not all_ok:
        print(" [WARN] Warning: Some python dependencies are not installed. Run 'pip install -r requirements.txt'")
    else:
        print(" [OK] All core package requirements verified successfully!")

def run_dataset_downloads():
    print("\n[3/5] Programmatically querying national CPCB, Swachh Bharat & EPR datasets...")
    from modules.data_downloader import DataDownloader
    
    downloader = DataDownloader()
    
    # 1. Get CPCB data
    cpcb_file = downloader.download_cpcb_dataset()
    print(f" [OK] CPCB raw data location: {cpcb_file}")
    
    # 2. Get Swachh Bharat data
    sbm_file = downloader.download_swachh_bharat_dataset()
    print(f" [OK] Swachh Bharat raw data location: {sbm_file}")

    # 3. Get CPCB EPR data
    epr_file = downloader.download_epr_portal_dataset()
    print(f" [OK] EPR Portal raw data location: {epr_file}")
    
    # 4. Clean and process
    downloader.preprocess_datasets()
    print(" [OK] Benchmark databases preprocessed and cached in datasets/processed/")

def validate_datasets():
    print("\n[4/5] Checking database file availability...")
    paths = [
        "datasets/raw/cpcb_data.csv",
        "datasets/raw/swachh_bharat_data.csv",
        "datasets/raw/epr_portal_data.csv",
        "datasets/processed/cpcb_processed.csv",
        "datasets/processed/swachh_bharat_processed.csv",
        "datasets/processed/epr_processed.csv"
    ]
    
    for path in paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f" [OK] Verified dataset file: {path} ({size} bytes)")
        else:
            print(f" [ERROR] Missing dataset file: {path}")

def generate_sample_audit():
    print("\n[5/5] Ingesting initial institutional audit log template...")
    filepath = "datasets/processed_data.csv"
    
    if os.path.exists(filepath):
        print(f" [INFO] Session template file already exists at {filepath}.")
        return
        
    sample_csv = """date,resin_code,weight_kg,disposal_method,thickness_microns
2026-05-01,1,15.2,RECYCLED,250
2026-05-02,2,42.0,RECYCLED,150
2026-05-03,6,18.5,LANDFILLED,50
2026-05-04,4,30.0,CO_PROCESSED,130
2026-05-05,7,12.0,OPEN_BURNT,30
2026-05-06,5,25.4,RECYCLED,180
2026-05-07,1,8.0,RECYCLED,250
2026-05-08,6,35.0,LANDFILLED,40
2026-05-09,4,14.5,RECYCLED,120
2026-05-10,3,9.0,INCINERATED,100
2026-05-11,2,55.0,RECYCLED,160
2026-05-12,7,28.0,LANDFILLED,80
"""
    with open(filepath, "w") as f:
        f.write(sample_csv)
    print(f" [OK] Sample audit data created: {filepath}")

def main():
    print_banner()
    create_folders()
    check_dependencies()
    run_dataset_downloads()
    validate_datasets()
    generate_sample_audit()
    print("\n========================================================================")
    print(" [INFO] PlasticWise AI project setup is complete! Run 'streamlit run app.py' to launch.")
    print("========================================================================")

if __name__ == "__main__":
    main()
