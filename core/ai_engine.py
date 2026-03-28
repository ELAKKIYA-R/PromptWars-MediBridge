import os
import google.genai as genai
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import json
import logging

logger = logging.getLogger('medibridge_app.ai_engine')

class Medication(BaseModel):
    name: str = Field(description="Name of the medication")
    dosage: str = Field(description="Dosage of the medication")
    frequency: str = Field(description="Frequency of taking the medication")

class MedicalContext(BaseModel):
    patient_name: str = Field(description="Name of the patient")
    medications: List[Medication] = Field(description="List of medications prescribed")
    critical_alerts: List[str] = Field(description="Critical Alerts like Allergies or Warnings")

def extract_medical_info(image: Any) -> Optional[MedicalContext]:
    """
    Extracts medical information from a PIL Image using Gemini 3 Flash Preview.
    Uses the modern google-genai SDK.
    
    Args:
        image: PIL Image object containing the medical document.
        
    Returns:
        Optional[MedicalContext]: A validated Pydantic model containing the extracted data, 
                                 or None if extraction fails.
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
            logger.info("Attempting extraction with primary model: gemini-3-flash-preview")
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
            logger.warning(f"Primary model (gemini-3-flash-preview) failed: {e}. Falling back to gemini-2.5-flash...")
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
        logger.error(f"Error extracting medical info: {e}", exc_info=True)
        return None
