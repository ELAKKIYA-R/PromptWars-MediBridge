# MediBridge

MediBridge is a Streamlit application designed to process uploaded images of medical prescriptions or lab reports using Google's Gemini 1.5 Flash vision capabilities.

The app extracts key information, structured logically, and seamlessly integrates with the Google Calendar API to sync medication schedules to a Care Plan.

## Features
- **AI Extraction**: Upload prescription images and extract Patient Name, Medications (with Dosage and Frequency), and Critical Alerts.
- **Structured Data**: Leverages Pydantic for rigid LLM output parsing (JSON schema).
- **Care Plan Sync**: Automatically creates recurring events in Google Calendar for medications.
- **Clean Architecture**: Separates UI (Streamlit) from AI Logic (Gemini) and Actions (Google Services).
- **Error Handling**: Basic handling for blurred images or failed extraction.

## Setup instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Keys**:
   - Set the `GEMINI_API_KEY` environment variable.
   - Obtain Google Calendar API `credentials.json` (Desktop App OAuth Client) from Google Cloud Console and place it in the project root.

3. **Run the app**:
   ```bash
   streamlit run main.py
   ```