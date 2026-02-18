from typing import Optional
from pydantic import BaseModel


class LocationType(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
