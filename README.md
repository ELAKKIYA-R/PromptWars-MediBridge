# MediBridge

MediBridge is a Streamlit application designed to process uploaded images of medical prescriptions or lab reports using Google's Gemini 1.5 Flash vision capabilities.

The app extracts key information, structured logically, and seamlessly integrates with the Google Calendar API to sync medication schedules to a Care Plan.

## Features
- **AI Extraction**: Upload prescription images and extract Patient Name, Medications (with Dosage and Frequency), and Critical Alerts, explicitly looking for contraindications.
- **Structured Data**: Leverages Pydantic and native Gemini response schemas for rigid LLM output parsing (JSON schema).
- **Care Plan Sync**: Includes a logic gate to review accuracy before automatically creating recurring events in Google Calendar for medications.
- **Clean Architecture**: Separates UI (Streamlit) from AI Logic (Gemini) and Actions (Google Services).
- **Security**: All API keys are managed via environment variables. User data is processed in-memory and not persisted to disk to ensure HIPAA-aligned privacy standards.
- **Infrastructure**: Uses GCP's global infrastructure and Cloud Logging approaches to provide low-latency inference and broad adoption support.

## Setup instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Keys**:
   - Set the `GEMINI_API_KEY` environment variable.
   - Obtain Google Calendar API `credentials.json` (Desktop App OAuth Client) from Google Cloud Console and place it in the project root.

## Cloud Run Deployment

To deploy to Google Cloud Run:

1. **Build and Push the Image**:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/medibridge
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy medibridge \
     --image gcr.io/YOUR_PROJECT_ID/medibridge \
     --platform managed \
     --region YOUR_REGION \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_key_here \
     --set-env-vars GOOGLE_CREDENTIALS_JSON_BASE64=$(base64 -i credentials.json)
   ```

> [!NOTE]
> For the Google Calendar integration to work in a headless environment (like Cloud Run), you should ideally pre-authorize locally to generate `token.json`, and then provide its content as an environment variable or via Secret Manager, as `InstalledAppFlow` requires user interaction.