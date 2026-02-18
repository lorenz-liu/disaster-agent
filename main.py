"""
Disaster Agent - Complete Workflow: Triage → Transfer

This script demonstrates the complete workflow:
1. Natural language patient description
2. Triage using SALT protocol (with chain of thought)
3. Transfer decision using OR-Tools optimization
"""

import json
from agents.triage import PatientTriageAgent
from agents.transfer import TransferAgent
from schemas import HealthcareFacilityType
import config


def load_facilities():
    """Load healthcare facilities from example data."""
    with open("example_data/facilities.json", "r") as f:
        facilities_data = json.load(f)

    # Convert to HealthcareFacilityType objects
    facilities = []
    for facility_data in facilities_data:
        facility = HealthcareFacilityType(**facility_data)
        facilities.append(facility)

    return facilities


def main():
    """Run the complete triage → transfer workflow."""

    description = input("Describe the patient: ")
    if config.PLATFORM == "local":
        triage_agent = PatientTriageAgent(
            platform="local",
            model_path=config.LOCAL_MODEL_PATH,
            gpu_memory_utilization=config.LOCAL_MODEL_GPU_MEMORY_UTILIZATION,
            tensor_parallel_size=config.LOCAL_MODEL_TENSOR_PARALLEL_SIZE,
        )
    elif config.PLATFORM == "openrouter":
        triage_agent = PatientTriageAgent(
            platform="openrouter",
            api_key=config.OPENROUTER_API_KEY,
            model=config.OPENROUTER_MODEL,
            base_url=config.OPENROUTER_BASE_URL,
        )
    else:
        raise ValueError(f"Unknown platform: {config.PLATFORM}")

    # Run triage
    patient = triage_agent.triage_patient(description, validate=True, verbose=True)

    if not patient:
        print("\n✗ Triage failed - cannot proceed to transfer")
        return

    print("\n✓ Triage completed successfully")

    triage_agent.unload_model()

    # Load facilities
    print("\nLoading healthcare facilities from example_data/facilities.json...")
    facilities = load_facilities()
    print(f"✓ Loaded {len(facilities)} facilities")

    transfer_agent = TransferAgent(
        patient=patient,
        facilities=facilities,
        incident_type="MCI",  # Use "MEDEVAC" for evacuation chains
    )

    # Run transfer decision
    print("\nRunning transfer optimization...")
    decision = transfer_agent.decide_transfer()

    print(f"Action: {decision['action']}")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Reasoning Code: {decision['reasoning_code']}")

    if decision['action'] == "Transfer":
        dest = decision['destination']
        print(f"\nDestination:")
        print(f"  - Facility: {dest['facility_name']}")
        print(f"  - Facility ID: {dest['facility_id']}")
        print(f"  - ETA: {dest['eta_minutes']:.1f} minutes")

        # Display alternatives if available
        alternatives = decision.get('alternatives', [])
        if alternatives:
            print(f"\nAlternative Facilities ({len(alternatives)}):")
            for i, alt in enumerate(alternatives, 1):
                print(f"  {i}. {alt['facility_name']} (ETA: {alt['eta_minutes']:.1f} min)")

        # Display solver status
        if 'solver_status' in decision:
            print(f"\nSolver Status: {decision['solver_status']}")


if __name__ == "__main__":
    main()
