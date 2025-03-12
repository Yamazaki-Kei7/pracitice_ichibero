from pydantic import BaseModel


class PoiCreate(BaseModel):
    name: str
    longitude: float
    latitude: float


class PoiUpdate(BaseModel):
    name: str | None = None
    longitude: float | None = None
    latitude: float | None = None
