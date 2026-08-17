from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False, index=True)
    # unique=True : garantit au niveau BASE qu'un email n'est pas réutilisé,
    # même si deux requêtes arrivent exactement en même temps.
    email = Column(String(150), nullable=False, unique=True, index=True)
    phone = Column(String(30), nullable=True)
    # etudiant | professeur | externe — validé par l'enum Pydantic.
    type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
