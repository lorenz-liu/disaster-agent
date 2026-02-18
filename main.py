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

    # Patient description (natural language)
    description = """
    Michael Chen, 52-year-old male, motorcycle accident at intersection of Yonge and Bloor.
    Location: 43.6708°N, 79.3860°W

    Complaining of severe chest and leg pain.
    Heart rate 105, blood pressure 110/70, breathing rate 20, oxygen level 95%.
    Alert and responsive. Suspected rib fractures and possible tibia fracture.

    Patient can wave but cannot walk. Has peripheral pulse. Not in severe respiratory distress.
    Hemorrhage is controlled. Follows commands.
    """

    print("=" * 80)
    print("DISASTER AGENT - COMPLETE WORKFLOW")
    print("=" * 80)
    print("\nWorkflow: Natural Language → Triage → Transfer\n")
    print("=" * 80)

    # ========================================================================
    # STEP 1: TRIAGE
    # ========================================================================
    print("\n" + "=" * 80)
    print("STEP 1: PATIENT TRIAGE")
    print("=" * 80)

    # Create triage agent
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

    # Save triage result
    with open("triage_result.json", "w") as f:
        json.dump(patient.model_dump(), f, indent=2)
    print("Triage result saved to triage_result.json")

    triage_agent.unload_model()

    # ========================================================================
    # STEP 2: TRANSFER DECISION
    # ========================================================================
    print("\n\n" + "=" * 80)
    print("STEP 2: TRANSFER DECISION")
    print("=" * 80)

    # Load facilities
    print("\nLoading healthcare facilities from example_data/facilities.json...")
    facilities = load_facilities()
    print(f"✓ Loaded {len(facilities)} facilities")

    # Display facility summary
    print("\nFacility Summary:")
    level_counts = {1: 0, 2: 0, 3: 0}
    for f in facilities:
        level_counts[f.level] += 1
    print(f"  - Level 1 (Definitive Care): {level_counts[1]} facilities")
    print(f"  - Level 2 (Advanced Trauma): {level_counts[2]} facilities")
    print(f"  - Level 3 (Initial Stabilization): {level_counts[3]} facilities")

    # Create transfer agent
    print("\nCreating transfer agent...")
    print(f"Incident Type: MCI (Mass Casualty Incident)")
    print(f"Optimization: OR-Tools constraint-based")

    transfer_agent = TransferAgent(
        patient=patient,
        facilities=facilities,
        incident_type="MCI",  # Use "MEDEVAC" for evacuation chains
    )

    # Run transfer decision
    print("\nRunning transfer optimization...")
    decision = transfer_agent.decide_transfer()

    # Display decision
    print("\n" + "-" * 80)
    print("TRANSFER DECISION")
    print("-" * 80)
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

    # Save transfer decision
    with open("transfer_decision.json", "w") as f:
        json.dump(decision, f, indent=2)
    print("\nTransfer decision saved to transfer_decision.json")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Patient: {patient.name}, {patient.age} years old, {patient.gender}")
    print(f"Acuity: {patient.acuity}")
    print(f"Location: {patient.location.latitude:.4f}°N, {patient.location.longitude:.4f}°W")

    if decision['action'] == "Transfer":
        print(f"\n✓ Transfer Decision: {decision['destination']['facility_name']}")
        print(f"  ETA: {decision['destination']['eta_minutes']:.1f} minutes")
    else:
        print(f"\n✗ Transfer Decision: {decision['action']}")
        print(f"  Reason: {decision['reasoning']}")

    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
