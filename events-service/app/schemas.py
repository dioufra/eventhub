from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    starts_at: datetime
    location: str = Field(min_length=2, max_length=200)
    # gt=0 empêche de créer un événement à capacité nulle ou négative,
    # qui aurait des places « toujours disponibles ».
    capacity: int = Field(gt=0, le=10_000)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=200)
    capacity: Optional[int] = Field(default=None, gt=0, le=10_000)


class EventOut(EventBase):
    id: int
    seats_taken: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AvailabilityOut(BaseModel):
    event_id: int
    capacity: int
    seats_taken: int
    seats_available: int
    is_full: bool
