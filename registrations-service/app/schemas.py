from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class RegistrationBase(BaseModel):
    event_id: int
    participant_id: int


class RegistrationCreate(RegistrationBase):
    pass


class RegistrationOut(RegistrationBase):
    id: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RegistrationStats(BaseModel):
    total: int
    by_event: List[dict]
