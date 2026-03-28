import streamlit as st
from PIL import Image
import datetime
from core.ai_engine import extract_medical_info
from core.actions import sync_to_calendar

st.set_page_config(page_title="MediBridge", page_icon="🩺", layout="wide")

st.title("MediBridge 🩺")
st.write("Upload medical prescriptions or lab reports to extract information and sync to your Care Plan.")

uploaded_file = st.file_uploader(
    "Upload Medical Document", 
    type=["jpg", "jpeg", "png"],
    help="Please upload a clear photo of your prescription or lab report for AI analysis."
)

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Messy Input")
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', width='stretch')
        
    with col2:
        st.subheader("Structured Action")
        
        if "medical_context" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("Analyzing image..."):
                print(f"DEBUG: Processing medical image with fallback support at {datetime.datetime.now()}")
                st.session_state.medical_context = extract_medical_info(image)
                st.session_state.last_uploaded = uploaded_file.name
                
        medical_context = st.session_state.medical_context
        
        if medical_context:
            st.success("Analysis Complete!")
            
            st.write(f"**Patient Name:** {medical_context.patient_name}")
            
            st.markdown("### Medications")
            if medical_context.medications:
                for med in medical_context.medications:
                    st.write(f"- **{med.name}**: {med.dosage} ({med.frequency})")
            else:
                st.write("No medications found.")
                
            st.markdown("### Critical Alerts")
            if medical_context.critical_alerts:
                for alert in medical_context.critical_alerts:
                    st.warning(alert)
            else:
                st.info("No critical alerts found.")
                
            st.markdown("---")
            st.subheader("Care Plan Sync")
            st.warning("Please review the extracted data above before syncing to your calendar.")
            
            if st.button("Confirm and Sync to Care Plan", help="Click to save these reminders to your Google Calendar"):
                with st.spinner("Syncing to Google Calendar..."):
                    success = sync_to_calendar(medical_context)
                    if success:
                        st.success("Successfully synced to Care Plan!")
                    else:
                        st.error("Failed to sync. Please check your calendar integration.")
        else:
            st.error("Could not extract information. The image might be too blurred or unclear.")
