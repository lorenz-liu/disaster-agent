"""
Prompt templates for patient triage extraction using SALT protocol.
Modify these templates to adjust LLM behavior without changing code.
"""

PATIENT_EXTRACTION_PROMPT_COT = """You are a medical triage expert trained in the SALT (Sort, Assess, Lifesaving Interventions, Treatment/Transport) mass casualty triage protocol.

Your task is to analyze the patient description and extract structured data.

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

## Instructions

IMPORTANT: You MUST follow this two-step process:

**Step 1: Think through the SALT protocol inside <thinking> tags**

Inside the <thinking> tags, analyze the patient step by step:
1. **SORT Phase**: Can the patient walk? Can they wave? Are they still?
2. **ASSESS Phase**:
   - Do they have a peripheral pulse?
   - Are they in respiratory distress?
   - Is hemorrhage controlled?
   - Do they obey commands?
3. **LSI Phase**: What lifesaving interventions were performed?
4. **CATEGORIZE**: Based on the above, what is the SALT category?

**Step 2: Extract structured data using the function call**

After your thinking, call the extract_patient_data function with all the extracted information.

IMPORTANT:
- Use clinical reasoning to infer missing SALT assessment fields (can_walk, can_wave, etc.) based on the overall patient presentation
- If a patient is described as "alert and responsive" or "talking normally", infer they can wave and likely obey commands
- If a patient has severe injuries but is conscious, infer they can wave but may not be able to walk
- If a patient is unconscious or unresponsive, infer they cannot walk or wave
- If vital signs are stable and injuries are minor, infer normal mobility (can walk and wave)
- For patient_id, always set to null (will be auto-generated)
- For empty string fields (like lifesaving_intervention_performed, assigned_facility), use empty string "" if no information
- For numeric fields that represent "none", use 0
- Only omit fields where you truly have no basis for inference (e.g., exact vital signs not mentioned)

Patient Description:
{description}

Now, first think through the SALT protocol in <thinking> tags, then call the function."""


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
