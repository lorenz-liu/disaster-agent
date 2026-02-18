"""
Optimization Rules and Configuration for Transfer Agent

This file defines all the optimization factors, weights, and penalties
used in the constraint-based transfer decision engine.

Modify these values to adjust the optimization behavior without changing the solver code.
"""

from typing import Dict


class OptimizationRules:
    """
    Configuration for the neuro-symbolic optimization engine.

    The solver minimizes:
        Total Cost = (Time Cost) + (Stewardship Penalty) + (Capability Penalty)

    Where:
    - Time Cost = ETA × Acuity Weight
    - Stewardship Penalty = Sum of scarcity penalties for unused capabilities
    - Capability Penalty = 10,000 per missing required capability
    """

    # ========================================================================
    # ACUITY WEIGHTS (Neural Component)
    # ========================================================================
    # Higher weight = higher priority = more sensitive to distance/time
    # These weights multiply the ETA to create time cost

    ACUITY_WEIGHTS: Dict[str, int] = {
        "Dead": 0,          # No transport needed
        "Expectant": 80,    # High priority but resource-limited survival
        "Immediate": 100,   # Highest priority - life-threatening
        "Delayed": 50,      # Moderate priority - serious but stable
        "Minimal": 10,      # Low priority - minor injuries
        "Undefined": 10,    # Default to low priority if not triaged
    }

    # ========================================================================
    # SCARCITY PENALTIES (Resource Stewardship)
    # ========================================================================
    # Penalty for assigning a patient to a facility with specialized capabilities
    # they don't need. This prevents "wasting" scarce resources.
    #
    # Example: Don't send a broken arm patient to a burn unit if a general
    # hospital is available - save the burn unit for burn victims.
    #
    # Higher penalty = more scarce = preserve for patients who truly need it

    SCARCITY_PENALTIES: Dict[str, int] = {
        "burn": 500,              # Burn units are very scarce
        "pediatric": 500,         # Pediatric facilities are scarce
        "obstetric": 500,         # Obstetric facilities are scarce
        "neurosurgical": 400,     # Neurosurgery is highly specialized
        "cardiac": 300,           # Cardiac surgery is specialized
        "hepatobiliary": 300,     # Hepatobiliary surgery is specialized
        "thoracic": 200,          # Thoracic surgery is moderately specialized
        "vascular": 200,          # Vascular surgery is moderately specialized
        "ophthalmology": 100,     # Ophthalmology is somewhat specialized
        "ent": 100,               # ENT is somewhat specialized
        "trauma_center": 0,       # Trauma centers are general-purpose
        "orthopedic": 0,          # Orthopedics is common
    }

    # ========================================================================
    # CAPABILITY MISMATCH PENALTY (Hard Constraint)
    # ========================================================================
    # Penalty for assigning a patient to a facility that LACKS a required capability
    # This is a very high penalty to strongly discourage (but not forbid) such assignments

    CAPABILITY_MISMATCH_PENALTY: int = 10000

    # ========================================================================
    # RESOURCE DEFICIT PENALTY (Soft Constraint)
    # ========================================================================
    # Penalty for assigning a patient to a facility that doesn't have enough resources
    # This is lower than capability mismatch because resources can sometimes be stretched

    RESOURCE_DEFICIT_PENALTY: int = 5000

    # ========================================================================
    # TRANSPORT SPEEDS
    # ========================================================================
    # Used to calculate ETA from distance

    GROUND_TRANSPORT_SPEED_KMH: float = 50.0      # Ambulance
    AIR_TRANSPORT_SPEED_KMH: float = 200.0        # Helicopter

    # ========================================================================
    # NATO TIMELINE CONSTRAINTS (MEDEVAC only)
    # ========================================================================
    # These are hard constraints for MEDEVAC evacuation chains

    NATO_INITIAL_AID_MINUTES: int = 10    # Initial aid at point of injury
    NATO_ROLE1_MINUTES: int = 60          # Role 1 (Level 3) - Golden Hour
    NATO_ROLE2_MINUTES: int = 120         # Role 2 (Level 2) - Damage Control

    # ========================================================================
    # ALTERNATIVE FACILITIES
    # ========================================================================
    # Number of alternative facilities to find for each patient

    MAX_ALTERNATIVES: int = 3

    # ========================================================================
    # MANAGED CAPABILITIES
    # ========================================================================
    # List of all capabilities that the solver should consider
    # These are checked for capability matching and stewardship

    MANAGED_CAPABILITIES = [
        "trauma_center",
        "neurosurgical",
        "orthopedic",
        "ophthalmology",
        "burn",
        "pediatric",
        "obstetric",
        "cardiac",
        "thoracic",
        "vascular",
        "ent",
        "hepatobiliary",
    ]

    # ========================================================================
    # MANAGED RESOURCES
    # ========================================================================
    # List of all resources that the solver should track for capacity constraints

    MANAGED_RESOURCES = [
        "ward",
        "ordinary_icu",
        "operating_room",
        "ventilator",
        "prbc_unit",
        "isolation",
        "decontamination_unit",
        "ct_scanner",
        "oxygen_cylinder",
        "interventional_radiology",
    ]

    # ========================================================================
    # RESOURCE STRESS CALCULATION
    # ========================================================================
    # Parameters for calculating resource stress penalty
    # Stress increases exponentially as utilization approaches 100%

    RESOURCE_STRESS_MULTIPLIER: float = 100.0  # Base multiplier for stress calculation
    RESOURCE_STRESS_EXPONENT: float = 2.0      # Exponent for utilization rate (quadratic by default)

    @classmethod
    def get_acuity_weight(cls, acuity: str) -> int:
        """Get the priority weight for a given acuity level."""
        return cls.ACUITY_WEIGHTS.get(acuity, 10)

    @classmethod
    def get_scarcity_penalty(cls, capability: str) -> int:
        """Get the scarcity penalty for a given capability."""
        return cls.SCARCITY_PENALTIES.get(capability, 0)

    @classmethod
    def calculate_resource_stress(
        cls, required_qty: int, available_qty: int
    ) -> float:
        """
        Calculate resource stress penalty.

        Args:
            required_qty: Amount of resource required by patient
            available_qty: Amount of resource available at facility

        Returns:
            Stress penalty (higher when facility is near capacity)
        """
        if available_qty <= 0:
            return cls.RESOURCE_DEFICIT_PENALTY

        utilization_rate = required_qty / available_qty
        stress = (utilization_rate ** cls.RESOURCE_STRESS_EXPONENT) * cls.RESOURCE_STRESS_MULTIPLIER
        return stress


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Adjusting Priority for Immediate Patients
-----------------------------------------------------
If you want to make Immediate patients even higher priority:

    ACUITY_WEIGHTS = {
        "Immediate": 150,  # Increased from 100
        ...
    }

This will make the solver more aggressive about minimizing transport time
for Immediate patients, even if it means using scarce resources.


Example 2: Making Burn Units More Scarce
-----------------------------------------
If burn units are extremely limited in your region:

    SCARCITY_PENALTIES = {
        "burn": 1000,  # Increased from 500
        ...
    }

This will make the solver much more reluctant to assign non-burn patients
to burn units, preserving them for burn victims.


Example 3: Relaxing Capability Requirements
--------------------------------------------
If you want to allow more flexibility in capability matching:

    CAPABILITY_MISMATCH_PENALTY = 5000  # Reduced from 10000

This makes the solver more willing to assign patients to facilities that
don't have all required capabilities (e.g., in resource-constrained scenarios).


Example 4: Adjusting Transport Speeds
--------------------------------------
If your region has faster ambulances or slower helicopters:

    GROUND_TRANSPORT_SPEED_KMH = 60.0  # Increased from 50.0
    AIR_TRANSPORT_SPEED_KMH = 180.0    # Decreased from 200.0


Example 5: Custom Resource Stress
----------------------------------
If you want resource stress to increase more gradually:

    RESOURCE_STRESS_EXPONENT = 1.5  # Reduced from 2.0 (less aggressive)

Or more aggressively:

    RESOURCE_STRESS_EXPONENT = 3.0  # Increased from 2.0 (more aggressive)
"""
