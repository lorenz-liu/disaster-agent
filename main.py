"""
Patient Triage Agent - Simple Test
"""

import json
from agents.triage import PatientTriageAgent
import config


def main():
    """Test the triage agent with a moderate complexity patient description."""

    description = """
    Michael Chen, 52-year-old male, motorcycle accident.
    Complaining of chest and leg pain.
    Heart rate 105, blood pressure 110/70, breathing rate 20, oxygen level 95%.
    Alert and responsive. Suspected rib fractures and possible tibia fracture.
    """

    # Create agent based on config
    if config.PLATFORM == "local":
        agent = PatientTriageAgent(
            platform="local",
            model_path=config.LOCAL_MODEL_PATH,
            gpu_memory_utilization=config.LOCAL_MODEL_GPU_MEMORY_UTILIZATION,
            tensor_parallel_size=config.LOCAL_MODEL_TENSOR_PARALLEL_SIZE,
        )
    elif config.PLATFORM == "openrouter":
        agent = PatientTriageAgent(
            platform="openrouter",
            api_key=config.OPENROUTER_API_KEY,
            model=config.OPENROUTER_MODEL,
            base_url=config.OPENROUTER_BASE_URL,
        )
    else:
        raise ValueError(f"Unknown platform: {config.PLATFORM}")

    # Run triage
    patient = agent.triage_patient(description, validate=True, verbose=True)

    # Save result
    if patient:
        print("\n✓ Triage completed successfully")
        with open("patient_output.json", "w") as f:
            json.dump(patient.model_dump(), f, indent=2)
        print("Result saved to patient_output.json")
    else:
        print("\n✗ Triage failed")

    agent.unload_model()


if __name__ == "__main__":
    main()
