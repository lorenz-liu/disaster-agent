"""
Modular validation rules for patient data.
Add or modify rules here without touching other code.
"""

from typing import Dict, Any, List, Tuple


class ValidationRule:
    """Base class for validation rules."""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate patient data.

        Args:
            data: Patient data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        raise NotImplementedError


class VitalSignsRangeRule(ValidationRule):
    """Validate vital signs are within plausible ranges."""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        vital_signs = data.get("vital_signs")

        # Skip if vital signs is None
        if vital_signs is None:
            return True, []

        # Heart rate: 0-300 bpm (extreme range)
        hr = vital_signs.get("heart_rate")
        if hr is not None and (hr < 0 or hr > 300):
            errors.append(f"Heart rate {hr} is out of plausible range (0-300)")

        # Blood pressure
        bp = vital_signs.get("blood_pressure")
        if bp is not None:
            systolic = bp.get("systolic")
            diastolic = bp.get("diastolic")

            if systolic is not None and (systolic < 0 or systolic > 300):
                errors.append(f"Systolic BP {systolic} is out of plausible range (0-300)")

            if diastolic is not None and (diastolic < 0 or diastolic > 200):
                errors.append(f"Diastolic BP {diastolic} is out of plausible range (0-200)")

            if systolic is not None and diastolic is not None and systolic < diastolic:
                errors.append(f"Systolic BP ({systolic}) cannot be less than diastolic BP ({diastolic})")

        # Respiratory rate: 0-100 breaths/min
        rr = vital_signs.get("respiratory_rate")
        if rr is not None and (rr < 0 or rr > 100):
            errors.append(f"Respiratory rate {rr} is out of plausible range (0-100)")

        # Oxygen saturation: 0-100%
        spo2 = vital_signs.get("oxygen_saturation")
        if spo2 is not None and (spo2 < 0 or spo2 > 100):
            errors.append(f"Oxygen saturation {spo2} is out of plausible range (0-100)")

        # Temperature: 25-45°C
        temp = vital_signs.get("temperature")
        if temp is not None and (temp < 25 or temp > 45):
            errors.append(f"Temperature {temp} is out of plausible range (25-45°C)")

        return len(errors) == 0, errors


class GlasgowComaScaleRule(ValidationRule):
    """Validate Glasgow Coma Scale scores."""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        consciousness = data.get("consciousness")

        # Skip if consciousness is None
        if consciousness is None:
            return True, []

        eye = consciousness.get("eye_response")
        verbal = consciousness.get("verbal_response")
        motor = consciousness.get("motor_response")
        total = consciousness.get("total_score")

        # Validate individual components
        if eye is not None and (eye < 1 or eye > 4):
            errors.append(f"Eye response {eye} must be between 1-4")

        if verbal is not None and (verbal < 1 or verbal > 5):
            errors.append(f"Verbal response {verbal} must be between 1-5")

        if motor is not None and (motor < 1 or motor > 6):
            errors.append(f"Motor response {motor} must be between 1-6")

        # Validate total score
        if total is not None and (total < 3 or total > 15):
            errors.append(f"GCS total score {total} must be between 3-15")

        # Check consistency if all components are present
        if all(x is not None for x in [eye, verbal, motor, total]):
            expected_total = eye + verbal + motor
            if total != expected_total:
                errors.append(
                    f"GCS total score {total} doesn't match sum of components "
                    f"(E{eye} + V{verbal} + M{motor} = {expected_total})"
                )

        return len(errors) == 0, errors


class AgeRangeRule(ValidationRule):
    """Validate age is reasonable."""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        age = data.get("age")

        if age is not None and (age < 0 or age > 120):
            errors.append(f"Age {age} is out of plausible range (0-120)")

        return len(errors) == 0, errors


class DeceasedConsistencyRule(ValidationRule):
    """Validate deceased status is consistent with other fields."""

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        deceased = data.get("deceased", False)
        acuity = data.get("acuity")

        # If deceased, acuity should be "Deceased"
        if deceased and acuity != "Deceased":
            errors.append(f"Patient marked as deceased but acuity is '{acuity}' (should be 'Deceased')")

        # If acuity is "Deceased", deceased should be True
        if acuity == "Deceased" and not deceased:
            errors.append(f"Patient acuity is 'Deceased' but deceased flag is False")

        return len(errors) == 0, errors


class InjuryCapabilityConsistencyRule(ValidationRule):
    """Validate required capabilities match injury types."""

    INJURY_CAPABILITY_MAP = {
        "Head": ["trauma_center", "neurosurgical"],
        "Neck": ["trauma_center", "vascular", "ent"],
        "Chest": ["trauma_center", "thoracic", "cardiac"],
        "Back": ["trauma_center", "orthopedic"],
        "Pelvis": ["trauma_center", "orthopedic"],
        "Abdomen": ["trauma_center", "hepatobiliary"],
        "Limbs (Upper)": ["orthopedic"],
        "Limbs (Lower)": ["orthopedic"],
    }

    MECHANISM_CAPABILITY_MAP = {
        "Thermal": ["burn"],
        "Blast": ["trauma_center"],
        "Chemical": ["trauma_center"],
        "Radiation": ["trauma_center"],
    }

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        warnings = []  # These are warnings, not hard errors
        injuries = data.get("injuries")
        capabilities = data.get("required_medical_capabilities")

        # Skip if injuries or capabilities is None
        if injuries is None or capabilities is None:
            return True, []

        # Check if injury locations suggest certain capabilities
        for injury in injuries:
            locations = injury.get("locations", [])
            mechanisms = injury.get("mechanisms", [])

            # Check location-based capabilities
            for location in locations:
                expected_caps = self.INJURY_CAPABILITY_MAP.get(location, [])
                for cap in expected_caps:
                    if not capabilities.get(cap, False):
                        warnings.append(
                            f"Injury to {location} typically requires {cap} capability"
                        )

            # Check mechanism-based capabilities
            for mechanism in mechanisms:
                expected_caps = self.MECHANISM_CAPABILITY_MAP.get(mechanism, [])
                for cap in expected_caps:
                    if not capabilities.get(cap, False):
                        warnings.append(
                            f"Injury mechanism {mechanism} typically requires {cap} capability"
                        )

        # These are warnings, so always return True but include messages
        return True, warnings


class RequiredFieldsRule(ValidationRule):
    """Validate all required fields are present."""

    REQUIRED_FIELDS = [
        "description",
    ]

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                errors.append(f"Required field '{field}' is missing or None")

        # patient_id will be auto-generated if missing, so we don't validate it here

        return len(errors) == 0, errors


# Registry of all validation rules
VALIDATION_RULES = [
    RequiredFieldsRule(),
    VitalSignsRangeRule(),
    GlasgowComaScaleRule(),
    AgeRangeRule(),
    DeceasedConsistencyRule(),
    InjuryCapabilityConsistencyRule(),  # This one produces warnings
]


def validate_patient_data(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Run all validation rules on patient data.

    Args:
        data: Patient data dictionary

    Returns:
        Tuple of (is_valid, list_of_errors, list_of_warnings)
    """
    all_errors = []
    all_warnings = []

    for rule in VALIDATION_RULES:
        is_valid, messages = rule.validate(data)

        if not is_valid:
            all_errors.extend(messages)
        elif messages:  # Valid but has warnings
            all_warnings.extend(messages)

    return len(all_errors) == 0, all_errors, all_warnings
