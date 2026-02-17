"""
Prompt templates for patient triage extraction.
Modify these templates to adjust LLM behavior without changing code.
"""

PATIENT_EXTRACTION_PROMPT = """You are a medical triage expert. Extract structured patient information from the natural language description below.

IMPORTANT: Output ONLY valid JSON matching the exact schema provided. Do not include any explanatory text before or after the JSON.

Patient Description:
{description}

Output a JSON object with the following structure:
{{
  "patient_id": "string (generate if not provided)",
  "name": "string (use 'Unknown' if not provided)",
  "age": number (estimate if not exact),
  "gender": "Male" | "Female" | "Unknown",
  "vital_signs": {{
    "heart_rate": number or null,
    "blood_pressure": {{
      "systolic": number or null,
      "diastolic": number or null
    }},
    "respiratory_rate": number or null,
    "oxygen_saturation": number or null,
    "temperature": number or null
  }},
  "consciousness": {{
    "eye_response": number (1-4) or null,
    "verbal_response": number (1-5) or null,
    "motor_response": number (1-6) or null,
    "total_score": number (3-15) or null
  }},
  "acuity": "Deceased" | "Minor" | "Severe" | "Critical" | "Undefined",
  "injuries": [
    {{
      "locations": ["Head" | "Neck" | "Chest" | "Back" | "Pelvis" | "Abdomen" | "Limbs (Upper)" | "Limbs (Lower)"],
      "mechanisms": ["Blunt" | "Penetrating" | "Thermal" | "Blast" | "Drowning" | "Chemical" | "Radiation" | "Electrical" | "Hypothermia" | "Other"],
      "severity": "Deceased" | "Minor" | "Severe" | "Critical",
      "description": "string"
    }}
  ],
  "required_medical_capabilities": {{
    "trauma_center": boolean,
    "neurosurgical": boolean,
    "orthopedic": boolean,
    "ophthalmology": boolean,
    "burn": boolean,
    "pediatric": boolean,
    "obstetric": boolean,
    "cardiac": boolean,
    "thoracic": boolean,
    "vascular": boolean,
    "ent": boolean,
    "hepatobiliary": boolean
  }},
  "required_medical_resources": {{
    "ward": number,
    "ordinary_icu": number,
    "operating_room": number,
    "ventilator": number,
    "prbc_unit": number,
    "isolation": number,
    "decontamination_unit": number,
    "ct_scanner": number,
    "oxygen_cylinder": number,
    "interventional_radiology": number
  }},
  "description": "string (original or summarized description)",
  "predicted_death_timestamp": number (unix timestamp, 0 if not applicable),
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": ["string"],
  "deceased": boolean,
  "location": {{
    "latitude": number,
    "longitude": number
  }}
}}

Guidelines:
- Use medical knowledge to infer required capabilities from injuries
- Estimate resource needs based on injury severity
- Calculate Glasgow Coma Scale if consciousness level is described
- Determine acuity using START triage principles (Critical: immediate life threat, Severe: urgent care needed, Minor: can wait)
- Set deceased=true only if explicitly stated or incompatible with life
- Use null for unknown vital signs rather than guessing
- Generate reasonable patient_id if not provided (e.g., "P-001")
- Set predicted_death_timestamp to 0 if patient is stable or minor

Output JSON:"""


FEW_SHOT_EXAMPLES = """
Example 1:
Input: "35-year-old female, car accident, complaining of severe chest pain, HR 120, BP 85/50, RR 28, SpO2 88%, GCS 14 (E4V4M6), suspected pneumothorax"

Output:
{{
  "patient_id": "P-001",
  "name": "Unknown",
  "age": 35,
  "gender": "Female",
  "vital_signs": {{
    "heart_rate": 120,
    "blood_pressure": {{"systolic": 85, "diastolic": 50}},
    "respiratory_rate": 28,
    "oxygen_saturation": 88,
    "temperature": null
  }},
  "consciousness": {{
    "eye_response": 4,
    "verbal_response": 4,
    "motor_response": 6,
    "total_score": 14
  }},
  "acuity": "Critical",
  "injuries": [
    {{
      "locations": ["Chest"],
      "mechanisms": ["Blunt"],
      "severity": "Critical",
      "description": "Suspected pneumothorax with respiratory distress"
    }}
  ],
  "required_medical_capabilities": {{
    "trauma_center": true,
    "neurosurgical": false,
    "orthopedic": false,
    "ophthalmology": false,
    "burn": false,
    "pediatric": false,
    "obstetric": false,
    "cardiac": true,
    "thoracic": true,
    "vascular": false,
    "ent": false,
    "hepatobiliary": false
  }},
  "required_medical_resources": {{
    "ward": 0,
    "ordinary_icu": 1,
    "operating_room": 1,
    "ventilator": 1,
    "prbc_unit": 2,
    "isolation": 0,
    "decontamination_unit": 0,
    "ct_scanner": 1,
    "oxygen_cylinder": 2,
    "interventional_radiology": 0
  }},
  "description": "35-year-old female, car accident, complaining of severe chest pain, HR 120, BP 85/50, RR 28, SpO2 88%, GCS 14 (E4V4M6), suspected pneumothorax",
  "predicted_death_timestamp": 0,
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": [],
  "deceased": false,
  "location": {{"latitude": 0.0, "longitude": 0.0}}
}}

---

Now process the following patient:
"""
