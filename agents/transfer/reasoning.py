"""
LLM-based reasoning generator for transfer decisions.

Generates detailed explanations of why a particular facility was selected
based on patient profile, facility capabilities, and optimization results.
"""

import json
from typing import Dict, List, Optional
from schemas import PatientType, HealthcareFacilityType


REASONING_PROMPT_TEMPLATE = """You are a medical transfer coordinator explaining why a particular healthcare facility was selected for a patient.

## Patient Profile

**Name:** {patient_name}
**Age:** {patient_age}
**Gender:** {patient_gender}
**Acuity:** {patient_acuity}
**Location:** {patient_location}

**Injuries:**
{patient_injuries}

**Required Capabilities:**
{required_capabilities}

**Required Resources:**
{required_resources}

**Vital Signs:**
{vital_signs}

## Selected Destination

**Facility:** {destination_name}
**Level:** {destination_level} (1=Definitive Care, 2=Advanced Trauma, 3=Initial Stabilization)
**ETA:** {destination_eta} minutes
**Distance:** {destination_distance} km

**Available Capabilities:**
{destination_capabilities}

**Available Resources:**
{destination_resources}

## Alternative Facilities Considered

{alternatives}

## Optimization Details

**Incident Type:** {incident_type}
**Solver Status:** {solver_status}
**Optimization Method:** OR-Tools constraint-based optimization

The solver minimized:
- Time Cost (ETA × Acuity Weight)
- Capability Mismatch Penalty
- Resource Stress
- Stewardship Penalty (preserving scarce resources)

## Task

Write a clear, concise explanation (2-3 paragraphs) of why this facility was selected as optimal for this patient. Consider:

1. **Medical Match**: Does the facility have the required capabilities and resources?
2. **Proximity**: How does the ETA compare to alternatives?
3. **Resource Stewardship**: Are we preserving scarce capabilities for patients who truly need them?
4. **Patient Acuity**: How urgent is this patient's condition?

Be specific and reference actual data points. Write in a professional medical tone suitable for emergency coordinators.

Your explanation:"""


class TransferReasoningGenerator:
    """Generates detailed reasoning for transfer decisions using LLM."""

    def __init__(self, platform: str = "openrouter", **kwargs):
        """
        Initialize the reasoning generator.

        Args:
            platform: "openrouter" for API (local not supported for reasoning)
            **kwargs: Platform-specific configuration (api_key, model, base_url)
        """
        self.platform = platform.lower()

        if self.platform == "openrouter":
            self._init_openrouter(**kwargs)
        else:
            raise ValueError("Only 'openrouter' platform is supported for reasoning generation")

    def _init_openrouter(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
        **kwargs
    ):
        """Initialize OpenRouter API client."""
        try:
            from openai import OpenAI
            import os
        except ImportError:
            raise ImportError(
                "OpenAI SDK is required for reasoning generation. Install with: pip install openai"
            )

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY in config.py or environment"
            )

        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key,
        )

    def generate_reasoning(
        self,
        patient: PatientType,
        destination: HealthcareFacilityType,
        destination_eta: float,
        destination_distance: float,
        alternatives: List[Dict],
        incident_type: str,
        solver_status: str = "OPTIMAL",
    ) -> str:
        """
        Generate detailed reasoning for facility selection.

        Args:
            patient: The triaged patient
            destination: The selected facility
            destination_eta: ETA to destination in minutes
            destination_distance: Distance to destination in km
            alternatives: List of alternative facilities with their ETAs
            incident_type: Type of incident (MCI, MEDEVAC, PHE)
            solver_status: Optimization solver status

        Returns:
            Detailed reasoning text
        """
        # Format patient injuries
        injuries_text = "None reported"
        if patient.injuries and len(patient.injuries) > 0:
            injuries_list = []
            for injury in patient.injuries:
                locations = ", ".join(injury.locations) if injury.locations else "Unknown"
                mechanisms = ", ".join(injury.mechanisms) if injury.mechanisms else "Unknown"
                injuries_list.append(
                    f"  - {injury.description} (Location: {locations}, Mechanism: {mechanisms}, Severity: {injury.severity})"
                )
            injuries_text = "\n".join(injuries_list)

        # Format required capabilities
        required_caps = []
        if patient.required_medical_capabilities:
            caps_dict = patient.required_medical_capabilities.model_dump()
            for cap, required in caps_dict.items():
                if required:
                    required_caps.append(f"  - {cap.replace('_', ' ').title()}")
        required_capabilities_text = "\n".join(required_caps) if required_caps else "  - None specified"

        # Format required resources
        required_res = []
        if patient.required_medical_resources:
            res_dict = patient.required_medical_resources.model_dump()
            for res, qty in res_dict.items():
                if qty and qty > 0:
                    required_res.append(f"  - {res.replace('_', ' ').title()}: {qty}")
        required_resources_text = "\n".join(required_res) if required_res else "  - None specified"

        # Format vital signs
        vital_signs_text = "Not available"
        if patient.vital_signs:
            vs = patient.vital_signs
            vital_signs_text = f"HR: {vs.heart_rate}, BP: {vs.blood_pressure.systolic}/{vs.blood_pressure.diastolic}, RR: {vs.respiratory_rate}, SpO2: {vs.oxygen_saturation}%"

        # Format destination capabilities
        dest_caps = []
        if destination.capabilities:
            caps_dict = destination.capabilities.model_dump()
            for cap, available in caps_dict.items():
                if available:
                    dest_caps.append(f"  - {cap.replace('_', ' ').title()}")
        destination_capabilities_text = "\n".join(dest_caps) if dest_caps else "  - None"

        # Format destination resources
        dest_res = []
        if destination.medical_resources:
            res_dict = destination.medical_resources.model_dump()
            for res, qty in res_dict.items():
                if qty and qty > 0:
                    dest_res.append(f"  - {res.replace('_', ' ').title()}: {qty}")
        destination_resources_text = "\n".join(dest_res) if dest_res else "  - None"

        # Format alternatives
        alternatives_text = ""
        if alternatives and len(alternatives) > 0:
            alt_list = []
            for i, alt in enumerate(alternatives, 1):
                alt_list.append(
                    f"{i}. **{alt['facility_name']}** - ETA: {alt['eta_minutes']:.1f} min"
                )
            alternatives_text = "\n".join(alt_list)
        else:
            alternatives_text = "No viable alternatives found"

        # Format patient location
        patient_location = "Unknown"
        if patient.location:
            patient_location = f"{patient.location.latitude:.4f}°N, {patient.location.longitude:.4f}°W"

        # Build prompt
        prompt = REASONING_PROMPT_TEMPLATE.format(
            patient_name=patient.name,
            patient_age=patient.age,
            patient_gender=patient.gender,
            patient_acuity=patient.acuity,
            patient_location=patient_location,
            patient_injuries=injuries_text,
            required_capabilities=required_capabilities_text,
            required_resources=required_resources_text,
            vital_signs=vital_signs_text,
            destination_name=destination.name,
            destination_level=destination.level,
            destination_eta=f"{destination_eta:.1f}",
            destination_distance=f"{destination_distance:.2f}",
            destination_capabilities=destination_capabilities_text,
            destination_resources=destination_resources_text,
            alternatives=alternatives_text,
            incident_type=incident_type,
            solver_status=solver_status,
        )

        # Generate reasoning
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            if response.choices and len(response.choices) > 0:
                reasoning = response.choices[0].message.content.strip()
                return reasoning
            else:
                return f"Optimal facility selected using constraint optimization (ETA: {destination_eta:.1f} min)"

        except Exception as e:
            print(f"Warning: Failed to generate detailed reasoning: {e}")
            return f"Optimal facility selected using constraint optimization (ETA: {destination_eta:.1f} min)"
