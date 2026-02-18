# Disaster Agent

AI-powered disaster management system for patient triage and transfer optimization using neuro-symbolic reasoning.

## Overview

This system implements a complete workflow for disaster response:

```mermaid
flowchart TB
    Start([Natural Language Patient Description]) --> TriageAgent

    subgraph TriageAgent["TRIAGE AGENT"]
        direction TB
        T1[Parse Natural Language Input]
        T2[Extract Vital Signs & Injuries]
        T3[Apply SALT Protocol]
        T4[Assess Acuity Level]
        T5[Predict Mortality Window]
        T6[Determine Required Capabilities]
        T7[Validate Schema]

        T1 --> T2 --> T3 --> T4 --> T5 --> T6 --> T7

        TechStack1["Tech Stack:<br/>• OpenAI/OpenRouter API<br/>• Function Calling<br/>• SALT Protocol<br/>• Chain-of-Thought<br/>• Pydantic Schemas"]
    end

    TriageAgent --> PatientData[(Structured Patient Data<br/>PatientType)]

    PatientData --> TransferAgent
    Facilities[(Healthcare Facilities<br/>HealthcareFacilityType)] --> TransferAgent

    subgraph TransferAgent["TRANSFER AGENT"]
        direction TB
        TA1{Incident Type?}
        TA2[MEDEVAC<br/>Greedy Chain]
        TA3[MCI/PHE<br/>OR-Tools Optimizer]

        TA1 -->|MEDEVAC| TA2
        TA1 -->|MCI PHE| TA3

        TA2 --> Chain[Role 1 → Role 2 → Role 3<br/>60min Golden Hour<br/>120min Damage Control]

        TA3 --> Optimize[Constraint Optimization<br/>• Minimize ETA × Acuity<br/>• Capability Match<br/>• Resource Capacity<br/>• Stewardship Penalty]

        Chain --> LLM[Generate LLM Reasoning]
        Optimize --> LLM

        TechStack2["Tech Stack:<br/>• Google OR-Tools<br/>• CP-SAT Solver<br/>• NATO AJP-4.10<br/>• Neuro-Symbolic AI"]
    end

    TransferAgent --> Output([Optimal Facility Assignment<br/>+ Reasoning + Alternatives])

    style TriageAgent fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    style TransferAgent fill:#fff4e1,stroke:#cc6600,stroke-width:2px
    style PatientData fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Facilities fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Output fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Start fill:#fff,stroke:#333,stroke-width:2px
```

### System Dataflow

```mermaid
graph LR
    subgraph Input
        NL[Natural Language<br/>Patient Description]
    end

    subgraph TriageOutput["Triage Agent Output"]
        PD[PatientType Schema]
        VS[Vital Signs]
        INJ[Injuries]
        ACU[Acuity Level]
        CAP[Required Capabilities]
        MOR[Mortality Prediction]
        LOC[Location]
    end

    subgraph TransferInput["Transfer Agent Input"]
        PT[Patient Data]
        FAC[Facility List]
        RULES[Optimization Rules]
    end

    subgraph TransferOutput["Transfer Agent Output"]
        DEST[Destination Facility]
        ETA[ETA Minutes]
        REASON[LLM Reasoning]
        ALT[Alternative Facilities]
        STATUS[Solver Status]
    end

    NL --> PD
    PD --> VS & INJ & ACU & CAP & MOR & LOC

    VS & INJ & ACU & CAP & MOR & LOC --> PT
    PT --> DEST
    FAC --> DEST
    RULES --> DEST

    DEST --> ETA & REASON & ALT & STATUS

    style Input fill:#e3f2fd,stroke:#1976d2
    style TriageOutput fill:#e8f5e9,stroke:#388e3c
    style TransferInput fill:#fff3e0,stroke:#f57c00
    style TransferOutput fill:#f3e5f5,stroke:#7b1fa2
```

### Workflow

1. **Natural Language Input**: Describe a patient in plain English (injuries, vital signs, location)
2. **Triage Agent**: Uses SALT protocol with chain-of-thought reasoning to assess patient acuity
3. **Transfer Agent**: Assigns patient to optimal healthcare facility using constraint optimization

### Tech Stack

- **Pydantic**: Type-safe data schemas and validation
- **OpenAI/OpenRouter**: LLM-powered triage with structured output (function calling)
- **OR-Tools**: Google's constraint optimization solver for facility assignment
- **SALT Protocol**: Sort, Assess, Lifesaving Interventions, Treatment/Transport
- **NATO AJP-4.10**: Medical evacuation doctrine (MEDEVAC chains)
- **Neuro-Symbolic AI**: Combines neural reasoning (LLM) with symbolic optimization (constraints)

## Quick Start

```bash
# Install dependencies
pip install pydantic openai ortools

# Run complete workflow
python main.py
```

## Agents

### Triage Agent (`agents/triage/`)

Converts natural language patient descriptions into structured triage assessments using SALT protocol.

**Input**: Natural language description
**Output**: Structured PatientType with acuity, vital signs, required capabilities

**Features**:
- Chain-of-thought reasoning with `<thinking>` tags
- SALT protocol compliance (Immediate, Delayed, Minimal, Expectant, Dead)
- Mortality prediction based on vital signs and injuries
- Structured output via OpenAI function calling

### Transfer Agent (`agents/transfer/`)

Assigns triaged patients to optimal healthcare facilities using constraint-based optimization.

**Input**: PatientType + List of HealthcareFacilityType
**Output**: Transfer decision with destination facility or evacuation chain

**Features**:
- OR-Tools SCIP solver for single-destination optimization (MCI/PHE)
- NATO MEDEVAC evacuation chains (Role 1 → Role 2 → Role 3)
- Configurable optimization rules (`rules.py`)
- Resource stewardship (preserve scarce capabilities)
- Timeline compliance (Golden Hour, Damage Control)
- LLM-generated reasoning for explainable decision-making

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
