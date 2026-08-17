from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


def _get_or_404(db: Session, participant_id: int) -> models.Participant:
    participant = (
        db.query(models.Participant)
        .filter(models.Participant.id == participant_id)
        .first()
    )
    if not participant:
        raise HTTPException(status_code=404, detail="participant not found")
    return participant


@router.get(
    "", response_model=List[schemas.ParticipantOut], summary="Lister les participants"
)
def list_participants(search: Optional[str] = None, db: Session = Depends(get_db)):
    """Liste les participants. `search` filtre sur le nom OU l'email."""
    query = db.query(models.Participant)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Participant.full_name.ilike(pattern),
                models.Participant.email.ilike(pattern),
            )
        )

    return query.order_by(models.Participant.full_name).all()


@router.post(
    "",
    response_model=schemas.ParticipantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte participant",
)
def create_participant(
    payload: schemas.ParticipantCreate, db: Session = Depends(get_db)
):
    email = str(payload.email)
    if db.query(models.Participant).filter(models.Participant.email == email).first():
        raise HTTPException(status_code=409, detail="email already used")

    participant = models.Participant(
        full_name=payload.full_name,
        email=email,
        phone=payload.phone,
        type=payload.type.value,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@router.get(
    "/{participant_id}",
    response_model=schemas.ParticipantOut,
    summary="Détail d'un participant",
)
def get_participant(participant_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, participant_id)


@router.put(
    "/{participant_id}",
    response_model=schemas.ParticipantOut,
    summary="Modifier un profil participant",
)
def update_participant(
    participant_id: int,
    payload: schemas.ParticipantUpdate,
    db: Session = Depends(get_db),
):
    participant = _get_or_404(db, participant_id)
    updates = payload.model_dump(exclude_unset=True)

    if updates.get("email") is not None:
        email = str(updates["email"])
        clash = (
            db.query(models.Participant)
            .filter(
                models.Participant.email == email,
                models.Participant.id != participant_id,
            )
            .first()
        )
        if clash:
            raise HTTPException(status_code=409, detail="email already used")
        updates["email"] = email

    if updates.get("type") is not None:
        updates["type"] = updates["type"].value

    for field, value in updates.items():
        setattr(participant, field, value)

    db.commit()
    db.refresh(participant)
    return participant


@router.delete(
    "/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un participant",
)
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    participant = _get_or_404(db, participant_id)
    db.delete(participant)
    db.commit()
