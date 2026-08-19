from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        # Garde-fous au niveau BASE. La validation Pydantic couvre déjà l'API,
        # mais elle ne protège pas d'une écriture directe ou d'un import.
        CheckConstraint("capacity > 0", name="ck_events_capacity_positive"),
        CheckConstraint("seats_taken >= 0", name="ck_events_seats_taken_positive"),
        CheckConstraint(
            "seats_taken <= capacity", name="ck_events_seats_within_capacity"
        ),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # Index sur les deux colonnes servant aux filtres exigés par l'énoncé.
    starts_at = Column(DateTime, nullable=False, index=True)
    location = Column(String(200), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    # Compteur détenu par CE service. registrations-service ne l'écrit
    # jamais directement : il passe par /seats/reserve et /seats/release.
    # C'est ce qui évite une dépendance circulaire entre les deux services.
    seats_taken = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def seats_available(self) -> int:
        return max((self.capacity or 0) - (self.seats_taken or 0), 0)
