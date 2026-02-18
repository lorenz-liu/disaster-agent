"""
OR-Tools Constraint-Based Optimizer for Transfer Decisions

This module implements the constraint optimization solver using Google OR-Tools.
It handles single-destination assignments for MCI/PHE incidents.
"""

from typing import Dict, List, Optional, Tuple
from ortools.linear_solver import pywraplp

from schemas import PatientType, HealthcareFacilityType
from .rules import OptimizationRules


class TransferOptimizer:
    """
    Constraint-based optimizer using OR-Tools for patient-facility assignment.

    Minimizes:
        Total Cost = (Time Cost) + (Stewardship Penalty) + (Capability Penalty)

    Subject to:
        - Each patient assigned to exactly 1 facility
        - Resource capacity constraints (soft)
        - Survival window constraints (hard)
    """

    def __init__(
        self,
        patients: List[PatientType],
        facilities: List[HealthcareFacilityType],
        current_time: float,
    ):
        """
        Initialize the optimizer.

        Args:
            patients: List of triaged patients
            facilities: List of available facilities
            current_time: Current timestamp
        """
        self.patients = patients
        self.facilities = facilities
        self.current_time = current_time
        self.rules = OptimizationRules

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance using Haversine formula (in km)."""
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
        self, patient: PatientType, facility: HealthcareFacilityType
    ) -> float:
        """
        Calculate ETA in minutes.

        Args:
            patient: Patient with location
            facility: Facility with location

        Returns:
            ETA in minutes
        """
        if not patient.location or not facility.location:
            return float("inf")

        dist_km = self._calculate_distance(
            patient.location.latitude,
            patient.location.longitude,
            facility.location.latitude,
            facility.location.longitude,
        )

        # Use ground transport by default
        speed = self.rules.GROUND_TRANSPORT_SPEED_KMH
        return (dist_km / speed) * 60

    def _calculate_slack_time(self, patient: PatientType) -> float:
        """
        Calculate survival window in minutes.

        Returns:
            Minutes until predicted death (or large value if no prediction)
        """
        if not patient.predicted_death_timestamp:
            return 24 * 60  # 24 hours default

        return (patient.predicted_death_timestamp - self.current_time) / 60.0

    def _setup_solver(
        self,
        active_patients: List[PatientType],
        excluded_assignments: Optional[Dict[str, List[str]]] = None,
    ) -> Tuple:
        """
        Set up the OR-Tools optimization problem.

        Args:
            active_patients: Patients to assign
            excluded_assignments: Dict of patient_id -> [facility_ids to exclude]

        Returns:
            Tuple of (solver, decision_variables, all_pairs)
        """
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            raise RuntimeError("OR-Tools SCIP solver not available")

        # Decision Variables: x[p, f] = 1 if patient p assigned to facility f
        x = {}
        all_pairs = set()

        for p in active_patients:
            for f in self.facilities:
                x[(p.patient_id, f.facility_id)] = solver.IntVar(
                    0, 1, f"x_{p.patient_id}_{f.facility_id}"
                )
                all_pairs.add((p.patient_id, f.facility_id))

        # ====================================================================
        # CONSTRAINT 1: Each patient assigned to EXACTLY 1 facility
        # ====================================================================
        for p in active_patients:
            vars_for_p = [
                x[(p.patient_id, f.facility_id)]
                for f in self.facilities
                if (p.patient_id, f.facility_id) in all_pairs
            ]
            if vars_for_p:
                solver.Add(solver.Sum(vars_for_p) == 1)

        # ====================================================================
        # CONSTRAINT 2: Exclusion constraints (for finding alternatives)
        # ====================================================================
        if excluded_assignments:
            for patient_id, facility_ids in excluded_assignments.items():
                for facility_id in facility_ids:
                    if (patient_id, facility_id) in all_pairs:
                        solver.Add(x[(patient_id, facility_id)] == 0)

        # ====================================================================
        # CONSTRAINT 3: Resource capacity constraints
        # ====================================================================
        for f in self.facilities:
            if not f.medical_resources:
                continue

            facility_resources = f.medical_resources.model_dump()

            for res_name in self.rules.MANAGED_RESOURCES:
                capacity = facility_resources.get(res_name, 0)
                if not capacity or capacity <= 0:
                    continue

                # Sum of all patients assigned here needing this resource
                usage_terms = []
                for p in active_patients:
                    if (p.patient_id, f.facility_id) not in all_pairs:
                        continue

                    if not p.required_medical_resources:
                        continue

                    patient_resources = p.required_medical_resources.model_dump()
                    req_qty = patient_resources.get(res_name, 0) or 0

                    if req_qty > 0:
                        usage_terms.append(
                            x[(p.patient_id, f.facility_id)] * req_qty
                        )

                if usage_terms:
                    solver.Add(solver.Sum(usage_terms) <= capacity)

        # ====================================================================
        # OBJECTIVE FUNCTION: Minimize total cost
        # ====================================================================
        objective = solver.Objective()

        for p in active_patients:
            patient_weight = self.rules.get_acuity_weight(p.acuity)

            for f in self.facilities:
                if (p.patient_id, f.facility_id) not in all_pairs:
                    continue

                # ============================================================
                # TERM 1: Time Cost (weighted by acuity)
                # ============================================================
                eta = self._calculate_eta(p, f)
                time_cost = eta * patient_weight

                # ============================================================
                # TERM 2: Stewardship Penalty (don't waste scarce resources)
                # ============================================================
                stewardship_penalty = 0

                if p.required_medical_capabilities and f.capabilities:
                    patient_caps = p.required_medical_capabilities.model_dump()
                    facility_caps = f.capabilities.model_dump()

                    for cap_name in self.rules.MANAGED_CAPABILITIES:
                        f_has = facility_caps.get(cap_name, False)
                        p_needs = patient_caps.get(cap_name, False)

                        # Facility has it but patient doesn't need it = waste
                        if f_has and not p_needs:
                            penalty = self.rules.get_scarcity_penalty(cap_name)
                            stewardship_penalty += penalty

                # ============================================================
                # TERM 3: Capability Mismatch Penalty (missing required caps)
                # ============================================================
                capability_penalty = 0

                if p.required_medical_capabilities and f.capabilities:
                    patient_caps = p.required_medical_capabilities.model_dump()
                    facility_caps = f.capabilities.model_dump()

                    for cap_name in self.rules.MANAGED_CAPABILITIES:
                        p_needs = patient_caps.get(cap_name, False)
                        f_has = facility_caps.get(cap_name, False)

                        # Patient needs it but facility doesn't have it = bad
                        if p_needs and not f_has:
                            capability_penalty += self.rules.CAPABILITY_MISMATCH_PENALTY

                # ============================================================
                # TERM 4: Resource Stress Penalty (near capacity)
                # ============================================================
                resource_stress = 0

                if p.required_medical_resources and f.medical_resources:
                    patient_resources = p.required_medical_resources.model_dump()
                    facility_resources = f.medical_resources.model_dump()

                    for res_name in self.rules.MANAGED_RESOURCES:
                        req_qty = patient_resources.get(res_name, 0) or 0
                        available = facility_resources.get(res_name, 0) or 0

                        if req_qty > 0 and available > 0:
                            stress = self.rules.calculate_resource_stress(
                                req_qty, available
                            )
                            resource_stress += stress

                # ============================================================
                # TERM 5: Acuity-Level Score (preference for matching acuity to level)
                # ============================================================
                # Positive scores reduce cost (good match)
                # Negative scores increase cost (poor match)
                acuity_level_score = self.rules.get_acuity_level_score(p.acuity, f.level)

                # Total cost for this assignment
                # Note: We subtract the score because positive scores should reduce cost
                total_cost = (
                    time_cost
                    + stewardship_penalty
                    + capability_penalty
                    + resource_stress
                    - acuity_level_score
                )

                objective.SetCoefficient(
                    x[(p.patient_id, f.facility_id)], total_cost
                )

        objective.SetMinimization()

        return solver, x, all_pairs

    def solve(self) -> Dict[str, Dict]:
        """
        Solve the optimization problem.

        Returns:
            Dict mapping patient_id to decision dict with:
                - action: "Transfer" or "Forfeit"
                - destination_id: facility ID (if Transfer)
                - destination_name: facility name (if Transfer)
                - eta_minutes: ETA in minutes (if Transfer)
                - reasoning_code: reason code
                - alternatives: list of alternative facilities
        """
        results = {}

        # ====================================================================
        # PHASE 1: Pre-filter patients who should forfeit
        # ====================================================================
        active_patients = []

        for p in self.patients:
            # Check if deceased
            if p.acuity == "Dead" or p.deceased:
                results[p.patient_id] = {
                    "action": "Forfeit",
                    "reasoning_code": "PATIENT_DECEASED",
                    "destination_id": None,
                    "destination_name": None,
                    "eta_minutes": None,
                    "alternatives": [],
                }
                continue

            # Check survival window
            slack_time = self._calculate_slack_time(p)
            if slack_time <= 0:
                results[p.patient_id] = {
                    "action": "Forfeit",
                    "reasoning_code": "PATIENT_DECEASED",
                    "destination_id": None,
                    "destination_name": None,
                    "eta_minutes": None,
                    "alternatives": [],
                }
                continue

            # Check if patient will survive to ANY facility
            will_survive = False
            for f in self.facilities:
                eta = self._calculate_eta(p, f)
                if eta < slack_time:
                    will_survive = True
                    break

            if not will_survive:
                results[p.patient_id] = {
                    "action": "Forfeit",
                    "reasoning_code": "DEAD_ON_ARRIVAL_ALL_FACILITIES",
                    "destination_id": None,
                    "destination_name": None,
                    "eta_minutes": None,
                    "alternatives": [],
                }
                continue

            active_patients.append(p)

        # If no active patients, return
        if not active_patients:
            return results

        # ====================================================================
        # PHASE 2: Run OR-Tools solver
        # ====================================================================
        solver, x, all_pairs = self._setup_solver(active_patients)
        status = solver.Solve()

        # Map status to human-readable
        status_map = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
            pywraplp.Solver.ABNORMAL: "ABNORMAL",
            pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
        }
        status_name = status_map.get(status, f"UNKNOWN_{status}")

        # ====================================================================
        # PHASE 3: Extract solution or use fallback
        # ====================================================================
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            # Extract optimal assignments
            for p in active_patients:
                assigned_f = None
                for f in self.facilities:
                    if (p.patient_id, f.facility_id) in all_pairs:
                        if x[(p.patient_id, f.facility_id)].solution_value() > 0.5:
                            assigned_f = f
                            break

                if assigned_f:
                    eta = self._calculate_eta(p, assigned_f)
                    alternatives = self._find_alternatives(
                        p, assigned_f, active_patients
                    )

                    results[p.patient_id] = {
                        "action": "Transfer",
                        "reasoning_code": "TRANSFER_OPTIMAL",
                        "destination_id": assigned_f.facility_id,
                        "destination_name": assigned_f.name,
                        "eta_minutes": eta,
                        "alternatives": alternatives,
                        "solver_status": status_name,
                    }
        else:
            # Fallback: greedy assignment
            for p in active_patients:
                best_f = None
                best_cost = float("inf")

                patient_weight = self.rules.get_acuity_weight(p.acuity)

                for f in self.facilities:
                    eta = self._calculate_eta(p, f)
                    cost = eta * patient_weight

                    # Add capability penalty
                    if p.required_medical_capabilities and f.capabilities:
                        patient_caps = p.required_medical_capabilities.model_dump()
                        facility_caps = f.capabilities.model_dump()

                        for cap_name in self.rules.MANAGED_CAPABILITIES:
                            p_needs = patient_caps.get(cap_name, False)
                            f_has = facility_caps.get(cap_name, False)
                            if p_needs and not f_has:
                                cost += self.rules.CAPABILITY_MISMATCH_PENALTY

                    if cost < best_cost:
                        best_cost = cost
                        best_f = f

                if best_f:
                    eta = self._calculate_eta(p, best_f)
                    results[p.patient_id] = {
                        "action": "Transfer",
                        "reasoning_code": "TRANSFER_FALLBACK",
                        "destination_id": best_f.facility_id,
                        "destination_name": best_f.name,
                        "eta_minutes": eta,
                        "alternatives": [],
                        "solver_status": status_name,
                        "fallback_reason": f"Solver returned {status_name}",
                    }

        return results

    def _find_alternatives(
        self,
        patient: PatientType,
        chosen_facility: HealthcareFacilityType,
        active_patients: List[PatientType],
    ) -> List[Dict]:
        """
        Find alternative facilities by re-running solver with exclusions.

        Args:
            patient: Patient to find alternatives for
            chosen_facility: The facility chosen in primary solution
            active_patients: All active patients

        Returns:
            List of up to MAX_ALTERNATIVES alternative facilities
        """
        alternatives = []
        excluded = {patient.patient_id: [chosen_facility.facility_id]}

        for _ in range(self.rules.MAX_ALTERNATIVES):
            try:
                solver, x, all_pairs = self._setup_solver(active_patients, excluded)
                status = solver.Solve()

                if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
                    break

                # Find assignment for this patient
                alt_facility = None
                for f in self.facilities:
                    if (patient.patient_id, f.facility_id) in all_pairs:
                        if x[(patient.patient_id, f.facility_id)].solution_value() > 0.5:
                            alt_facility = f
                            break

                if not alt_facility:
                    break

                eta = self._calculate_eta(patient, alt_facility)
                alternatives.append({
                    "facility_id": alt_facility.facility_id,
                    "facility_name": alt_facility.name,
                    "eta_minutes": eta,
                })

                # Exclude this facility for next iteration
                excluded[patient.patient_id].append(alt_facility.facility_id)

            except Exception:
                # If solver fails, stop looking for alternatives
                break

        return alternatives
