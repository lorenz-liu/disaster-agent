from pydantic import BaseModel
from .enums import HealthcareFacilityLevelEnum
from .types import LocationType


class FacilityCapabilitiesType(BaseModel):
    trauma_center: bool
    neurosurgical: bool
    orthopedic: bool
    ophthalmology: bool
    burn: bool
    pediatric: bool
    obstetric: bool
    cardiac: bool
    thoracic: bool
    vascular: bool
    ent: bool
    hepatobiliary: bool


class MedicalResourcesType(BaseModel):
    ward: int
    ordinary_icu: int
    operating_room: int
    ventilator: int
    prbc_unit: int
    isolation: int
    decontamination_unit: int
    ct_scanner: int
    oxygen_cylinder: int
    interventional_radiology: int


class VehicleResourcesType(BaseModel):
    ambulances: int
    helicopters: int


class HealthcareFacilityType(BaseModel):
    facility_id: str
    name: str
    level: HealthcareFacilityLevelEnum
    medical_resources: MedicalResourcesType
    capabilities: FacilityCapabilitiesType
    vehicle_resources: VehicleResourcesType
    location: LocationType
    accepted_patients: list[str]
