from typing import Optional
from pydantic import BaseModel, Field
from .enums import (
    GenderEnum,
    PatientSeverityEnum,
    PatientInjuryLocationEnum,
    PatientInjuryMechanismEnum,
    PatientStatusEnum,
)
from .types import LocationType
from .facility import (
    FacilityCapabilitiesType,
    MedicalResourcesType,
)


class BloodPressure(BaseModel):
    systolic: Optional[float] = None
    diastolic: Optional[float] = None


class PatientVitalSignsType(BaseModel):
    heart_rate: Optional[float] = None
    blood_pressure: BloodPressure
    respiratory_rate: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    temperature: Optional[float] = None


class PatientConsciousnessType(BaseModel):
    eye_response: Optional[int] = None
    verbal_response: Optional[int] = None
    motor_response: Optional[int] = None
    total_score: Optional[int] = None


class PatientInjuryType(BaseModel):
    locations: list[PatientInjuryLocationEnum]
    mechanisms: list[PatientInjuryMechanismEnum]
    severity: PatientSeverityEnum
    description: str


class PatientType(BaseModel):
    patient_id: str
    name: str = "Unknown"
    age: Optional[int] = None
    gender: Optional[GenderEnum] = None
    vital_signs: Optional[PatientVitalSignsType] = None
    consciousness: Optional[PatientConsciousnessType] = None
    acuity: Optional[PatientSeverityEnum] = None
    injuries: Optional[list[PatientInjuryType]] = None
    required_medical_capabilities: Optional[FacilityCapabilitiesType] = None
    required_medical_resources: Optional[MedicalResourcesType] = None
    description: str
    predicted_death_timestamp: Optional[int] = None
    status: PatientStatusEnum = PatientStatusEnum.UNASSIGNED
    assigned_facility: Optional[str] = None
    action_logs: list[str] = []
    deceased: Optional[bool] = None
    location: Optional[LocationType] = None
