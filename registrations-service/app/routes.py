from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import clients, models, schemas
from app.database import get_db

router = APIRouter()


# ATTENTION : /stats doit être déclaré AVANT toute route /{registration_id},
# sinon FastAPI tente de convertir "stats" en entier et renvoie une 422.
@router.get(
    "/stats",
    response_model=schemas.RegistrationStats,
    summary="Statistiques d'inscription",
)
def registration_stats(db: Session = Depends(get_db)):
    confirmed = db.query(models.Registration).filter(
        models.Registration.status == "confirmed"
    )
    total = confirmed.count()

    counts: dict[int, int] = {}
    for row in confirmed.with_entities(models.Registration.event_id).all():
        counts[row.event_id] = counts.get(row.event_id, 0) + 1

    return {
        "total": total,
        "by_event": [
            {"event_id": event_id, "count": count} for event_id, count in counts.items()
        ],
    }


@router.get(
    "/event/{event_id}",
    response_model=List[schemas.RegistrationOut],
    summary="Lister les inscriptions d'un événement",
)
def list_by_event(event_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Registration)
        .filter(
            models.Registration.event_id == event_id,
            models.Registration.status == "confirmed",
        )
        .order_by(models.Registration.id)
        .all()
    )


@router.get(
    "/participant/{participant_id}",
    response_model=List[schemas.RegistrationOut],
    summary="Lister les événements d'un participant",
)
def list_by_participant(participant_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Registration)
        .filter(
            models.Registration.participant_id == participant_id,
            models.Registration.status == "confirmed",
        )
        .order_by(models.Registration.id)
        .all()
    )


@router.get(
    "",
    response_model=List[schemas.RegistrationOut],
    summary="Lister toutes les inscriptions",
)
def list_registrations(
    status_filter: str | None = None, db: Session = Depends(get_db)
):
    """Liste toutes les inscriptions, filtrables par statut."""
    query = db.query(models.Registration)
    if status_filter:
        query = query.filter(models.Registration.status == status_filter)
    return query.order_by(models.Registration.id.desc()).all()


@router.post(
    "",
    response_model=schemas.RegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Inscrire un participant à un événement",
)
def create_registration(
    payload: schemas.RegistrationCreate, db: Session = Depends(get_db)
):
    """Inscription en quatre temps, dans cet ordre précis.

    1. Refus si déjà inscrit — contrôle local, aucun appel réseau inutile.
    2. Le participant existe-t-il ? (participants-service)
    3. Réservation ATOMIQUE d'une place (events-service).
    4. Enregistrement local ; si l'écriture échoue, on rend la place.
    """
    existing = (
        db.query(models.Registration)
        .filter(
            models.Registration.event_id == payload.event_id,
            models.Registration.participant_id == payload.participant_id,
            models.Registration.status == "confirmed",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="participant already registered for this event"
        )

    clients.get_participant(payload.participant_id)

    # Renvoie 404 si l'événement n'existe pas, 409 s'il est complet.
    clients.reserve_seat(payload.event_id)

    try:
        registration = (
            db.query(models.Registration)
            .filter(
                models.Registration.event_id == payload.event_id,
                models.Registration.participant_id == payload.participant_id,
            )
            .first()
        )
        if registration:
            # Réinscription après annulation : on réutilise la ligne.
            registration.status = "confirmed"
        else:
            registration = models.Registration(
                event_id=payload.event_id,
                participant_id=payload.participant_id,
                status="confirmed",
            )
            db.add(registration)
        db.commit()
        db.refresh(registration)
    except Exception:
        # Compensation : la place réservée à l'étape 3 est rendue, sinon
        # elle resterait bloquée pour toujours.
        db.rollback()
        clients.release_seat(payload.event_id)
        raise

    return registration


@router.delete(
    "/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Annuler une inscription",
)
def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    registration = (
        db.query(models.Registration)
        .filter(models.Registration.id == registration_id)
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="registration not found")
    if registration.status == "cancelled":
        # Annuler deux fois est sans effet : on ne libère pas deux places.
        return

    registration.status = "cancelled"
    db.commit()
    clients.release_seat(registration.event_id)
