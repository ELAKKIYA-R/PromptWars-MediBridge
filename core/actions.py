import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .ai_engine import MedicalContext

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_calendar_service():
    """Shows basic usage of the Google Calendar API."""
    creds = None
    # Check for token from environment first (for Cloud Run/Headless)
    token_json_base64 = os.environ.get("GOOGLE_TOKEN_JSON_BASE64")
    if token_json_base64:
        import base64
        import json
        token_data = json.loads(base64.b64decode(token_json_base64).decode("utf-8"))
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            import base64
            import tempfile
            
            if os.path.exists("credentials.json"):
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            else:
                creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON_BASE64")
                if creds_json:
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
                        tf.write(base64.b64decode(creds_json).decode("utf-8"))
                        temp_path = tf.name
                    flow = InstalledAppFlow.from_client_secrets_file(temp_path, SCOPES)
                    # Note: remove temp_path after use if needed, but InstalledAppFlow might need it during flow
                else:
                    print("credentials.json not found and GOOGLE_CREDENTIALS_JSON_BASE64 not set.")
                    return None
            
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
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

def sync_to_calendar(medical_context: MedicalContext) -> bool:
    """Syncs the extracted medical context to Google Calendar as events."""
    service = get_calendar_service()
    if not service:
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
            print(f"Event created: {event.get('htmlLink')}")
            
        return True
    except Exception as e:
        print(f"Failed to create events: {e}")
        return False
