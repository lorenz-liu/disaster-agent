"""
Patient Triage Agent - Test Cases
"""

import json
from agents.triage import PatientTriageAgent


def test_minimal_description():
    """Test Case 1: Minimal information - name, age, gender, brief condition."""
    print("=" * 80)
    print("TEST CASE 1: Minimal Description")
    print("=" * 80)

    description = "Sarah Johnson, 28 years old, female, broken arm from a fall"

    agent = PatientTriageAgent(model_path="/models/gpt-oss-20b")
    patient = agent.triage_patient(description, validate=True, verbose=True)

    if patient:
        print("\n✓ Test Case 1 PASSED")
        with open("test1_minimal.json", "w") as f:
            json.dump(patient.model_dump(), f, indent=2)
    else:
        print("\n✗ Test Case 1 FAILED")

    agent.unload_model()
    return patient


def test_moderate_description():
    """Test Case 2: Moderate detail - includes vital signs and injury details."""
    print("\n\n" + "=" * 80)
    print("TEST CASE 2: Moderate Description")
    print("=" * 80)

    description = """
    Michael Chen, 52-year-old male, motorcycle accident.
    Complaining of chest and leg pain.
    Heart rate 105, blood pressure 110/70, breathing rate 20, oxygen level 95%.
    Alert and responsive. Suspected rib fractures and possible tibia fracture.
    """

    agent = PatientTriageAgent(model_path="/models/gpt-oss-20b")
    patient = agent.triage_patient(description, validate=True, verbose=True)

    if patient:
        print("\n✓ Test Case 2 PASSED")
        with open("test2_moderate.json", "w") as f:
            json.dump(patient.model_dump(), f, indent=2)
    else:
        print("\n✗ Test Case 2 FAILED")

    agent.unload_model()
    return patient


def test_detailed_description():
    """Test Case 3: Comprehensive detail - full medical assessment."""
    print("\n\n" + "=" * 80)
    print("TEST CASE 3: Detailed Description")
    print("=" * 80)

    description = """
    Patient ID: P-2024-001
    Name: Jennifer Martinez
    Age: 45 years old
    Gender: Female

    Incident: Motor vehicle collision at intersection of Highway 401 and Don Valley Parkway
    Location: 43.7315°N, 79.3466°W

    Chief Complaint: Severe chest and abdominal pain, difficulty breathing

    Vital Signs:
    - Heart Rate: 118 bpm (tachycardia)
    - Blood Pressure: 88/55 mmHg (hypotensive)
    - Respiratory Rate: 26 breaths/min (tachypneic)
    - Oxygen Saturation: 89% on room air
    - Temperature: 36.5°C

    Neurological Assessment:
    - Glasgow Coma Scale: 14 (E4 V4 M6)
    - Patient is alert but anxious and in significant distress

    Physical Examination:
    - Multiple rib fractures on left side (ribs 4-7)
    - Suspected hemopneumothorax
    - Abdominal tenderness and guarding, possible splenic injury
    - Seat belt sign across chest and abdomen
    - No obvious head or spinal injuries
    - Extremities intact, no obvious fractures

    Injury Mechanism: Blunt force trauma from high-speed T-bone collision

    Assessment: Critical polytrauma patient requiring immediate trauma center care

    Required Interventions:
    - Immediate chest tube placement
    - Possible emergency surgery for intra-abdominal bleeding
    - Blood transfusion likely needed
    - ICU admission
    - CT scan of chest and abdomen

    Triage Category: RED - Immediate

    Action Log:
    - 14:23 - Patient extricated from vehicle by fire rescue
    - 14:28 - Initial assessment by paramedics on scene
    - 14:30 - IV access established, oxygen therapy initiated
    - 14:35 - Patient loaded into ambulance
    """

    agent = PatientTriageAgent(model_path="/models/gpt-oss-20b")
    patient = agent.triage_patient(description, validate=True, verbose=True)

    if patient:
        print("\n✓ Test Case 3 PASSED")
        with open("test3_detailed.json", "w") as f:
            json.dump(patient.model_dump(), f, indent=2)
    else:
        print("\n✗ Test Case 3 FAILED")

    agent.unload_model()
    return patient


def main():
    """Run all test cases."""
    print("\n" + "=" * 80)
    print("PATIENT TRIAGE AGENT - TEST SUITE")
    print("=" * 80)
    print("\nTesting with three levels of description complexity:\n")
    print("1. Minimal: Basic demographics + brief condition")
    print("2. Moderate: Demographics + vital signs + injury details")
    print("3. Detailed: Complete medical assessment with full context")
    print("\n" + "=" * 80 + "\n")

    results = []

    # Run tests
    results.append(("Minimal", test_minimal_description()))
    results.append(("Moderate", test_moderate_description()))
    results.append(("Detailed", test_detailed_description()))

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:12} - {status}")

    passed = sum(1 for _, r in results if r is not None)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80)


if __name__ == "__main__":
    main()
