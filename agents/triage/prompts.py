"""
Prompt templates for patient triage extraction using SALT protocol.
Modify these templates to adjust LLM behavior without changing code.
"""

PATIENT_EXTRACTION_PROMPT = """You are a medical triage expert trained in the SALT (Sort, Assess, Lifesaving Interventions, Treatment/Transport) mass casualty triage protocol.

IMPORTANT:
- Output ONLY valid JSON matching the exact schema provided.
- Do not include any explanatory text before or after the JSON.
- Use null for any field where information is not provided or you are uncertain.
- Only include values you are confident about based on the description.
- Do not generate patient_id - leave it as null (it will be auto-generated).

## SALT Triage Protocol

### 1. SORT (Global Sorting)
- **Walkers (Green)**: Can walk when asked → Likely minimal injuries
- **Wavers (Yellow)**: Can wave but cannot walk → Likely delayed priority
- **Still (Red/Black)**: Cannot move or wave → Assess first for immediate/dead

### 2. ASSESS (Individual Assessment)
Ask these yes/no questions:
- Does the patient have a peripheral pulse?
- Are they in respiratory distress?
- Is hemorrhage controlled?
- Do they follow commands or make purposeful movements?

### 3. LIFESAVING INTERVENTIONS (LSI)
Note any rapid interventions performed:
- Tourniquet/hemorrhage control
- Airway opening
- Chest decompression
- Auto-injector antidotes

### 4. TREATMENT/TRANSPORT (Categorization)
Assign SALT category:
- **Dead**: Not breathing even after opening airway
- **Expectant**: Breathing but unlikely to survive given resource constraints
- **Immediate**: Fails ≥1 assessment question but likely to survive with immediate care
- **Delayed**: Passes all assessment questions but has serious injuries
- **Minimal**: Passes all assessment questions, minor injuries only

Patient Description:
{description}

Output a JSON object with the following structure:
{{
  "patient_id": null,
  "name": "string (use 'Unknown' if not provided)",
  "age": number or null,
  "gender": "Male" | "Female" | "Unknown" | null,
  "salt_assessment": {{
    "can_walk": boolean or null,
    "can_wave": boolean or null,
    "obeys_commands": boolean or null,
    "has_peripheral_pulse": boolean or null,
    "in_respiratory_distress": boolean or null,
    "hemorrhage_controlled": boolean or null,
    "lifesaving_intervention_performed": "string describing LSI" or null
  }} or null,
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
  "acuity": "Dead" | "Expectant" | "Immediate" | "Delayed" | "Minimal" | "Undefined" | null,
  "injuries": [
    {{
      "locations": ["Head" | "Neck" | "Chest" | "Back" | "Pelvis" | "Abdomen" | "Limbs (Upper)" | "Limbs (Lower)"],
      "mechanisms": ["Blunt" | "Penetrating" | "Thermal" | "Blast" | "Drowning" | "Chemical" | "Radiation" | "Electrical" | "Hypothermia" | "Other"],
      "severity": "Dead" | "Expectant" | "Immediate" | "Delayed" | "Minimal",
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

Guidelines for SALT Triage:
- **Sort Phase**: Determine if patient can walk, wave, or is still
- **Assess Phase**: Evaluate pulse, respiratory distress, hemorrhage control, command following
- **LSI Phase**: Note any lifesaving interventions performed
- **Categorize**:
  - Dead if not breathing after airway opening
  - Expectant if breathing but expectant (resource-limited survival)
  - Immediate if fails any assessment but salvageable
  - Delayed if passes all assessments but has serious injuries
  - Minimal if passes all assessments with minor injuries only
- Use null for any field where information is not provided or uncertain
- Always set patient_id to null (will be auto-generated as UUID)
- Set deceased=true only for Dead category
- Set predicted_death_timestamp based on category (Expectant/Immediate get timestamps, others null)

Output JSON:"""


FEW_SHOT_EXAMPLES = """
Example 1 - IMMEDIATE:
Input: "35-year-old female, car accident, severe chest pain, no radial pulse, gasping for air, bleeding controlled with tourniquet, GCS 14"

Output:
{{
  "patient_id": null,
  "name": "Unknown",
  "age": 35,
  "gender": "Female",
  "salt_assessment": {{
    "can_walk": false,
    "can_wave": false,
    "obeys_commands": true,
    "has_peripheral_pulse": false,
    "in_respiratory_distress": true,
    "hemorrhage_controlled": true,
    "lifesaving_intervention_performed": "Tourniquet applied to control hemorrhage"
  }},
  "vital_signs": null,
  "consciousness": {{
    "eye_response": 4,
    "verbal_response": 4,
    "motor_response": 6,
    "total_score": 14
  }},
  "acuity": "Immediate",
  "injuries": [
    {{
      "locations": ["Chest"],
      "mechanisms": ["Blunt"],
      "severity": "Immediate",
      "description": "Severe chest trauma with respiratory distress and absent peripheral pulse"
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
    "vascular": true,
    "ent": false,
    "hepatobiliary": false
  }},
  "required_medical_resources": {{
    "ward": 0,
    "ordinary_icu": 1,
    "operating_room": 1,
    "ventilator": 1,
    "prbc_unit": 4,
    "isolation": 0,
    "decontamination_unit": 0,
    "ct_scanner": 1,
    "oxygen_cylinder": 2,
    "interventional_radiology": 0
  }},
  "description": "35-year-old female, car accident, severe chest pain, no radial pulse, gasping for air, bleeding controlled with tourniquet, GCS 14",
  "predicted_death_timestamp": null,
  "status": "Unassigned",
  "assigned_facility": null,
  "action_logs": [],
  "deceased": false,
  "location": null
}}

Example 2 - MINIMAL:
Input: "28-year-old female, broken arm from fall, walking and talking normally, good pulse"

Output:
{{
  "patient_id": null,
  "name": "Unknown",
  "age": 28,
  "gender": "Female",
  "salt_assessment": {{
    "can_walk": true,
    "can_wave": true,
    "obeys_commands": true,
    "has_peripheral_pulse": true,
    "in_respiratory_distress": false,
    "hemorrhage_controlled": true,
    "lifesaving_intervention_performed": null
  }},
  "vital_signs": null,
  "consciousness": null,
  "acuity": "Minimal",
  "injuries": [
    {{
      "locations": ["Limbs (Upper)"],
      "mechanisms": ["Blunt"],
      "severity": "Minimal",
      "description": "Suspected arm fracture"
    }}
  ],
  "required_medical_capabilities": {{
    "trauma_center": false,
    "neurosurgical": false,
    "orthopedic": true,
    "ophthalmology": false,
    "burn": false,
    "pediatric": false,
    "obstetric": false,
    "cardiac": false,
    "thoracic": false,
    "vascular": false,
    "ent": false,
    "hepatobiliary": false
  }},
  "required_medical_resources": {{
    "ward": 1,
    "ordinary_icu": 0,
    "operating_room": 0,
    "ventilator": 0,
    "prbc_unit": 0,
    "isolation": 0,
    "decontamination_unit": 0,
    "ct_scanner": 0,
    "oxygen_cylinder": 0,
    "interventional_radiology": 0
  }},
  "description": "28-year-old female, broken arm from fall, walking and talking normally, good pulse",
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
