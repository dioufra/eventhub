from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        # Garantit au niveau BASE qu'un participant ne peut pas être inscrit
        # deux fois au même événement. Le contrôle applicatif seul ne suffit
        # pas : entre le SELECT et l'INSERT, une requête concurrente peut
        # s'intercaler. C'est le même raisonnement que le verrou posé sur le
        # compteur de places dans events-service.
        UniqueConstraint(
            "event_id", "participant_id", name="uq_registration_event_participant"
        ),
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False, index=True)
    participant_id = Column(Integer, nullable=False, index=True)
    status = Column(String(20), default="confirmed", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
