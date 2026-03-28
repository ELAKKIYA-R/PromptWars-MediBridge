import streamlit as st
from PIL import Image
import datetime
import os
from core.ai_engine import extract_medical_info
from core.actions import sync_to_calendar, get_oauth_flow

# Setup GCP Cloud Logging robustly for both local and cloud environments
try:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
    import logging
    logger = logging.getLogger('medibridge_app')
except Exception as e:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('medibridge_app')
    logger.warning(f"Using local standard logging. GCP logging setup failed: {e}")

st.set_page_config(page_title="MediBridge | AI Medical Sync", page_icon="🧩", layout="wide", initial_sidebar_state="expanded")

# --- PREMIUM UI OVERRIDES ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif !important;
}

/* App Background */
.stApp {
    background: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #030712 80%);
    color: #f8fafc;
}

/* Typography Enhancements */
h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #38bdf8 !important;
    text-shadow: 0 4px 20px rgba(56, 189, 248, 0.4);
    font-weight: 700 !important;
    letter-spacing: -1px;
}
h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #e2e8f0 !important;
}

/* Glassmorphism Cards */
.glass-card {
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

/* Medication UI Component */
.med-item {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
    border-left: 4px solid #0ea5e9;
    padding: 16px 20px;
    border-radius: 8px 16px 16px 8px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
.med-item:hover {
    transform: translateX(8px);
    background: linear-gradient(135deg, rgba(51, 65, 85, 0.9), rgba(30, 41, 59, 0.9));
    border-left-color: #38bdf8;
    box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);
}

/* Alert Component */
.alert-item {
    background: linear-gradient(135deg, rgba(127, 29, 29, 0.8), rgba(69, 10, 10, 0.8));
    border-left: 4px solid #f87171;
    padding: 16px 20px;
    border-radius: 8px 16px 16px 8px;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* Elegant Buttons */
div.stButton > button, a[data-testid="baseLinkButton"] {
    background: linear-gradient(135deg, #0284c7 0%, #3b82f6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase;
    font-size: 0.9rem !important;
    box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4) !important;
}
div.stButton > button:hover, a[data-testid="baseLinkButton"]:hover {
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.6) !important;
    transform: translateY(-2px) !important;
}

/* File Uploader Hover */
[data-testid="stFileUploader"] {
    background: rgba(15, 23, 42, 0.4) !important;
    border: 1px dashed rgba(56, 189, 248, 0.5) !important;
    border-radius: 16px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #38bdf8 !important;
    background: rgba(15, 23, 42, 0.8) !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.7) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
}

header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Try to infer redirect URI intelligently
REDIRECT_URI = "https://medibridge-940688733909.asia-south1.run.app/" if not os.environ.get("LOCAL_DEV") else "http://localhost:8501/"

# --- OAUTH AUTHENTICATION GATE ---
if "user_creds" not in st.session_state:
    st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-top: 8vh;'>MediBridge 🧩</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 3rem;'>Intelligent Multi-Tenant Healthcare Extraction & Synchronization Platform</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align: center; margin-bottom: 2rem;">
            <h3 style="margin-top:0;">Secure Architect Access</h3>
            <p style="color: #cbd5e1; font-size: 1.05rem;">Connect your medical insights securely.<br/>Log in via Google OAuth to build and automate your personal Care Plan calendar.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if this is the callback redirect from Google Auth
        if "code" in st.query_params:
            auth_code = st.query_params.get("code")
            
            # If we already authenticated successfully BEFORE a rerun, just pass
            if "google_auth_success" in st.session_state:
                st.success("✅ Secure Handshake Verified.")
                st.markdown(f'<a href="{REDIRECT_URI}" target="_self"><button style="padding:10px 20px;border-radius:10px;background:#38bdf8;color:white;border:none;cursor:pointer;font-weight:bold;">Initialize Workspace</button></a>', unsafe_allow_html=True)
                st.stop()
                
            flow = get_oauth_flow(REDIRECT_URI)
            if flow:
                with st.spinner("Authenticating Securely..."):
                    try:
                        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
                        from urllib.parse import urlencode
                        qs = urlencode(st.query_params.to_dict())
                        full_url = f"{REDIRECT_URI}?{qs}"
                        
                        flow.fetch_token(authorization_response=full_url)
                        credentials = flow.credentials
                        
                        st.session_state["user_creds"] = {
                            "token": credentials.token,
                            "refresh_token": credentials.refresh_token,
                            "token_uri": credentials.token_uri,
                            "client_id": credentials.client_id,
                            "client_secret": credentials.client_secret,
                            "scopes": credentials.scopes
                        }
                        st.session_state["google_auth_success"] = True
                        
                        st.success("✅ Secure Handshake Verified.")
                        st.info("The secure connection to Google was successful. Click the button below to initialize the Care Plan Workspace.")
                        st.markdown(f'<a href="{REDIRECT_URI}" target="_self"><button style="padding:10px 20px;border-radius:10px;background:#38bdf8;color:white;border:none;cursor:pointer;font-weight:bold;">Initialize Workspace</button></a>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Authentication Session Expired or Invalid Link")
                        st.warning(f"Google login codes are one-time use and expire quickly. Please clear your session and log in again. (Error trace: {str(e)})")
                        logger.error(f"Token exchange failed: {e}")
                        st.markdown(f'<a href="{REDIRECT_URI}" target="_self"><button style="padding:10px 20px;border-radius:10px;background:#ef4444;color:white;border:none;cursor:pointer;font-weight:bold;">Start Fresh Login</button></a>', unsafe_allow_html=True)
            st.stop()
        else:
            flow = get_oauth_flow(REDIRECT_URI)
            if flow:
                auth_url, _ = flow.authorization_url(prompt='consent')
                st.link_button("🌐 Authenticate with Google", url=auth_url, use_container_width=True)
                st.info("Your PHI is strictly isolated. Data is entirely processed in-memory and never persisted to local disks.")
            else:
                st.error("Authentication Engine Offline: Configuration missing.")
    st.stop()

# --- MAIN ASSISTIVE APPLICATION ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Navigation</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
        <h4 style="color:#38bdf8; margin:0 0 10px 0;">Workflow</h4>
        <ol style="color:#cbd5e1; padding-left: 20px; margin:0; line-height: 1.6;">
            <li><b>Upload</b> HD document scan</li>
            <li><b>Audit</b> AI extraction payload</li>
            <li><b>Sync</b> to Google Calendar</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    st.info("🟢 Session Authenticated")
    if st.button("End Session"):
        del st.session_state["user_creds"]
        st.rerun()

st.title("Care Plan Workspace")

uploaded_file = st.file_uploader(
    "Drag and drop prescription or lab report", 
    type=["jpg", "jpeg", "png", "pdf"],
    help="Supports both images and multipage PDF documents for AI extraction."
)

if uploaded_file is None:
    st.markdown("""
        <div style='text-align: center; padding: 60px 20px; border-radius: 16px; background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(56, 189, 248, 0.3); margin-top: 20px;'>
            <h2 style='color:#38bdf8; margin-bottom: 15px;'>Initialize AI Extraction</h2>
            <p style='color:#94a3b8; font-size:1.1rem; max-width: 600px; margin: 0 auto; line-height: 1.6;'>Upload a clear photograph of a prescription or a digital lab report PDF. Our Gemini 3.0 Vision Engine will structure the clinical data in milliseconds.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("### Document Source")
        
        is_pdf = uploaded_file.name.lower().endswith('.pdf')
        if is_pdf:
            import base64
            base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            image = Image.open(uploaded_file)
            st.image(image, use_column_width=True, output_format="PNG")
        
    with col2:
        st.markdown("### Processed Extraction")
        
        if "medical_context" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("Engaging Gemini Vision AI..."):
                logger.info(f"Processing document {uploaded_file.name} at {datetime.datetime.now()}")
                st.session_state.medical_context = extract_medical_info(uploaded_file, uploaded_file.name)
                st.session_state.last_uploaded = uploaded_file.name
                
        mc = st.session_state.medical_context
        
        if mc:
            st.markdown(f"""
            <div class="glass-card" style="padding: 15px; margin-bottom: 20px;">
                <h4 style="margin:0; color:#cbd5e1;">Target Patient</h4>
                <h2 style="margin:5px 0 0 0; color:#38bdf8;">{mc.patient_name}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["💊 Medications Payload", "⚠️ Safety Alerts"])
            
            with tab1:
                if mc.medications:
                    for med in mc.medications:
                        st.markdown(f"""
                        <div class="med-item">
                            <h4 style="margin:0; color:#e0f2fe;">{med.name}</h4>
                            <p style="margin:8px 0 0 0; color:#94a3b8; font-size:0.95rem;">
                                <b>Dosage:</b> <span style="color:#f8fafc;">{med.dosage}</span> &nbsp;|&nbsp; 
                                <b>Frequency:</b> <span style="color:#7dd3fc;">{med.frequency}</span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No pharmacological regimens identified.")
            
            with tab2:
                if mc.critical_alerts:
                    for alert in mc.critical_alerts:
                        st.markdown(f"""
                        <div class="alert-item">
                            <h4 style="margin:0; color:#fecaca;">CRITICAL</h4>
                            <p style="margin:5px 0 0 0; color:#f8fafc;">{alert}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("No contraindications or critical alerts detected.")
                    
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown("### ☁️ Google Cloud Integration")
            st.warning("Review the structured metrics above. Synchronization will automatically generate strict calendar events.")
            
            if st.button("🚀 Push to Google Calendar", use_container_width=True):
                with st.spinner("Synchronizing to Identity Provider..."):
                    success = sync_to_calendar(mc, st.session_state["user_creds"])
                    if success:
                        st.success("✅ Events provisioned successfully! Check your Care Plan Calendar.")
                        logger.info("Care Plan Sync Successful.")
                    else:
                        st.error("❌ Synchronization interrupted. Re-validate OAuth scopes.")
                        logger.error("Care Plan Sync Failed.")
        else:
            st.error("Extraction failed. Document topography might be unrecognizable.")
            logger.warning("Image extraction failed or returned None.")
