"""
Post-processors for calculating derived fields and applying medical logic.
Modify these to adjust how derived values are calculated.
"""

from typing import Dict, Any
import time
import uuid


class PostProcessor:
    """Base class for post-processors."""

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process patient data and return modified version.

        Args:
            data: Patient data dictionary

        Returns:
            Modified patient data dictionary
        """
        raise NotImplementedError


class GCSCalculator(PostProcessor):
    """Calculate GCS total score from components if missing."""

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        consciousness = data.get("consciousness")

        # Skip if consciousness is None
        if consciousness is None:
            return data

        eye = consciousness.get("eye_response")
        verbal = consciousness.get("verbal_response")
        motor = consciousness.get("motor_response")
        total = consciousness.get("total_score")

        # If total is missing but components are present, calculate it
        if total is None and all(x is not None for x in [eye, verbal, motor]):
            consciousness["total_score"] = eye + verbal + motor
            data["consciousness"] = consciousness

        return data


class AcuityDetermination(PostProcessor):
    """
    Determine or validate acuity based on SALT triage protocol.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # If already marked as deceased, set to Dead
        if data.get("deceased", False):
            data["acuity"] = "Dead"
            return data

        salt_assessment = data.get("salt_assessment")
        vital_signs = data.get("vital_signs")
        consciousness = data.get("consciousness")
        injuries = data.get("injuries")

        # If LLM already set acuity and it's not Undefined, trust it
        current_acuity = data.get("acuity")
        if current_acuity not in [None, "Undefined"]:
            return data

        # Try to determine acuity using SALT logic
        if salt_assessment is not None:
            # SALT Sort Phase
            can_walk = salt_assessment.get("can_walk")
            can_wave = salt_assessment.get("can_wave")

            # SALT Assess Phase
            has_pulse = salt_assessment.get("has_peripheral_pulse")
            in_distress = salt_assessment.get("in_respiratory_distress")
            hemorrhage_controlled = salt_assessment.get("hemorrhage_controlled")
            obeys_commands = salt_assessment.get("obeys_commands")

            # Determine category based on SALT
            if can_walk is True:
                # Walkers are typically Minimal
                suggested_acuity = "Minimal"
            elif can_walk is False and can_wave is True:
                # Wavers are typically Delayed
                suggested_acuity = "Delayed"
            elif has_pulse is False:
                # No pulse → likely Dead or Immediate depending on salvageability
                suggested_acuity = "Immediate"  # Assume salvageable unless stated otherwise
            elif in_distress is True or hemorrhage_controlled is False:
                # Fails assessment → Immediate
                suggested_acuity = "Immediate"
            elif obeys_commands is False:
                # Doesn't follow commands → Immediate
                suggested_acuity = "Immediate"
            else:
                # Passes all assessments but check for serious injuries
                has_serious_injury = False
                if injuries is not None:
                    has_serious_injury = any(
                        injury.get("severity") in ["Immediate", "Delayed"] for injury in injuries
                    )

                if has_serious_injury:
                    suggested_acuity = "Delayed"
                else:
                    suggested_acuity = "Minimal"

            data["acuity"] = suggested_acuity
            return data

        # Fallback: Use vital signs if SALT assessment not available
        if vital_signs is None and consciousness is None and injuries is None:
            return data

        # Critical indicators (fallback logic)
        critical_indicators = []

        if vital_signs is not None:
            rr = vital_signs.get("respiratory_rate")
            if rr is not None and (rr < 10 or rr > 29):
                critical_indicators.append("abnormal_respiratory_rate")

            spo2 = vital_signs.get("oxygen_saturation")
            if spo2 is not None and spo2 < 90:
                critical_indicators.append("low_oxygen_saturation")

            bp = vital_signs.get("blood_pressure")
            if bp is not None:
                systolic = bp.get("systolic")
                if systolic is not None and systolic < 90:
                    critical_indicators.append("hypotension")

            hr = vital_signs.get("heart_rate")
            if hr is not None and (hr < 50 or hr > 120):
                critical_indicators.append("abnormal_heart_rate")

        if consciousness is not None:
            gcs_total = consciousness.get("total_score")
            if gcs_total is not None and gcs_total < 13:
                critical_indicators.append("altered_consciousness")

        has_critical_injury = False
        has_severe_injury = False
        if injuries is not None:
            has_critical_injury = any(
                injury.get("severity") in ["Immediate", "Dead"] for injury in injuries
            )
            has_severe_injury = any(
                injury.get("severity") == "Delayed" for injury in injuries
            )

        # Map to SALT categories
        if len(critical_indicators) >= 2 or has_critical_injury:
            suggested_acuity = "Immediate"
        elif len(critical_indicators) >= 1 or has_severe_injury:
            suggested_acuity = "Delayed"
        else:
            suggested_acuity = "Minimal"

        data["acuity"] = suggested_acuity
        return data


class MortalityPredictor(PostProcessor):
    """
    Predict mortality risk and set predicted_death_timestamp based on SALT category.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # If already deceased (Dead), set timestamp to current time
        if data.get("deceased", False):
            data["predicted_death_timestamp"] = int(time.time())
            return data

        acuity = data.get("acuity")
        vital_signs = data.get("vital_signs")
        consciousness = data.get("consciousness")

        # Calculate risk score
        risk_score = 0

        # SALT category-based risk
        if acuity == "Dead":
            # Already dead
            data["predicted_death_timestamp"] = int(time.time())
            data["deceased"] = True
            return data
        elif acuity == "Expectant":
            # Expectant - high mortality risk
            risk_score += 5
        elif acuity == "Immediate":
            # Immediate - moderate mortality risk without treatment
            risk_score += 3
        elif acuity == "Delayed":
            # Delayed - low mortality risk
            risk_score += 1
        elif acuity == "Minimal":
            # Minimal - very low mortality risk
            risk_score += 0

        # Additional risk factors from vital signs
        if vital_signs is not None:
            bp = vital_signs.get("blood_pressure")
            if bp is not None:
                systolic = bp.get("systolic")
                if systolic is not None and systolic < 70:
                    risk_score += 2

            spo2 = vital_signs.get("oxygen_saturation")
            if spo2 is not None and spo2 < 80:
                risk_score += 2

        # Additional risk from consciousness
        if consciousness is not None:
            gcs_total = consciousness.get("total_score")
            if gcs_total is not None and gcs_total <= 8:
                risk_score += 2

        # Predict death timestamp based on risk score
        if risk_score >= 5:
            # High risk: predict death in 1-2 hours
            data["predicted_death_timestamp"] = int(time.time() + 3600 + 3600)
        elif risk_score >= 3:
            # Moderate risk: predict death in 4-6 hours
            data["predicted_death_timestamp"] = int(time.time() + 14400 + 7200)
        else:
            # Low risk: no predicted death
            data["predicted_death_timestamp"] = None

        return data


class ResourceEstimator(PostProcessor):
    """
    Adjust resource requirements based on SALT category and injuries.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        acuity = data.get("acuity")
        injuries = data.get("injuries")
        resources = data.get("required_medical_resources")

        # Skip if no resources to adjust
        if resources is None:
            return data

        # SALT category-based resource allocation
        if acuity == "Immediate":
            # Immediate - needs ICU and likely surgery
            resources["ordinary_icu"] = max(resources.get("ordinary_icu") or 0, 1)
            resources["ventilator"] = max(resources.get("ventilator") or 0, 1)
            resources["operating_room"] = max(resources.get("operating_room") or 0, 1)
        elif acuity == "Expectant":
            # Expectant - comfort care, minimal resources
            resources["ward"] = max(resources.get("ward") or 0, 1)
        elif acuity == "Delayed":
            # Delayed - needs ward bed, possible surgery later
            resources["ward"] = max(resources.get("ward") or 0, 1)
        elif acuity == "Minimal":
            # Minimal - outpatient or minimal ward
            resources["ward"] = max(resources.get("ward") or 0, 1)

        # Check if any injury requires surgery
        if injuries is not None:
            needs_surgery = any(
                injury.get("severity") in ["Immediate", "Delayed"] for injury in injuries
            )
            if needs_surgery:
                resources["operating_room"] = max(resources.get("operating_room") or 0, 1)

        data["required_medical_resources"] = resources
        return data


class DefaultValueFiller(PostProcessor):
    """Fill in minimal default values for missing fields."""

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Generate patient_id if missing
        if "patient_id" not in data or data["patient_id"] is None:
            data["patient_id"] = str(uuid.uuid4())

        # Set default status if missing
        if "status" not in data or data["status"] is None:
            data["status"] = "Unassigned"

        # Set default action_logs if missing
        if "action_logs" not in data:
            data["action_logs"] = []

        # Set default name if missing
        if "name" not in data or data["name"] is None:
            data["name"] = "Unknown"

        # Set default deceased if missing
        if "deceased" not in data or data["deceased"] is None:
            data["deceased"] = False

        # Set default assigned_facility if missing
        if "assigned_facility" not in data:
            data["assigned_facility"] = None

        # Convert empty strings to None for assigned_facility
        if data.get("assigned_facility") == "":
            data["assigned_facility"] = None

        # Convert 0 to None for predicted_death_timestamp
        if data.get("predicted_death_timestamp") == 0:
            data["predicted_death_timestamp"] = None

        return data


class InjuryNormalizer(PostProcessor):
    """Normalize injury data to ensure locations and mechanisms are arrays."""

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        injuries = data.get("injuries")

        if injuries is None:
            return data

        # Normalize each injury
        for injury in injuries:
            # Convert locations to array if it's a string
            if "locations" in injury and isinstance(injury["locations"], str):
                injury["locations"] = [injury["locations"]]

            # Convert mechanisms to array if it's a string
            if "mechanisms" in injury and isinstance(injury["mechanisms"], str):
                injury["mechanisms"] = [injury["mechanisms"]]

        data["injuries"] = injuries
        return data


# Registry of post-processors (order matters!)
POST_PROCESSORS = [
    DefaultValueFiller(),  # Fill defaults first
    InjuryNormalizer(),  # Normalize injury arrays
    GCSCalculator(),  # Calculate GCS
    AcuityDetermination(),  # Determine acuity
    MortalityPredictor(),  # Predict mortality
    ResourceEstimator(),  # Adjust resources
]


def post_process_patient_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all post-processors on patient data.

    Args:
        data: Patient data dictionary

    Returns:
        Post-processed patient data dictionary
    """
    for processor in POST_PROCESSORS:
        data = processor.process(data)

    return data
