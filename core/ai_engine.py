import os
import google.genai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
import json

class Medication(BaseModel):
    name: str = Field(description="Name of the medication")
    dosage: str = Field(description="Dosage of the medication")
    frequency: str = Field(description="Frequency of taking the medication")

class MedicalContext(BaseModel):
    patient_name: str = Field(description="Name of the patient")
    medications: List[Medication] = Field(description="List of medications prescribed")
    critical_alerts: List[str] = Field(description="Critical Alerts like Allergies or Warnings")

def extract_medical_info(image) -> Optional[MedicalContext]:
    """
    Extracts medical information from an image using Gemini 3 Flash Preview.
    Uses the modern google-genai SDK.
    """
    try:
        # Efficiency improvement: Resize image
        img = image.copy()
        img.thumbnail((1024, 1024))
        
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        
        prompt = """
        Analyze this medical prescription or lab report.
        Extract the Patient Name, Medications (including Dosage and Frequency), and Critical Alerts (Allergies/Warnings/Contraindications).
        Pay special attention to contraindications (e.g., "Warning: This patient is allergic to Penicillin, and this prescription contains Amoxicillin").
        If the image is too blurry to read with high confidence, return an empty medications list and add "Image too blurry" to critical alerts.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=[prompt, img],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': MedicalContext,
                }
            )
            return response.parsed
        except Exception as e:
            print(f"DEBUG: Primary model (gemini-3-flash-preview) failed: {e}. Falling back to gemini-2.5-flash...")
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, img],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': MedicalContext,
                }
            )
            return response.parsed
        
    except Exception as e:
        import datetime
        print(f"DEBUG: Error extracting medical info at {datetime.datetime.now()}: {e}")
        return None
