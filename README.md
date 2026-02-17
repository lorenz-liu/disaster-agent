# Disaster Agent Schemas

Pydantic data schemas for disaster management simulation system.

## Schemas

- **PatientType**: Patient information including vital signs, injuries, and status
- **HealthcareFacilityType**: Healthcare facility with resources, capabilities, and location
- **Enums**: All enumeration types used across schemas
- **Types**: Reusable common types like LocationType

## Usage

```python
from schemas import PatientType, HealthcareFacilityType

# Create a patient instance
patient = PatientType(**patient_data)

# Create a facility instance
facility = HealthcareFacilityType(**facility_data)
```

## Example Data

### Patient Example

```json
{
  "patient_id": "P-001",
  "name": "John Doe",
  "age": 45,
  "gender": "Male",
  "vital_signs": {
    "heart_rate": 110,
    "blood_pressure": {
      "systolic": 90,
      "diastolic": 60
    },
    "respiratory_rate": 22,
    "oxygen_saturation": 92,
    "temperature": 36.8
  },
  "consciousness": {
    "eye_response": 4,
    "verbal_response": 5,
    "motor_response": 6,
    "total_score": 15
  },
  "acuity": "Severe",
  "injuries": [
    {
      "locations": ["Chest", "Abdomen"],
      "mechanisms": ["Blunt", "Penetrating"],
      "severity": "Severe",
      "description": "Multiple rib fractures with suspected internal bleeding"
    }
  ],
  "required_medical_capabilities": {
    "trauma_center": true,
    "neurosurgical": false,
    "orthopedic": true,
    "ophthalmology": false,
    "burn": false,
    "pediatric": false,
    "obstetric": false,
    "cardiac": true,
    "thoracic": true,
    "vascular": true,
    "ent": false,
    "hepatobiliary": false
  },
  "required_medical_resources": {
    "ward": 1,
    "ordinary_icu": 1,
    "operating_room": 1,
    "ventilator": 1,
    "prbc_unit": 4,
    "isolation": 0,
    "decontamination_unit": 0,
    "ct_scanner": 1,
    "oxygen_cylinder": 2,
    "interventional_radiology": 0
  },
  "description": "45-year-old male involved in motor vehicle collision, presenting with chest and abdominal trauma",
  "predicted_death_timestamp": 1708185600,
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": [
    "Patient triaged at scene - 14:30",
    "Vital signs assessed - 14:35"
  ],
  "deceased": false,
  "location": {
    "latitude": 43.6532,
    "longitude": -79.3832
  }
}
```

### Healthcare Facility Example

```json
{
  "facility_id": "F-001",
  "name": "Toronto General Hospital",
  "level": 1,
  "medical_resources": {
    "ward": 50,
    "ordinary_icu": 20,
    "operating_room": 8,
    "ventilator": 25,
    "prbc_unit": 100,
    "isolation": 10,
    "decontamination_unit": 2,
    "ct_scanner": 3,
    "oxygen_cylinder": 50,
    "interventional_radiology": 2
  },
  "capabilities": {
    "trauma_center": true,
    "neurosurgical": true,
    "orthopedic": true,
    "ophthalmology": true,
    "burn": true,
    "pediatric": true,
    "obstetric": true,
    "cardiac": true,
    "thoracic": true,
    "vascular": true,
    "ent": true,
    "hepatobiliary": true
  },
  "vehicle_resources": {
    "ambulances": 12,
    "helicopters": 2
  },
  "location": {
    "latitude": 43.6591,
    "longitude": -79.3877
  },
  "accepted_patients": ["P-003", "P-007", "P-012"]
}
```

## Enums

### Patient Severity
- `Deceased` 
- `Minor`
- `Severe`
- `Critical`
- `Undefined`

### Patient Status
- `Unassigned`
- `Awaiting Transfer`
- `In-Transfer`
- `Arrived`

### Healthcare Facility Level
- `1` - Level 1 Trauma Center (highest capability)
- `2` - Level 2 Trauma Center
- `3` - Level 3 Trauma Center

### Gender
- `Male`
- `Female`
- `Unknown`

### Injury Mechanisms
- `Blunt`
- `Penetrating`
- `Thermal`
- `Blast`
- `Drowning`
- `Chemical`
- `Radiation`
- `Electrical`
- `Hypothermia`
- `Other`

### Injury Locations
- `Head`
- `Neck`
- `Chest`
- `Back`
- `Pelvis`
- `Abdomen`
- `Limbs (Upper)`
- `Limbs (Lower)`
