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
    Determine or validate acuity based on vital signs and injuries.
    Uses START triage principles.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # If already marked as deceased, keep it
        if data.get("deceased", False):
            data["acuity"] = "Deceased"
            return data

        vital_signs = data.get("vital_signs")
        consciousness = data.get("consciousness")
        injuries = data.get("injuries")

        # Skip if not enough data to determine acuity
        if vital_signs is None and consciousness is None and injuries is None:
            return data

        # Critical indicators
        critical_indicators = []

        # Check vital signs if available
        if vital_signs is not None:
            # Respiratory rate
            rr = vital_signs.get("respiratory_rate")
            if rr is not None:
                if rr < 10 or rr > 29:
                    critical_indicators.append("abnormal_respiratory_rate")

            # Oxygen saturation
            spo2 = vital_signs.get("oxygen_saturation")
            if spo2 is not None and spo2 < 90:
                critical_indicators.append("low_oxygen_saturation")

            # Blood pressure (hypotension)
            bp = vital_signs.get("blood_pressure")
            if bp is not None:
                systolic = bp.get("systolic")
                if systolic is not None and systolic < 90:
                    critical_indicators.append("hypotension")

            # Heart rate
            hr = vital_signs.get("heart_rate")
            if hr is not None:
                if hr < 50 or hr > 120:
                    critical_indicators.append("abnormal_heart_rate")

        # Check GCS if available
        if consciousness is not None:
            gcs_total = consciousness.get("total_score")
            if gcs_total is not None and gcs_total < 13:
                critical_indicators.append("altered_consciousness")

        # Check injury severity if available
        has_critical_injury = False
        has_severe_injury = False
        if injuries is not None:
            has_critical_injury = any(
                injury.get("severity") == "Critical" for injury in injuries
            )
            has_severe_injury = any(
                injury.get("severity") == "Severe" for injury in injuries
            )

        # Determine acuity
        if len(critical_indicators) >= 2 or has_critical_injury:
            suggested_acuity = "Critical"
        elif len(critical_indicators) >= 1 or has_severe_injury:
            suggested_acuity = "Severe"
        else:
            suggested_acuity = "Minor"

        # If LLM didn't set acuity or set it to "Undefined", use our calculation
        current_acuity = data.get("acuity")
        if current_acuity in [None, "Undefined"]:
            data["acuity"] = suggested_acuity

        return data


class MortalityPredictor(PostProcessor):
    """
    Predict mortality risk and set predicted_death_timestamp.
    Simple rule-based approach.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # If already deceased, set timestamp to current time
        if data.get("deceased", False):
            data["predicted_death_timestamp"] = int(time.time())
            return data

        acuity = data.get("acuity")
        vital_signs = data.get("vital_signs")
        consciousness = data.get("consciousness")

        # Calculate risk score
        risk_score = 0

        # Critical acuity
        if acuity == "Critical":
            risk_score += 3
        elif acuity == "Severe":
            risk_score += 1

        # Check vital signs if available
        if vital_signs is not None:
            # Severe hypotension
            bp = vital_signs.get("blood_pressure")
            if bp is not None:
                systolic = bp.get("systolic")
                if systolic is not None and systolic < 70:
                    risk_score += 2

            # Severe hypoxia
            spo2 = vital_signs.get("oxygen_saturation")
            if spo2 is not None and spo2 < 80:
                risk_score += 2

        # Check consciousness if available
        if consciousness is not None:
            # Very low GCS
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
    Adjust resource requirements based on acuity and injuries.
    """

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        acuity = data.get("acuity")
        injuries = data.get("injuries")
        resources = data.get("required_medical_resources")

        # Skip if no resources to adjust
        if resources is None:
            return data

        # Ensure critical patients get ICU
        if acuity == "Critical":
            resources["ordinary_icu"] = max(resources.get("ordinary_icu") or 0, 1)
            resources["ventilator"] = max(resources.get("ventilator") or 0, 1)

        # Ensure severe patients get ward bed
        if acuity in ["Critical", "Severe"]:
            resources["ward"] = max(resources.get("ward") or 0, 1)

        # Check if any injury requires surgery
        if injuries is not None:
            needs_surgery = any(
                injury.get("severity") in ["Critical", "Severe"] for injury in injuries
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

        return data


# Registry of post-processors (order matters!)
POST_PROCESSORS = [
    DefaultValueFiller(),  # Fill defaults first
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
