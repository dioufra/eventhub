from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas, clients

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.RegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Inscrire un participant à un événement",
)
def create_registration(payload: schemas.RegistrationCreate, db: Session = Depends(get_db)):
    clients.get_participant(payload.participant_id)
    clients.get_event(payload.event_id)
    availability = clients.get_event_availability(payload.event_id)
    remaining = availability.get("remaining", 0)
    if remaining <= 0:
        raise HTTPException(status_code=409, detail="no remaining places for this event")
    existing = db.query(models.Registration).filter(
        models.Registration.event_id == payload.event_id,
        models.Registration.participant_id == payload.participant_id,
        models.Registration.status == "confirmed",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="participant already registered for this event")
    registration = models.Registration(
        event_id=payload.event_id,
        participant_id=payload.participant_id,
        status="confirmed",
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


@router.post(
    "/{registration_id}/cancel",
    response_model=schemas.RegistrationOut,
    summary="Annuler une inscription",
)
def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    registration = db.query(models.Registration).filter(models.Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="registration not found")
    if registration.status == "cancelled":
        raise HTTPException(status_code=409, detail="registration already cancelled")
    registration.status = "cancelled"
    db.commit()
    db.refresh(registration)
    return registration


@router.get(
    "/event/{event_id}",
    response_model=List[schemas.RegistrationOut],
    summary="Lister les inscriptions par événement",
)
def list_by_event(event_id: int, db: Session = Depends(get_db)):
    return db.query(models.Registration).filter(
        models.Registration.event_id == event_id,
        models.Registration.status == "confirmed",
    ).all()


@router.get(
    "/participant/{participant_id}",
    response_model=List[schemas.RegistrationOut],
    summary="Lister les événements d'un participant",
)
def list_by_participant(participant_id: int, db: Session = Depends(get_db)):
    return db.query(models.Registration).filter(
        models.Registration.participant_id == participant_id,
        models.Registration.status == "confirmed",
    ).all()


@router.get(
    "/stats",
    response_model=schemas.RegistrationStats,
    summary="Statistiques d'inscription",
)
def registration_stats(db: Session = Depends(get_db)):
    total = db.query(models.Registration).filter(models.Registration.status == "confirmed").count()
    rows = db.query(models.Registration.event_id).filter(
        models.Registration.status == "confirmed"
    ).all()
    counts = {}
    for row in rows:
        counts[row.event_id] = counts.get(row.event_id, 0) + 1
    by_event = [{"event_id": event_id, "count": count} for event_id, count in counts.items()]
    return {"total": total, "by_event": by_event}
