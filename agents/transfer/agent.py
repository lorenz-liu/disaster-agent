"""
Transfer Agent - NATO MEDEVAC Evacuation Chain Decision Engine

Implements NATO medical doctrine (AJP-4.10) for MEDEVAC operations,
creating evacuation chains that follow the Role 1 → Role 2 → Role 3 progression
with strict adherence to the 10-1-2 timeline (Golden Hour and Damage Control).

Uses OR-Tools constraint optimization for single-destination assignments (MCI/PHE).
"""

import time
from typing import Dict, List, Optional, Tuple
from schemas import PatientType, HealthcareFacilityType
from schemas.enums import HealthcareFacilityLevelEnum, IncidentTypeEnum, PatientSeverityEnum
from .rules import OptimizationRules
from .solver import TransferOptimizer
from .reasoning import TransferReasoningGenerator


class TransferAgent:
    """
    Implements NATO AJP-4.10 MEDEVAC doctrine using neuro-symbolic optimization.

    The agent creates evacuation chains following the medical echelon system:
    - Role 1 (Level 3): Initial stabilization and triage
    - Role 2 (Level 2): Advanced trauma care
    - Role 3 (Level 1): Definitive surgical care
    """

    def __init__(
        self,
        patient: PatientType,
        facilities: List[HealthcareFacilityType],
        incident_type: str = "MCI",
        current_time: Optional[float] = None,
        enable_reasoning: bool = True,
        reasoning_config: Optional[Dict] = None,
    ):
        """
        Initialize the transfer agent.

        Args:
            patient: Triaged patient requiring transfer
            facilities: List of available healthcare facilities
            incident_type: Type of incident ("MCI", "MEDEVAC", "PHE")
            current_time: Current timestamp (defaults to time.time())
            enable_reasoning: Whether to generate detailed LLM-based reasoning
            reasoning_config: Optional config for reasoning generator (api_key, model, etc.)
        """
        self.patient = patient
        self.facilities = facilities
        self.incident_type = incident_type
        self.current_time = current_time or time.time()
        self.rules = OptimizationRules
        self.enable_reasoning = enable_reasoning

        # Initialize reasoning generator if enabled
        self.reasoning_generator = None
        if enable_reasoning:
            try:
                config = reasoning_config or {}
                self.reasoning_generator = TransferReasoningGenerator(**config)
            except Exception as e:
                print(f"Warning: Failed to initialize reasoning generator: {e}")
                self.enable_reasoning = False

        # Transport speeds (from rules)
        self.traffic_speed_kmh = self.rules.GROUND_TRANSPORT_SPEED_KMH
        self.helicopter_speed_kmh = self.rules.AIR_TRANSPORT_SPEED_KMH

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.

        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _calculate_eta(
        self,
        from_lat: float,
        from_lon: float,
        to_facility: HealthcareFacilityType,
        use_helicopter: bool = False,
    ) -> float:
        """
        Calculate ETA in minutes based on transport mode.

        Args:
            from_lat: Starting latitude
            from_lon: Starting longitude
            to_facility: Destination facility
            use_helicopter: Whether to use helicopter transport

        Returns:
            ETA in minutes
        """
        if not to_facility.location:
            return float("inf")

        dist_km = self._calculate_distance(
            from_lat, from_lon,
            to_facility.location.latitude,
            to_facility.location.longitude
        )
        speed = self.helicopter_speed_kmh if use_helicopter else self.traffic_speed_kmh
        return (dist_km / speed) * 60

    def _get_patient_weight(self) -> int:
        """Get neural priority weight based on acuity."""
        return self.rules.get_acuity_weight(self.patient.acuity)

    def _calculate_slack_time(self) -> float:
        """
        Calculate slack time (survival window) in minutes.

        Returns:
            Remaining time before predicted death (negative if already expired)
        """
        if not self.patient.predicted_death_timestamp:
            # No predicted death, assume large survival window
            return 24 * 60  # 24 hours

        return (self.patient.predicted_death_timestamp - self.current_time) / 60.0

    def _check_capability_match(
        self, facility: HealthcareFacilityType
    ) -> Tuple[bool, int]:
        """
        Check if facility has required capabilities.

        Returns:
            Tuple of (is_match, penalty_score)
        """
        penalty = 0
        is_match = True

        if not self.patient.required_medical_capabilities or not facility.capabilities:
            return True, 0

        for cap_name, required in self.patient.required_medical_capabilities.model_dump().items():
            if required:
                facility_caps = facility.capabilities.model_dump()
                facility_has = facility_caps.get(cap_name, False)
                if not facility_has:
                    # Missing required capability - heavy penalty
                    penalty += 10000
                    is_match = False

        return is_match, penalty

    def _check_resource_availability(
        self, facility: HealthcareFacilityType
    ) -> Tuple[bool, Dict]:
        """
        Check if facility has sufficient resources.

        Returns:
            Tuple of (has_resources, deficit_dict)
        """
        deficit = {}
        has_all = True

        if not self.patient.required_medical_resources or not facility.medical_resources:
            return True, {}

        patient_resources = self.patient.required_medical_resources.model_dump()
        facility_resources = facility.medical_resources.model_dump()

        for res_name, required_qty in patient_resources.items():
            if required_qty and required_qty > 0:
                available = facility_resources.get(res_name, 0) or 0
                if available < required_qty:
                    deficit[res_name] = required_qty - available
                    has_all = False

        return has_all, deficit

    def _calculate_resource_stress(self, facility: HealthcareFacilityType) -> float:
        """
        Calculate resource stress penalty.

        Higher penalty when facility resources are near depletion.
        """
        stress = 0.0

        if not self.patient.required_medical_resources or not facility.medical_resources:
            return 0.0

        patient_resources = self.patient.required_medical_resources.model_dump()
        facility_resources = facility.medical_resources.model_dump()

        for res_name, required_qty in patient_resources.items():
            if required_qty and required_qty > 0:
                available = facility_resources.get(res_name, 0) or 0
                if available > 0:
                    utilization_rate = required_qty / available
                    # Exponential penalty as utilization approaches 100%
                    stress += utilization_rate ** 2 * 100

        return stress

    def _filter_facilities_by_level(
        self, level: HealthcareFacilityLevelEnum
    ) -> List[HealthcareFacilityType]:
        """Filter facilities by healthcare level."""
        return [f for f in self.facilities if f.level == level.value]

    def _find_best_facility(
        self,
        facilities: List[HealthcareFacilityType],
        from_lat: float,
        from_lon: float,
        time_budget: float,
    ) -> Tuple[Optional[HealthcareFacilityType], float]:
        """
        Find best facility within time budget using optimization.

        Returns:
            Tuple of (best_facility, eta) or (None, 0) if none viable
        """
        if not facilities:
            return None, 0.0

        best_facility = None
        best_score = float("inf")
        best_eta = 0.0

        patient_weight = self._get_patient_weight()

        for facility in facilities:
            # Calculate ETA
            eta = self._calculate_eta(from_lat, from_lon, facility, use_helicopter=False)

            # Check time budget
            if eta > time_budget:
                continue

            # Check capability match
            is_capable, capability_penalty = self._check_capability_match(facility)

            # Check resource availability
            has_resources, deficit = self._check_resource_availability(facility)

            # Calculate resource stress
            resource_stress = self._calculate_resource_stress(facility)

            # Get acuity-level score
            acuity_level_score = self.rules.get_acuity_level_score(self.patient.acuity, facility.level)

            # Calculate total cost
            # Note: We subtract the score because positive scores should reduce cost
            time_cost = eta * patient_weight
            total_cost = time_cost + capability_penalty + resource_stress - acuity_level_score

            # Add penalty for resource deficit
            if not has_resources:
                total_cost += 5000

            if total_cost < best_score:
                best_score = total_cost
                best_facility = facility
                best_eta = eta

        return best_facility, best_eta

    def decide_transfer(self) -> Dict:
        """
        Main decision entry point.

        Returns:
            Decision dictionary with action, reasoning, and evacuation chain/destination
        """
        slack_time = self._calculate_slack_time()

        # Check if patient is already deceased or unsalvageable
        if slack_time <= 0 or self.patient.acuity == "Dead":
            return {
                "action": "Forfeit",
                "reasoning": "Patient has deceased or survival window expired",
                "reasoning_code": "PATIENT_DECEASED",
                "evacuation_chain": [],
            }

        # For MEDEVAC, build sequential chain
        if self.incident_type == IncidentTypeEnum.MEDICAL_EVACUATION.value:
            return self._build_medevac_chain(slack_time)
        else:
            # For MCI/PHE, use single destination
            return self._build_single_destination(slack_time)

    def _build_medevac_chain(self, slack_time: float) -> Dict:
        """
        Build MEDEVAC evacuation chain following NATO doctrine.

        Chain progression:
        1. Role 1 (Level 3): Initial stabilization - must reach within 60 min
        2. Role 2 (Level 2): Advanced trauma care - must reach within 120 min total
        3. Role 3 (Level 1): Definitive care - final destination
        """
        if not self.patient.location:
            return {
                "action": "Forfeit",
                "reasoning": "Patient location unknown",
                "reasoning_code": "NO_LOCATION",
                "evacuation_chain": [],
            }

        chain = []
        current_lat = self.patient.location.latitude
        current_lon = self.patient.location.longitude
        cumulative_time = 0.0

        # Step 1: Find Role 1 (Level 3) facility - Initial stabilization
        level3_facilities = self._filter_facilities_by_level(HealthcareFacilityLevelEnum.THREE)

        if level3_facilities:
            role1_facility, role1_eta = self._find_best_facility(
                level3_facilities, current_lat, current_lon, self.rules.NATO_ROLE1_MINUTES - cumulative_time
            )

            if role1_facility:
                cumulative_time += role1_eta
                chain.append({
                    "role": "Role 1",
                    "level": 3,
                    "facility_id": role1_facility.facility_id,
                    "facility_name": role1_facility.name,
                    "eta_minutes": role1_eta,
                    "cumulative_time": cumulative_time,
                    "timeline_compliance": cumulative_time <= self.rules.NATO_ROLE1_MINUTES,
                })
                if role1_facility.location:
                    current_lat = role1_facility.location.latitude
                    current_lon = role1_facility.location.longitude

        # Step 2: Find Role 2 (Level 2) facility - Advanced trauma care
        level2_facilities = self._filter_facilities_by_level(HealthcareFacilityLevelEnum.TWO)

        if level2_facilities:
            role2_facility, role2_eta = self._find_best_facility(
                level2_facilities, current_lat, current_lon, self.rules.NATO_ROLE2_MINUTES - cumulative_time
            )

            if role2_facility:
                cumulative_time += role2_eta
                chain.append({
                    "role": "Role 2",
                    "level": 2,
                    "facility_id": role2_facility.facility_id,
                    "facility_name": role2_facility.name,
                    "eta_minutes": role2_eta,
                    "cumulative_time": cumulative_time,
                    "timeline_compliance": cumulative_time <= self.rules.NATO_ROLE2_MINUTES,
                })
                if role2_facility.location:
                    current_lat = role2_facility.location.latitude
                    current_lon = role2_facility.location.longitude

        # Step 3: Find Role 3 (Level 1) facility - Definitive care
        level1_facilities = self._filter_facilities_by_level(HealthcareFacilityLevelEnum.ONE)

        if level1_facilities:
            role3_facility, role3_eta = self._find_best_facility(
                level1_facilities, current_lat, current_lon, slack_time - cumulative_time
            )

            if role3_facility:
                cumulative_time += role3_eta
                chain.append({
                    "role": "Role 3",
                    "level": 1,
                    "facility_id": role3_facility.facility_id,
                    "facility_name": role3_facility.name,
                    "eta_minutes": role3_eta,
                    "cumulative_time": cumulative_time,
                    "timeline_compliance": cumulative_time <= slack_time,
                })

        # Validate chain
        if not chain:
            return {
                "action": "Forfeit",
                "reasoning": "Unable to construct viable evacuation chain within survival window",
                "reasoning_code": "NO_VIABLE_CHAIN",
                "evacuation_chain": [],
            }

        # Check if patient will survive to final destination
        if cumulative_time > slack_time:
            return {
                "action": "Forfeit",
                "reasoning": f"Patient will not survive evacuation chain (requires {cumulative_time:.1f} min, survival window: {slack_time:.1f} min)",
                "reasoning_code": "DEAD_ON_ARRIVAL",
                "evacuation_chain": chain,
            }

        return {
            "action": "Transfer",
            "reasoning": f"NATO-compliant evacuation chain constructed ({len(chain)} facilities, total time: {cumulative_time:.1f} min)",
            "reasoning_code": "EVACUATION_CHAIN_OPTIMAL",
            "evacuation_chain": chain,
            "total_time_minutes": cumulative_time,
            "survival_window_minutes": slack_time,
            "nato_compliance": {
                "role1_compliant": any(f["role"] == "Role 1" and f["timeline_compliance"] for f in chain),
                "role2_compliant": any(f["role"] == "Role 2" and f["timeline_compliance"] for f in chain),
                "survival_compliant": cumulative_time <= slack_time,
            },
        }

    def _build_single_destination(self, slack_time: float) -> Dict:
        """
        Build single destination decision for MCI/PHE incidents using OR-Tools optimization.

        Uses constraint-based optimization to find the best facility considering:
        - Time cost (ETA × acuity weight)
        - Capability matching
        - Resource availability
        - Resource stewardship (don't waste scarce capabilities)
        """
        if not self.patient.location:
            return {
                "action": "Forfeit",
                "reasoning": "Patient location unknown",
                "reasoning_code": "NO_LOCATION",
                "destination": None,
            }

        # Use OR-Tools optimizer for single-destination assignment
        optimizer = TransferOptimizer(
            patients=[self.patient],
            facilities=self.facilities,
            current_time=self.current_time,
        )

        results = optimizer.solve()
        decision = results.get(self.patient.patient_id)

        if not decision:
            return {
                "action": "Forfeit",
                "reasoning": "No suitable facility available",
                "reasoning_code": "NO_FACILITIES_AVAILABLE",
                "destination": None,
            }

        if decision["action"] == "Forfeit":
            return {
                "action": "Forfeit",
                "reasoning": f"Patient cannot be transferred ({decision['reasoning_code']})",
                "reasoning_code": decision["reasoning_code"],
                "destination": None,
            }

        # Find the destination facility object
        destination_facility = None
        for facility in self.facilities:
            if facility.facility_id == decision["destination_id"]:
                destination_facility = facility
                break

        # Generate detailed reasoning if enabled
        detailed_reasoning = f"Optimal facility selected using constraint optimization (ETA: {decision['eta_minutes']:.1f} min)"

        if self.enable_reasoning and self.reasoning_generator and destination_facility:
            try:
                # Calculate distance for reasoning
                distance_km = self._calculate_distance(
                    self.patient.location.latitude,
                    self.patient.location.longitude,
                    destination_facility.location.latitude,
                    destination_facility.location.longitude
                )

                detailed_reasoning = self.reasoning_generator.generate_reasoning(
                    patient=self.patient,
                    destination=destination_facility,
                    destination_eta=decision["eta_minutes"],
                    destination_distance=distance_km,
                    alternatives=decision.get("alternatives", []),
                    incident_type=self.incident_type,
                    solver_status=decision.get("solver_status", "OPTIMAL"),
                )
            except Exception as e:
                print(f"Warning: Failed to generate detailed reasoning: {e}")
                # Fall back to simple reasoning

        # Build destination response
        return {
            "action": "Transfer",
            "reasoning": detailed_reasoning,
            "reasoning_code": decision["reasoning_code"],
            "destination": {
                "facility_id": decision["destination_id"],
                "facility_name": decision["destination_name"],
                "eta_minutes": decision["eta_minutes"],
            },
            "alternatives": decision.get("alternatives", []),
            "solver_status": decision.get("solver_status"),
        }
