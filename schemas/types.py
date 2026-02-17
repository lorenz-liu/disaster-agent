from pydantic import BaseModel


class LocationType(BaseModel):
    latitude: float
    longitude: float
