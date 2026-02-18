# Patient Triage Agent

Hybrid LLM + Rule-Based system for extracting structured patient data from natural language descriptions.

## Architecture

```
Natural Language Description 
         ↓
    LLM Extraction (Local GPT-OSS-20B)
         ↓
    Post-Processing (Calculate derived fields)
         ↓
    Validation (Medical logic checks)
         ↓
    Pydantic Validation (Schema compliance)
         ↓
    Structured Patient JSON
```

## Components

### 1. LLM Extractor (`llm_extractor.py`)
- Loads and runs local GPT-OSS-20B model
- Extracts structured data from natural language
- Handles JSON parsing from model output

### 2. Prompt Templates (`prompts.py`)
- Configurable prompts for LLM
- Few-shot examples
- **Modify here** to adjust LLM behavior without changing code

### 3. Post-Processors (`post_processors.py`)
- Calculate derived fields (GCS total, acuity, mortality risk)
- Apply medical logic and triage algorithms
- **Modify here** to change calculation logic

Available post-processors:
- `GCSCalculator`: Calculate Glasgow Coma Scale total
- `AcuityDetermination`: Determine patient acuity using START triage
- `MortalityPredictor`: Predict death timestamp based on risk factors
- `ResourceEstimator`: Estimate required medical resources
- `DefaultValueFiller`: Fill missing fields with defaults

### 4. Validation Rules (`validation_rules.py`)
- Modular validation rules
- Medical logic consistency checks
- **Modify here** to add/remove validation rules

Available rules:
- `RequiredFieldsRule`: Check all required fields present
- `VitalSignsRangeRule`: Validate vital signs in plausible ranges
- `GlasgowComaScaleRule`: Validate GCS scores
- `AgeRangeRule`: Validate age is reasonable
- `DeceasedConsistencyRule`: Check deceased status consistency
- `InjuryCapabilityConsistencyRule`: Validate injury-capability mapping

### 5. Main Agent (`agent.py`)
- Orchestrates the entire pipeline
- Provides simple API for single/batch processing
- Handles model loading/unloading

## Usage

### Single Patient

```python
from agents.triage import PatientTriageAgent

agent = PatientTriageAgent(model_path="/models/gpt-oss-20b")

description = """
45-year-old male, car accident, chest pain,
HR 110, BP 90/60, RR 22, SpO2 92%, GCS 15
"""

patient = agent.triage_patient(description, validate=True, verbose=True)

if patient:
    print(patient.model_dump_json(indent=2))

agent.unload_model()
```

### Batch Processing

```python
from agents.triage import PatientTriageAgent

descriptions = [
    "35F, chest trauma, HR 120, BP 85/50...",
    "22M, leg fracture, HR 90, BP 120/80...",
    "60F, chemical burns, HR 105, BP 95/65..."
]

with PatientTriageAgent(model_path="/models/gpt-oss-20b") as agent:
    patients = agent.triage_batch(descriptions, validate=True)

    for patient in patients:
        if patient:
            print(f"Patient {patient.patient_id}: {patient.acuity}")
```

## Customization

### Adding a Validation Rule

Edit `validation_rules.py`:

```python
class CustomRule(ValidationRule):
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        # Your validation logic here
        return len(errors) == 0, errors

# Add to registry
VALIDATION_RULES.append(CustomRule())
```

### Adding a Post-Processor

Edit `post_processors.py`:

```python
class CustomProcessor(PostProcessor):
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Your processing logic here
        return data

# Add to registry (order matters!)
POST_PROCESSORS.append(CustomProcessor())
```

### Modifying Prompts

Edit `prompts.py` to change how the LLM extracts data:

```python
PATIENT_EXTRACTION_PROMPT = """
Your custom prompt here...
{description}
"""
```

## Requirements

```bash
pip install torch transformers pydantic
```

## Model Setup

Download GPT-OSS-20B to `/models/gpt-oss-20b`:

```bash
# Using huggingface-cli
huggingface-cli download openai/gpt-oss-20b --local-dir /models/gpt-oss-20b
```

## Examples

Run the example script:

```bash
python example_triage.py
```

This will:
1. Process a single patient with verbose output
2. Show the complete pipeline execution
3. Save results to `patient_output.json`

## Pipeline Details

### Stage 1: LLM Extraction
- Model generates structured JSON from natural language
- Extracts all available fields
- Handles missing/ambiguous information

### Stage 2: Post-Processing
- Calculates GCS total from components
- Determines acuity using START triage principles
- Predicts mortality risk based on vital signs
- Estimates required resources
- Fills default values

### Stage 3: Validation
The system applies the following validation rules to ensure medical plausibility and data integrity:

#### 1. Required Fields Validation
- **Description**: Must be present and non-null
- **Patient ID**: Auto-generated with UUID if missing
- **Rationale**: Ensures minimum viable data for patient tracking

#### 2. Vital Signs Range Validation
Validates physiological parameters are within extreme but plausible ranges:
- **Heart Rate**: 0-300 bpm
- **Systolic Blood Pressure**: 0-300 mmHg
- **Diastolic Blood Pressure**: 0-200 mmHg
- **Blood Pressure Consistency**: Systolic must be ≥ diastolic
- **Respiratory Rate**: 0-100 breaths/min
- **Oxygen Saturation**: 0-100%
- **Temperature**: 25-45°C

**Note**: These are extreme ranges to accommodate unusual but possible cases. Values outside these ranges are flagged as errors.

**Behavior**: Skips validation if vital signs data is not provided (null).

#### 3. Glasgow Coma Scale (GCS) Validation
Validates neurological assessment scores:
- **Eye Response**: 1-4
- **Verbal Response**: 1-5
- **Motor Response**: 1-6
- **Total Score**: 3-15
- **Component Consistency**: If all components are present, validates that total = eye + verbal + motor

**Behavior**: Skips validation if consciousness data is not provided (null).

#### 4. Age Range Validation
- **Range**: 0-120 years
- **Rationale**: Accommodates neonates to supercentenarians

**Behavior**: Skips validation if age is not provided (null).

#### 5. Deceased Status Consistency
Ensures logical consistency between deceased flag and acuity:
- If `deceased = true`, then `acuity` should be "Deceased"
- If `acuity = "Deceased"`, then `deceased` should be true

**Behavior**: Only validates if both fields are present.

#### 6. Injury-Capability Consistency (Warning Only)
Provides warnings (not errors) when injuries suggest specific medical capabilities:

**Location-Based Capability Mapping**:
- **Head injuries** → Trauma center, Neurosurgical
- **Neck injuries** → Trauma center, Vascular, ENT
- **Chest injuries** → Trauma center, Thoracic, Cardiac
- **Back injuries** → Trauma center, Orthopedic
- **Pelvis injuries** → Trauma center, Orthopedic
- **Abdomen injuries** → Trauma center, Hepatobiliary
- **Upper limb injuries** → Orthopedic
- **Lower limb injuries** → Orthopedic

**Mechanism-Based Capability Mapping**:
- **Thermal injuries** → Burn unit
- **Blast injuries** → Trauma center
- **Chemical exposure** → Trauma center
- **Radiation exposure** → Trauma center

**Behavior**:
- Generates warnings (not errors) when injury patterns suggest capabilities not marked as required
- Skips validation if injuries or capabilities data is not provided (null)
- Warnings inform but do not block processing

#### Validation Philosophy
- **Permissive by Design**: Most fields are optional to accommodate incomplete information
- **Null Tolerance**: Validation rules skip gracefully when data is not provided
- **Medical Plausibility**: Ranges are intentionally broad to avoid false rejections
- **Warnings vs Errors**: Capability mismatches generate warnings to inform clinicians without blocking triage

### Stage 4: Schema Validation
- Pydantic validates against PatientType schema
- Ensures type correctness
- Final data integrity check

## Medical Logic

### Acuity Determination (START Triage)
- **Critical**: ≥2 abnormal vital signs OR critical injury
- **Severe**: ≥1 abnormal vital sign OR severe injury
- **Minor**: Stable vital signs, minor injuries

Abnormal indicators:
- RR < 10 or > 29
- SpO2 < 90%
- Systolic BP < 90
- HR < 50 or > 120
- GCS < 13

### Mortality Prediction
Risk score based on:
- Acuity level (Critical +3, Severe +1)
- Severe hypotension (SBP < 70) +2
- Severe hypoxia (SpO2 < 80) +2
- Very low GCS (≤8) +2

Prediction:
- Risk ≥5: Death in 1-2 hours
- Risk 3-4: Death in 4-6 hours
- Risk <3: No predicted death

## Troubleshooting

### Model fails to load
- Check model path is correct
- Ensure sufficient GPU/RAM
- Try reducing model precision

### JSON parsing fails
- Check prompt template format
- Increase `max_new_tokens`
- Lower `temperature` for more deterministic output

### Validation errors
- Review validation rules in `validation_rules.py`
- Check if rules are too strict
- Add custom rules for your use case
