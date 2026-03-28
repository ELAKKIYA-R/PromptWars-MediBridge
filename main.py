import streamlit as st
from PIL import Image
from core.ai_engine import extract_medical_info
from core.actions import sync_to_calendar

st.set_page_config(page_title="MediBridge", page_icon="🩺")

st.title("MediBridge 🩺")
st.write("Upload medical prescriptions or lab reports to extract information and sync to your Care Plan.")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image.', use_container_width=True)
        
        with st.spinner("Analyzing image..."):
            medical_context = extract_medical_info(image)
        
        if medical_context:
            st.success("Analysis Complete!")
            
            st.subheader("Patient Name")
            st.write(medical_context.patient_name)
            
            st.subheader("Medications")
            if medical_context.medications:
                for med in medical_context.medications:
                    st.write(f"- **{med.name}**: {med.dosage} ({med.frequency})")
            else:
                st.write("No medications found.")
                
            st.subheader("Critical Alerts")
            if medical_context.critical_alerts:
                for alert in medical_context.critical_alerts:
                    st.warning(alert)
            else:
                st.write("No critical alerts found.")
                
            if st.button("Sync to Care Plan"):
                with st.spinner("Syncing to Google Calendar..."):
                    success = sync_to_calendar(medical_context)
                    if success:
                        st.success("Successfully synced to Care Plan!")
                    else:
                        st.error("Failed to sync. Please check your calendar integration.")
        else:
            st.error("Could not extract information. The image might be too blurred or unclear.")
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
