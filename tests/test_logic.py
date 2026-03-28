import unittest
from core.ai_engine import MedicalContext

class TestMediBridge(unittest.TestCase):
    def test_json_structure(self):
        # Mock test to show integration flow and structure mapping
        sample_output = {
            "patient_name": "John Doe",
            "medications": [{"name": "Test Medicine", "dosage": "500mg", "frequency": "Daily"}],
            "critical_alerts": []
        }
        
        context = MedicalContext(**sample_output)
        self.assertEqual(context.patient_name, "John Doe")
        self.assertEqual(context.medications[0].name, "Test Medicine")
        self.assertEqual(context.medications[0].dosage, "500mg")

if __name__ == '__main__':
    unittest.main()
