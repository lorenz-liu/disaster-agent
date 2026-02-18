"""
Prompt templates for patient triage extraction.
Modify these templates to adjust LLM behavior without changing code.
"""

PATIENT_EXTRACTION_PROMPT = """You are a medical triage expert. Extract structured patient information from the natural language description below.

IMPORTANT:
- Output ONLY valid JSON matching the exact schema provided.
- Do not include any explanatory text before or after the JSON.
- Use null for any field where information is not provided or you are uncertain.
- Only include values you are confident about based on the description.

Patient Description:
{description}

Output a JSON object with the following structure:
{{
  "patient_id": "string (generate if not provided, e.g., 'P-001')",
  "name": "string (use 'Unknown' if not provided)",
  "age": number or null,
  "gender": "Male" | "Female" | "Unknown" | null,
  "vital_signs": {{
    "heart_rate": number or null,
    "blood_pressure": {{
      "systolic": number or null,
      "diastolic": number or null
    }},
    "respiratory_rate": number or null,
    "oxygen_saturation": number or null,
    "temperature": number or null
  }} or null,
  "consciousness": {{
    "eye_response": number (1-4) or null,
    "verbal_response": number (1-5) or null,
    "motor_response": number (1-6) or null,
    "total_score": number (3-15) or null
  }} or null,
  "acuity": "Deceased" | "Minor" | "Severe" | "Critical" | "Undefined" | null,
  "injuries": [
    {{
      "locations": ["Head" | "Neck" | "Chest" | "Back" | "Pelvis" | "Abdomen" | "Limbs (Upper)" | "Limbs (Lower)"],
      "mechanisms": ["Blunt" | "Penetrating" | "Thermal" | "Blast" | "Drowning" | "Chemical" | "Radiation" | "Electrical" | "Hypothermia" | "Other"],
      "severity": "Deceased" | "Minor" | "Severe" | "Critical",
      "description": "string"
    }}
  ] or null,
  "required_medical_capabilities": {{
    "trauma_center": boolean or null,
    "neurosurgical": boolean or null,
    "orthopedic": boolean or null,
    "ophthalmology": boolean or null,
    "burn": boolean or null,
    "pediatric": boolean or null,
    "obstetric": boolean or null,
    "cardiac": boolean or null,
    "thoracic": boolean or null,
    "vascular": boolean or null,
    "ent": boolean or null,
    "hepatobiliary": boolean or null
  }} or null,
  "required_medical_resources": {{
    "ward": number or null,
    "ordinary_icu": number or null,
    "operating_room": number or null,
    "ventilator": number or null,
    "prbc_unit": number or null,
    "isolation": number or null,
    "decontamination_unit": number or null,
    "ct_scanner": number or null,
    "oxygen_cylinder": number or null,
    "interventional_radiology": number or null
  }} or null,
  "description": "string (original or summarized description)",
  "predicted_death_timestamp": number (unix timestamp) or null,
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": ["string"] or [],
  "deceased": boolean or null,
  "location": {{
    "latitude": number or null,
    "longitude": number or null
  }} or null
}}

Guidelines:
- Use medical knowledge to infer required capabilities from injuries ONLY if confident
- Estimate resource needs based on injury severity ONLY if confident
- Calculate Glasgow Coma Scale if consciousness level is described
- Determine acuity using START triage principles ONLY if enough information is provided
- Set deceased=true only if explicitly stated or incompatible with life
- Use null for any field where information is not provided or uncertain
- Generate reasonable patient_id if not provided (e.g., "P-001")
- Set predicted_death_timestamp to null if not enough information to predict

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
  "predicted_death_timestamp": null,
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": [],
  "deceased": false,
  "location": null
}}

---

Now process the following patient:
"""
