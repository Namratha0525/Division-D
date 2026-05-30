import streamlit as st
import pandas as pd
import datetime

from modules.dataset_processor import DatasetProcessor
from app import run_analysis_pipelines

def load_and_map_demo_data(file_path: str = "datasets/demo_audit.csv") -> pd.DataFrame:
    raw_df = pd.read_csv(file_path)
    mapped_rows = []
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    for idx, row in raw_df.iterrows():
        ptype = row["Plastic_Type"]
        disposal = row["Disposal_Method"]
        qty = float(row["Quantity_kg"])
        
        # Determine resin code and thickness
        if "PET" in ptype:
            resin_code = 1
            thickness = 250
        elif "LDPE" in ptype:
            resin_code = 4
            thickness = 40
        elif "Multi-layer" in ptype:
            resin_code = 7
            thickness = 80
        else:
            resin_code = 7
            thickness = 150
            
        # Determine disposal method key
        disp_upper = disposal.upper()
        if "RECYCLE" in disp_upper:
            disposal_method = "RECYCLED"
        elif "CO_PROCESS" in disp_upper or "CO-PROCESS" in disp_upper:
            disposal_method = "CO_PROCESSED"
        elif "LANDFILL" in disp_upper:
            disposal_method = "LANDFILLED"
        elif "INCINERATE" in disp_upper:
            disposal_method = "INCINERATED"
        elif "BURN" in disp_upper:
            disposal_method = "OPEN_BURNT"
        else:
            disposal_method = "LANDFILLED"
            
        mapped_rows.append({
            "date": today_str,
            "resin_code": resin_code,
            "weight_kg": qty,
            "disposal_method": disposal_method,
            "thickness_microns": thickness
        })
        
    mapped_df = pd.DataFrame(mapped_rows)
    
    if not raw_df.empty:
        inst = raw_df.iloc[0]["Institution"]
        state = raw_df.iloc[0]["State"]
        st.session_state["institution_name"] = inst
        st.session_state["benchmark_state"] = state
        
        district_map = {
            "Karnataka": "Bengaluru Urban",
            "Maharashtra": "Mumbai City",
            "Tamil Nadu": "Chennai",
            "Delhi": "New Delhi",
            "Uttar Pradesh": "Lucknow",
            "West Bengal": "Kolkata",
            "Gujarat": "Ahmedabad"
        }
        st.session_state["benchmark_district"] = district_map.get(state, "Bengaluru Urban")
        
    return mapped_df

# Configure page
st.set_page_config(page_title="Audit Form | PlasticWise AI", layout="wide")

st.markdown("<h1 style='color:#1E4620;'>📝 Waste Audit Data Ingestion</h1>", unsafe_allow_html=True)
st.markdown("Add monthly logging details manually or upload batch CSV audit sheets.")

# Prominent Load Demo Data button
col_demo, _ = st.columns([1, 2])
with col_demo:
    if st.button("🚀 Load Demo Data", use_container_width=True):
        try:
            processor = DatasetProcessor()
            demo_df = load_and_map_demo_data("datasets/demo_audit.csv")
            cleaned_demo = processor.clean_audit_data(demo_df)
            st.session_state["audit_df"] = cleaned_demo
            st.session_state["data_processed"] = True
            run_analysis_pipelines()
            st.success("🎉 Demo data successfully loaded! All reports and dashboards are pre-populated.")
            st.dataframe(cleaned_demo)
        except Exception as e:
            st.error(f"Error loading demo data: {e}")

tab1, tab2 = st.tabs(["📤 Bulk CSV Upload", "✍️ Manual Form Entry"])

processor = DatasetProcessor()

with tab1:

    st.subheader("Upload Audit Dataset")
    st.markdown(
        "Upload a CSV file containing columns: `date`, `resin_code`, `weight_kg`, `disposal_method`, `thickness_microns`."
    )
    
    # Template CSV download
    template_df = pd.DataFrame([
        {"date": "2026-05-30", "resin_code": 1, "weight_kg": 12.5, "disposal_method": "RECYCLED", "thickness_microns": 250},
        {"date": "2026-05-30", "resin_code": 6, "weight_kg": 5.0, "disposal_method": "LANDFILLED", "thickness_microns": 40}
    ])
    csv_template = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Template CSV Schema",
        data=csv_template,
        file_name="plasticwise_audit_template.csv",
        mime="text/csv"
    )

    uploaded_file = st.file_uploader("Select audit CSV file", type=["csv"])
    
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(uploaded_file)
            cleaned_df = processor.clean_audit_data(raw_df)
            
            st.success(f"Successfully processed {len(cleaned_df)} rows of data!")
            st.dataframe(cleaned_df.head(10))
            
            if st.button("Save & Analyze Ingested Data"):
                st.session_state["audit_df"] = cleaned_df
                st.session_state["data_processed"] = True
                run_analysis_pipelines()
                st.toast("Analysis completed! Head to Dashboard or Compliance pages.", icon="🚀")
                
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")

with tab2:
    st.subheader("Manual Record Registration")
    
    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            audit_date = st.date_input("Audit Date", value=datetime.date.today())
            resin_code = st.selectbox(
                "Resin Identification Code (RIC)",
                options=[1, 2, 3, 4, 5, 6, 7],
                format_func=lambda x: f"RIC {x}: { {1:'PET', 2:'HDPE', 3:'PVC', 4:'LDPE', 5:'PP', 6:'PS (Polystyrene)', 7:'Other'}[x] }"
            )
            weight_kg = st.number_input("Plastic Weight (kg)", min_value=0.1, step=0.1)
            
        with col2:
            disposal_method = st.selectbox(
                "Disposal Pathway",
                options=["RECYCLED", "CO_PROCESSED", "LANDFILLED", "INCINERATED", "OPEN_BURNT"],
                format_func=lambda x: {
                    "RECYCLED": "Recycling / Shredding",
                    "CO_PROCESSED": "Cement Kiln Co-processing",
                    "LANDFILLED": "Municipal Landfill Bin",
                    "INCINERATED": "Waste-to-Energy",
                    "OPEN_BURNT": "Open Facility Incineration / Burning (Illegal)"
                }[x]
            )
            thickness_microns = st.number_input(
                "Micron Thickness (if film/carry bag, else enter 0)",
                min_value=0,
                value=150,
                step=1
            )
            
        submit_btn = st.form_submit_button("Add Record to Session Audit Log")
        
        if submit_btn:
            new_row = {
                "date": audit_date.strftime("%Y-%m-%d"),
                "resin_code": resin_code,
                "weight_kg": weight_kg,
                "disposal_method": disposal_method,
                "thickness_microns": thickness_microns if thickness_microns > 0 else None
            }
            
            try:
                # Add to existing session frame
                new_df = pd.DataFrame([new_row])
                cleaned_new_row = processor.clean_audit_data(new_df)
                
                if st.session_state["audit_df"].empty:
                    st.session_state["audit_df"] = cleaned_new_row
                else:
                    st.session_state["audit_df"] = pd.concat([st.session_state["audit_df"], cleaned_new_row], ignore_index=True)
                    
                st.session_state["data_processed"] = True
                run_analysis_pipelines()
                st.success("Record appended successfully and models recalculated!")
                
            except Exception as e:
                st.error(f"Validation error: {e}")

    # Persistent Display of Structured Audit Data Input (Deliverable 1)
    df = st.session_state.get("audit_df")
    if df is not None and not df.empty:
        st.divider()
        st.markdown("<h3 style='color:#1E4620;'>📋 Active Audit Inventory Registry</h3>", unsafe_allow_html=True)
        
        # 1. Total KPI Summary Metrics Grid
        total_gen = float(df["weight_kg"].sum())
        total_rec = float(df[df["disposal_method"].isin(["RECYCLED", "CO_PROCESSED"])]["weight_kg"].sum())
        total_land = float(df[df["disposal_method"] == "LANDFILLED"]["weight_kg"].sum())
        total_inc = float(df[df["disposal_method"] == "INCINERATED"]["weight_kg"].sum())
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Waste Generated", f"{total_gen:.1f} kg")
        with c2:
            st.metric("Total Recycled / Co-Processed", f"{total_rec:.1f} kg")
        with c3:
            st.metric("Total Landfilled", f"{total_land:.1f} kg")
        with c4:
            st.metric("Total Incinerated", f"{total_inc:.1f} kg")
            
        # 2. Build Structured Display DataFrame
        display_rows = []
        for idx, row in df.iterrows():
            ric = row["resin_code"]
            # Category mapping
            if ric in [1, 2]:
                cat = "Category I (Rigid)"
            elif ric in [4, 5]:
                cat = "Category II (Flexible)"
            elif ric in [3, 7]:
                cat = "Category III (Multilayered)"
            elif ric == 6:
                cat = "Category III (Multilayered)"
            else:
                cat = "Category IV (Compostable)"
                
            poly = row.get("polymer_desc", f"RIC {ric}")
            weight = row["weight_kg"]
            disp = row.get("disposal_desc", row["disposal_method"])
            thick = row["thickness_microns"]
            thick_str = f"{thick:.0f}" if pd.notna(thick) and thick > 0 else "N/A"
            
            # Compliance Check
            is_violating = False
            reasons = []
            if pd.notna(thick) and 0 < thick < 120:
                is_violating = True
                reasons.append("Thickness < 120 microns")
            if row["disposal_method"] == "OPEN_BURNT":
                is_violating = True
                reasons.append("Illegal Open Burning")
            if ric == 6 and row["disposal_method"] != "RECYCLED":
                is_violating = True
                reasons.append("Banned Single-Use")
                
            status = "❌ Non-Compliant (" + ", ".join(reasons) + ")" if is_violating else "✅ Compliant"
            
            display_rows.append({
                "Plastic Category": cat,
                "Polymer Type": poly,
                "Weight (kg)": round(weight, 1),
                "Disposal Method": disp,
                "Thickness (Microns)": thick_str,
                "Compliance Status": status
            })
            
        display_df = pd.DataFrame(display_rows)
        st.dataframe(display_df, use_container_width=True)

