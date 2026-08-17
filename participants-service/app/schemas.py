from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ParticipantType(str, Enum):
    """Les trois types imposés par l'énoncé."""

    ETUDIANT = "etudiant"
    PROFESSEUR = "professeur"
    EXTERNE = "externe"


class ParticipantBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    type: ParticipantType


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    type: Optional[ParticipantType] = None


class ParticipantOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
