import unittest
from core.ai_engine import MedicalContext, Medication

class TestMediBridge(unittest.TestCase):
    def test_json_structure_success(self):
        """Test ideal scenario structural mapping"""
        sample_output = {
            "patient_name": "John Doe",
            "medications": [{"name": "Test Medicine", "dosage": "500mg", "frequency": "Daily"}],
            "critical_alerts": []
        }
        
        context = MedicalContext(**sample_output)
        self.assertEqual(context.patient_name, "John Doe")
        self.assertEqual(context.medications[0].name, "Test Medicine")
        self.assertEqual(context.medications[0].dosage, "500mg")
        
    def test_json_structure_missing_medications(self):
        """Test edge case where medications are missing (e.g. blurred image)"""
        sample_output = {
            "patient_name": "Unknown",
            "medications": [],
            "critical_alerts": ["Image too blurry to read"]
        }
        context = MedicalContext(**sample_output)
        self.assertEqual(len(context.medications), 0)
        self.assertIn("Image too blurry to read", context.critical_alerts[0])

    def test_json_structure_contraindications(self):
        """Test integration of the contraindication logic gate"""
        sample_output = {
            "patient_name": "Jane Smith",
            "medications": [{"name": "Amoxicillin", "dosage": "250mg", "frequency": "b.i.d"}],
            "critical_alerts": ["Warning: Patient is allergic to Penicillin"]
        }
        context = MedicalContext(**sample_output)
        self.assertEqual(len(context.critical_alerts), 1)
        self.assertEqual(context.critical_alerts[0], "Warning: Patient is allergic to Penicillin")

if __name__ == '__main__':
    unittest.main()
