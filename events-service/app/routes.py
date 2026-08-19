from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


def _availability(event: models.Event) -> schemas.AvailabilityOut:
    return schemas.AvailabilityOut(
        event_id=event.id,
        capacity=event.capacity,
        seats_taken=event.seats_taken,
        seats_available=event.seats_available,
        is_full=event.seats_available == 0,
    )


def _get_or_404(db: Session, event_id: int) -> models.Event:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return event


@router.get("", response_model=List[schemas.EventOut], summary="Lister les événements")
def list_events(
    event_date: Optional[date] = Query(default=None, alias="date"),
    location: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Liste les événements, avec filtres optionnels par date et par lieu."""
    query = db.query(models.Event)

    if event_date:
        query = query.filter(
            models.Event.starts_at.between(
                datetime.combine(event_date, time.min),
                datetime.combine(event_date, time.max),
            )
        )

    if location:
        query = query.filter(models.Event.location.ilike(f"%{location}%"))

    return query.order_by(models.Event.starts_at).all()


@router.post(
    "",
    response_model=schemas.EventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un événement",
)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    event = models.Event(**payload.model_dump(), seats_taken=0)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=schemas.EventOut, summary="Détail d'un événement")
def get_event(event_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, event_id)


@router.put("/{event_id}", response_model=schemas.EventOut, summary="Modifier un événement")
def update_event(
    event_id: int, payload: schemas.EventUpdate, db: Session = Depends(get_db)
):
    event = _get_or_404(db, event_id)
    updates = payload.model_dump(exclude_unset=True)

    new_capacity = updates.get("capacity")
    if new_capacity is not None and new_capacity < event.seats_taken:
        raise HTTPException(
            status_code=409,
            detail=f"capacity below the {event.seats_taken} existing registrations",
        )

    for field, value in updates.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un événement",
)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = _get_or_404(db, event_id)
    db.delete(event)
    db.commit()


@router.get(
    "/{event_id}/availability",
    response_model=schemas.AvailabilityOut,
    summary="Places restantes",
)
def availability(event_id: int, db: Session = Depends(get_db)):
    return _availability(_get_or_404(db, event_id))


# ---------------------------------------------------------------------------
# Endpoints INTERNES — appelés uniquement par registrations-service.
# Ils ne sont pas destinés au frontend.
# ---------------------------------------------------------------------------


@router.post(
    "/{event_id}/seats/reserve",
    response_model=schemas.AvailabilityOut,
    summary="[interne] Réserver une place",
)
def reserve_seat(event_id: int, db: Session = Depends(get_db)):
    # with_for_update() verrouille la ligne le temps de la transaction :
    # deux inscriptions simultanées ne peuvent pas réserver la même
    # dernière place. SQLite ignore la clause, PostgreSQL l'applique.
    event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .with_for_update()
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    if event.seats_available == 0:
        raise HTTPException(status_code=409, detail="event is full")

    event.seats_taken += 1
    db.commit()
    db.refresh(event)
    return _availability(event)


@router.post(
    "/{event_id}/seats/release",
    response_model=schemas.AvailabilityOut,
    summary="[interne] Libérer une place",
)
def release_seat(event_id: int, db: Session = Depends(get_db)):
    event = (
        db.query(models.Event)
        .filter(models.Event.id == event_id)
        .with_for_update()
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="event not found")

    event.seats_taken = max((event.seats_taken or 0) - 1, 0)
    db.commit()
    db.refresh(event)
    return _availability(event)
