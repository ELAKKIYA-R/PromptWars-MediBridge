import datetime
import os.path
import base64
import tempfile
import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional, Any
from .ai_engine import MedicalContext

logger = logging.getLogger('medibridge_app.actions')

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.events", "openid", "https://www.googleapis.com/auth/userinfo.email"]

def get_oauth_flow(redirect_uri: str) -> Optional[Flow]:
    """
    Constructs a Google OAuth Flow object from credentials.json
    (or via GOOGLE_CREDENTIALS_JSON_BASE64 env var).
    """
    creds_path = "credentials.json"
    temp_path = None
    
    if not os.path.exists(creds_path):
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON_BASE64")
        if creds_json:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
                tf.write(base64.b64decode(creds_json).decode("utf-8"))
                temp_path = tf.name
            creds_path = temp_path
        else:
            logger.error("credentials.json not found and GOOGLE_CREDENTIALS_JSON_BASE64 not set.")
            return None
            
    try:
        flow = Flow.from_client_secrets_file(
            creds_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        if temp_path:
            os.remove(temp_path)
        return flow
    except Exception as e:
        logger.error(f"Failed to build OAuth Flow: {e}")
        if temp_path:
            os.remove(temp_path)
        return None

def get_calendar_service(creds_dict: dict) -> Optional[Any]:
    """
    Initializes and returns the Google Calendar API v3 service using Streamlit session credentials.
    """
    if not creds_dict:
        return None
        
    try:
        creds = Credentials(**creds_dict)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        logger.error(f"An error occurred building calendar service: {error}")
        return None
    except Exception as e:
        logger.error(f"Failed to authenticate calendar service: {e}")
        return None

def calculate_recurrence(frequency: str) -> str:
    """Basic heuristic to map text frequency to RRULE """
    freq_lower = frequency.lower()
    if 'daily' in freq_lower or 'day' in freq_lower or '24 hours' in freq_lower:
        return 'RRULE:FREQ=DAILY;COUNT=14' # 2 weeks by default
    elif 'week' in freq_lower:
        return 'RRULE:FREQ=WEEKLY;COUNT=4' # 4 weeks by default
    elif 'twice' in freq_lower or 'two times' in freq_lower or 'b.i.d' in freq_lower or 'bid' in freq_lower:
        return 'RRULE:FREQ=DAILY;COUNT=14' # Simplifying bid
    return 'RRULE:FREQ=DAILY;COUNT=7' # Default 7 days

def sync_to_calendar(medical_context: MedicalContext, creds_dict: dict) -> bool:
    """Syncs the extracted medical context to Google Calendar as events."""
    service = get_calendar_service(creds_dict)
    if not service:
        logger.error("No valid calendar service available for sync.")
        return False
        
    try:
        # Start tomorrow morning at 9am
        start_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        for med in medical_context.medications:
            event = {
              'summary': f'Take Medication: {med.name}',
              'location': 'Home',
              'description': f'Dosage: {med.dosage}\\nFrequency: {med.frequency}\\nPatient: {medical_context.patient_name}',
              'start': {
                'dateTime': start_date.isoformat(),
                'timeZone': 'UTC',
              },
              'end': {
                'dateTime': (start_date + datetime.timedelta(minutes=30)).isoformat(),
                'timeZone': 'UTC',
              },
              'recurrence': [
                calculate_recurrence(med.frequency)
              ],
              'reminders': {
                'useDefault': False,
                'overrides': [
                  {'method': 'popup', 'minutes': 10},
                ],
              },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            
        return True
    except Exception as e:
        logger.error(f"Failed to create events: {e}")
        return False
