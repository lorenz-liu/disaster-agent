# Transfer Agent - NATO MEDEVAC Evacuation Chain Decision Engine

Implements NATO medical doctrine (AJP-4.10) for MEDEVAC operations, creating evacuation chains that follow the Role 1 → Role 2 → Role 3 progression with strict adherence to the **10-1-2 timeline** (Golden Hour and Damage Control).

Uses **Google OR-Tools** constraint optimization for single-destination assignments (MCI/PHE incidents).

## Overview

The Transfer Agent assigns triaged patients to healthcare facilities using:
- **OR-Tools Constraint Optimization**: For single-destination assignments (MCI/PHE)
- **Greedy Heuristic with NATO Constraints**: For evacuation chains (MEDEVAC)

### Neuro-Symbolic Optimization

Combines:
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
    │  2. Incident Type?          │
    └─────────────────────────────┘
         ↓                    ↓
    MEDEVAC              MCI/PHE
         ↓                    ↓
    ┌─────────────────┐  ┌──────────────────────┐
    │ Greedy Heuristic│  │ OR-Tools Constraint  │
    │ NATO Chain      │  │ Optimization         │
    │ (Level 3→2→1)   │  │ (Single Destination) │
    └─────────────────┘  └──────────────────────┘
         ↓                    ↓
    Evacuation Chain    Single Destination
```

## OR-Tools Constraint Optimization (MCI/PHE)

For single-destination assignments, the agent uses Google OR-Tools SCIP solver to find the globally optimal assignment.

### Decision Variables

```
x[p, f] ∈ {0, 1}  for each patient p and facility f
x[p, f] = 1 if patient p is assigned to facility f
```

### Constraints

**C1: Assignment Constraint (Hard)**
```
∑(f) x[p, f] = 1  for each patient p
```
Each patient must be assigned to exactly one facility.

**C2: Resource Capacity Constraint (Hard)**
```
∑(p) x[p, f] × required[p, r] ≤ capacity[f, r]  for each facility f and resource r
```
Total resource usage at each facility cannot exceed capacity.

**C3: Exclusion Constraint (for finding alternatives)**
```
x[p, f] = 0  for excluded (patient, facility) pairs
```
Used when finding alternative facilities.

### Objective Function

**Minimize:**
```
Total Cost = ∑(p,f) x[p, f] × (Time Cost + Stewardship Penalty + Capability Penalty + Resource Stress)
```

Where:
- **Time Cost** = ETA × Acuity Weight
- **Stewardship Penalty** = ∑ Scarcity Penalty for unused capabilities
- **Capability Penalty** = 10,000 × (number of missing required capabilities)
- **Resource Stress** = ∑ (utilization_rate² × 100) for each resource

### Optimization Rules (`rules.py`)

All optimization factors are defined in `rules.py` for easy modification:

```python
# Acuity Weights (higher = higher priority)
ACUITY_WEIGHTS = {
    "Immediate": 100,
    "Delayed": 50,
    "Minimal": 10,
}

# Scarcity Penalties (preserve scarce resources)
SCARCITY_PENALTIES = {
    "burn": 500,
    "pediatric": 500,
    "neurosurgical": 400,
    "cardiac": 300,
}

# Capability Mismatch Penalty
CAPABILITY_MISMATCH_PENALTY = 10000

# Resource Deficit Penalty
RESOURCE_DEFICIT_PENALTY = 5000
```

**To modify optimization behavior**, edit `rules.py`:
- Increase acuity weight → prioritize faster transport for that acuity
- Increase scarcity penalty → preserve that capability more aggressively
- Decrease capability penalty → allow more flexibility in capability matching

## NATO MEDEVAC Evacuation Chains

For MEDEVAC incidents, the agent builds sequential evacuation chains using a greedy heuristic with NATO timeline constraints.

### Survival Window Calculation

```
Slack Time = predicted_death_timestamp - current_time
```

- **Δt < 0**: Patient is unsalvageable → Action: `Forfeit`
- **Δt < ETA**: Patient will not survive transport → Action: `Forfeit`
- **Δt > ETA**: Viable for transport → Action: `Transfer`

### Facility Selection Heuristic

For each role in the chain, find the best facility by minimizing:

```
Cost = (ETA × Acuity Weight) + Capability Penalty + Resource Stress
```

Subject to:
- ETA < Time Budget (60 min for Role 1, 120 min cumulative for Role 2)
- Has required capabilities (or heavy penalty)
- Has sufficient resources (or penalty)

## Customizing Optimization Behavior

All optimization factors are defined in `rules.py`. Modify these values to adjust the solver's behavior:

### Example 1: Prioritize Immediate Patients More Aggressively

```python
# In rules.py
ACUITY_WEIGHTS = {
    "Immediate": 150,  # Increased from 100
    "Delayed": 50,
    "Minimal": 10,
}
```

This makes the solver minimize transport time more aggressively for Immediate patients.

### Example 2: Preserve Burn Units More Strictly

```python
# In rules.py
SCARCITY_PENALTIES = {
    "burn": 1000,  # Increased from 500
    "pediatric": 500,
    # ...
}
```

This makes the solver much more reluctant to assign non-burn patients to burn units.

### Example 3: Allow More Flexibility in Capability Matching

```python
# In rules.py
CAPABILITY_MISMATCH_PENALTY = 5000  # Reduced from 10000
```

This allows the solver to assign patients to facilities missing some required capabilities in resource-constrained scenarios.

### Example 4: Adjust Resource Stress Sensitivity

```python
# In rules.py
RESOURCE_STRESS_EXPONENT = 3.0  # Increased from 2.0
```

This makes resource stress increase more rapidly as facilities approach capacity, encouraging better load balancing.

## Requirements

```bash
pip install pydantic ortools
```

**OR-Tools** is required for constraint optimization:
```bash
pip install ortools
```

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

2. Determine Incident Type
   ├─ MEDEVAC → Build Evacuation Chain (greedy heuristic)
   └─ MCI/PHE → OR-Tools Optimization (single destination)

3. MEDEVAC Chain Building
   ├─ Find Role 1 (Level 3) within 60 min
   ├─ Find Role 2 (Level 2) within 120 min cumulative
   ├─ Find Role 3 (Level 1) within survival window
   └─ Validate NATO timeline compliance

4. MCI/PHE Optimization
   ├─ Set up OR-Tools SCIP solver
   ├─ Define decision variables x[p, f]
   ├─ Add constraints (assignment, resources)
   ├─ Minimize objective function
   ├─ Extract optimal solution
   └─ Find alternative facilities (re-run with exclusions)

5. Return Decision
   ├─ Action: Transfer or Forfeit
   ├─ Reasoning code
   ├─ Destination/Chain
   └─ Alternatives (for MCI/PHE)
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
