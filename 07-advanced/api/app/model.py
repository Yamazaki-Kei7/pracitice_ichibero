from typing import Optional

from pydantic import BaseModel


class PoiCreate(BaseModel):
    longitude: float
    latitude: float


class PoiUpdate(BaseModel):
    longitude: Optional[float] = None
    latitude: Optional[float] = None
