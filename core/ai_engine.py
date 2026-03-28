import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
import json

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

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
    Extracts medical information from an image using Gemini 1.5 Flash.
    Returns a structured MedicalContext object or None if extraction fails.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Analyze this medical prescription or lab report.
        Extract the Patient Name, Medications (including Dosage and Frequency), and Critical Alerts (Allergies/Warnings).
        If the image is too blurry to read with high confidence, return an empty medications list and add "Image too blurry" to critical alerts.
        Return the result strictly as a JSON object matching this schema without any extra text or markdown formatting:
        {
            "patient_name": "string",
            "medications": [
                {
                    "name": "string",
                    "dosage": "string",
                    "frequency": "string"
                }
            ],
            "critical_alerts": ["string"]
        }
        """
        
        response = model.generate_content([prompt, image])
        
        # Parse output as JSON
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        return MedicalContext(**data)
        
    except Exception as e:
        print(f"Error extracting info: {e}")
        return None
