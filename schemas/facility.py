from typing import Optional
from pydantic import BaseModel
from .enums import HealthcareFacilityLevelEnum
from .types import LocationType


class FacilityCapabilitiesType(BaseModel):
    trauma_center: Optional[bool] = None
    neurosurgical: Optional[bool] = None
    orthopedic: Optional[bool] = None
    ophthalmology: Optional[bool] = None
    burn: Optional[bool] = None
    pediatric: Optional[bool] = None
    obstetric: Optional[bool] = None
    cardiac: Optional[bool] = None
    thoracic: Optional[bool] = None
    vascular: Optional[bool] = None
    ent: Optional[bool] = None
    hepatobiliary: Optional[bool] = None


class MedicalResourcesType(BaseModel):
    ward: Optional[int] = None
    ordinary_icu: Optional[int] = None
    operating_room: Optional[int] = None
    ventilator: Optional[int] = None
    prbc_unit: Optional[int] = None
    isolation: Optional[int] = None
    decontamination_unit: Optional[int] = None
    ct_scanner: Optional[int] = None
    oxygen_cylinder: Optional[int] = None
    interventional_radiology: Optional[int] = None


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
