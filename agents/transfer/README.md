# Transfer Agent - NATO MEDEVAC Evacuation Chain Decision Engine

Implements NATO medical doctrine (AJP-4.10) for MEDEVAC operations, creating evacuation chains that follow the Role 1 → Role 2 → Role 3 progression with strict adherence to the **10-1-2 timeline** (Golden Hour and Damage Control).

## Overview

The Transfer Agent assigns triaged patients to healthcare facilities using neuro-symbolic optimization that combines:
- **Neural Component**: Mortality prediction based on patient acuity and vital signs
- **Symbolic Component**: Constraint-based optimization for capability matching, resource allocation, and timeline compliance

## NATO Medical Doctrine (AJP-4.10)

### Medical Echelon System

The NATO medical system is organized into three roles:

- **Role 1 (Level 3)**: Initial stabilization and triage at point of injury
- **Role 2 (Level 2)**: Advanced trauma care with surgical capability
- **Role 3 (Level 1)**: Definitive surgical care and specialized treatment

### Clinical Timeline Constraints (10-1-2 Rule)

| Doctrine Step | Target Timeline | Description |
|---------------|----------------|-------------|
| **Initial Aid** | 10 Minutes | First responder care at point of injury |
| **Role 1** | 60 Minutes | Golden Hour - Initial stabilization |
| **Role 2** | 120 Minutes | Damage Control - Advanced trauma care |

## Architecture

```
Triaged Patient + Available Facilities
         ↓
    Transfer Agent
         ↓
    ┌─────────────────────────────┐
    │  1. Calculate Slack Time    │
    │     (Survival Window)        │
    └─────────────────────────────┘
         ↓
    ┌─────────────────────────────┐
    │  2. Filter by Capabilities  │
    │     & Resources              │
    └─────────────────────────────┘
         ↓
    ┌─────────────────────────────┐
    │  3. Build Evacuation Chain  │
    │     (MEDEVAC) or Single     │
    │     Destination (MCI/PHE)   │
    └─────────────────────────────┘
         ↓
    Transfer Decision
    (Action + Reasoning + Chain/Destination)
```

## Neuro-Symbolic Optimization

### 1. Neural Component: Survival Maximization

The agent calculates **Slack Time (Δt)** to determine execution priority:

```
Slack Time = predicted_death_timestamp - current_time
```

- **Δt < 0**: Patient is unsalvageable → Action: `Forfeit`
- **Δt < ETA**: Patient will not survive transport → Action: `Forfeit`
- **Δt > ETA**: Viable for transport → Action: `Transfer`

Patient priority weights based on SALT acuity:
- Dead: 0
- Expectant: 80
- Immediate: 100
- Delayed: 50
- Minimal: 10

### 2. Symbolic Component: Constraint Optimization

**Capability Matching:**
```python
valid_assignment = all(
    facility.capabilities[cap] == True
    for cap in patient.required_medical_capabilities
    if patient.required_medical_capabilities[cap] == True
)
```

**Resource Availability:**
```python
has_resources = all(
    facility.resources[r] >= patient.required_resources[r]
    for r in patient.required_resources
)
```

**Cost Function:**
```
Total Cost = (ETA × Patient Weight) + Capability Penalty + Resource Stress
```

- Capability Penalty: 10,000 per missing required capability
- Resource Stress: Exponential penalty as utilization approaches 100%
- Resource Deficit Penalty: 5,000 if insufficient resources

## Usage

### Basic Example

```python
from agents.transfer import TransferAgent
from schemas import PatientType, HealthcareFacilityType

# Triaged patient
patient = PatientType(
    patient_id="P-001",
    name="John Doe",
    age=45,
    acuity="Immediate",
    location={"latitude": 43.6532, "longitude": -79.3832},
    predicted_death_timestamp=time.time() + 7200,  # 2 hours
    required_medical_capabilities={
        "trauma_center": True,
        "cardiac": True,
    },
    # ... other fields
)

# Available facilities
facilities = [
    HealthcareFacilityType(
        facility_id="F-001",
        name="City General Hospital",
        level=1,  # Level 1 = Role 3 (Definitive care)
        location={"latitude": 43.6629, "longitude": -79.3957},
        capabilities={
            "trauma_center": True,
            "cardiac": True,
            # ... other capabilities
        },
        medical_resources={
            "ordinary_icu": 5,
            "operating_room": 3,
            # ... other resources
        },
    ),
    # ... more facilities
]

# Create agent and decide transfer
agent = TransferAgent(
    patient=patient,
    facilities=facilities,
    incident_type="MCI",  # or "MEDEVAC" or "PHE"
)

decision = agent.decide_transfer()
print(decision)
```

### Decision Output

#### For MEDEVAC (Evacuation Chain)

```python
{
    "action": "Transfer",
    "reasoning": "NATO-compliant evacuation chain constructed (3 facilities, total time: 95.3 min)",
    "reasoning_code": "EVACUATION_CHAIN_OPTIMAL",
    "evacuation_chain": [
        {
            "role": "Role 1",
            "level": 3,
            "facility_id": "F-003",
            "facility_name": "Field Hospital Alpha",
            "eta_minutes": 25.5,
            "cumulative_time": 25.5,
            "timeline_compliance": True
        },
        {
            "role": "Role 2",
            "level": 2,
            "facility_id": "F-002",
            "facility_name": "Combat Support Hospital",
            "eta_minutes": 35.2,
            "cumulative_time": 60.7,
            "timeline_compliance": True
        },
        {
            "role": "Role 3",
            "level": 1,
            "facility_id": "F-001",
            "facility_name": "Regional Medical Center",
            "eta_minutes": 34.6,
            "cumulative_time": 95.3,
            "timeline_compliance": True
        }
    ],
    "total_time_minutes": 95.3,
    "survival_window_minutes": 180.0,
    "nato_compliance": {
        "role1_compliant": True,
        "role2_compliant": True,
        "survival_compliant": True
    }
}
```

#### For MCI/PHE (Single Destination)

```python
{
    "action": "Transfer",
    "reasoning": "Optimal facility selected (ETA: 15.3 min)",
    "reasoning_code": "TRANSFER_OPTIMAL",
    "destination": {
        "facility_id": "F-001",
        "facility_name": "City General Hospital",
        "eta_minutes": 15.3
    }
}
```

#### Forfeit Decision

```python
{
    "action": "Forfeit",
    "reasoning": "Patient will not survive evacuation chain (requires 150.0 min, survival window: 120.0 min)",
    "reasoning_code": "DEAD_ON_ARRIVAL",
    "evacuation_chain": []
}
```

## Incident Types

The agent supports three incident types:

1. **MCI (Mass Casualty Incident)**: Single destination assignment
2. **MEDEVAC (Medical Evacuation)**: NATO-compliant evacuation chain (Level 3 → 2 → 1)
3. **PHE (Public Health Emergency)**: Single destination assignment

## Decision Flow

```
1. Calculate Slack Time
   ├─ predicted_death_timestamp - current_time
   └─ If ≤ 0 or acuity = "Dead" → Forfeit

2. Filter Facilities
   ├─ By healthcare level (for MEDEVAC)
   ├─ By capability match
   └─ By resource availability

3. Optimize Assignment
   ├─ MEDEVAC: Build sequential chain (Role 1 → 2 → 3)
   │   ├─ Role 1 within 60 min
   │   ├─ Role 2 within 120 min cumulative
   │   └─ Role 3 within survival window
   │
   └─ MCI/PHE: Find single best facility
       ├─ Minimize: time_cost + capability_penalty + resource_stress
       └─ Ensure ETA < survival window

4. Validate Decision
   ├─ Check timeline compliance
   ├─ Verify survival window
   └─ Return action + reasoning
```

## Reasoning Codes

| Code | Description |
|------|-------------|
| `EVACUATION_CHAIN_OPTIMAL` | NATO-compliant chain successfully constructed |
| `TRANSFER_OPTIMAL` | Single destination selected (MCI/PHE) |
| `PATIENT_DECEASED` | Patient already deceased or survival window expired |
| `DEAD_ON_ARRIVAL` | Patient will not survive transport |
| `NO_FACILITIES_AVAILABLE` | No suitable facilities available |
| `NO_VIABLE_CHAIN` | Cannot construct evacuation chain meeting constraints |
| `NO_LOCATION` | Patient location unknown |

## Transport Modes

The agent calculates ETA based on transport mode:

- **Ground Transport (Ambulance)**: 50 km/h
- **Air Transport (Helicopter)**: 200 km/h

Currently defaults to ground transport. Future versions may include automatic mode selection based on distance and urgency.

## Integration with Triage Agent

The Transfer Agent is designed to work seamlessly with the Triage Agent:

```python
from agents.triage import PatientTriageAgent
from agents.transfer import TransferAgent

# Step 1: Triage patient
triage_agent = PatientTriageAgent(platform="openrouter")
patient = triage_agent.triage_patient(description, validate=True)

# Step 2: Decide transfer
transfer_agent = TransferAgent(
    patient=patient,
    facilities=available_facilities,
    incident_type="MEDEVAC"
)
decision = transfer_agent.decide_transfer()
```

## Requirements

```bash
pip install pydantic
```

No additional dependencies required - uses only Python standard library and Pydantic schemas.

## References

- NATO AJP-4.10: Allied Joint Medical Support Doctrine
- NATO STANAG 2560: Medical Evacuation
- Golden Hour Concept: Cowley, R. A. (1975)
- Damage Control Surgery: Rotondo, M. F., et al. (1993)
- SALT Triage Protocol: Sort, Assess, Lifesaving Interventions, Treatment/Transport

## Future Enhancements

- [ ] Automatic transport mode selection (ground vs. air)
- [ ] Multi-patient batch optimization
- [ ] Real-time traffic data integration
- [ ] Weather condition considerations
- [ ] Resource reservation and conflict resolution
- [ ] Dynamic facility capacity updates
