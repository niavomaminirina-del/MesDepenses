
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Depense
from schemas import DepenseCreate, DepenseResponse

router = APIRouter(
    prefix="/depenses",
    tags=["Dépenses"]
)


# Connexion à la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ajouter une dépense
@router.post("/", response_model=DepenseResponse)
def creer_depense(
    depense: DepenseCreate,
    db: Session = Depends(get_db)
):
    nouvelle_depense = Depense(**depense.model_dump())

    db.add(nouvelle_depense)
    db.commit()
    db.refresh(nouvelle_depense)

    return nouvelle_depense


# Afficher toutes les dépenses
@router.get("/", response_model=list[DepenseResponse])
def lister_depenses(db: Session = Depends(get_db)):
    return db.query(Depense).all()


# Consulter une dépense par son identifiant
@router.get("/{depense_id}", response_model=DepenseResponse)
def obtenir_depense(
    depense_id: int,
    db: Session = Depends(get_db)
):
    depense = db.query(Depense).filter(
        Depense.id == depense_id
    ).first()

    if depense is None:
        raise HTTPException(
            status_code=404,
            detail="Dépense introuvable"
        )

    return depense


# Modifier une dépense
@router.put("/{depense_id}", response_model=DepenseResponse)
def modifier_depense(
    depense_id: int,
    depense_modifiee: DepenseCreate,
    db: Session = Depends(get_db)
):
    depense = db.query(Depense).filter(
        Depense.id == depense_id
    ).first()

    if depense is None:
        raise HTTPException(
            status_code=404,
            detail="Dépense introuvable"
        )

    depense.titre = depense_modifiee.titre
    depense.montant = depense_modifiee.montant
    depense.categorie = depense_modifiee.categorie
    depense.date = depense_modifiee.date
    depense.description = depense_modifiee.description

    db.commit()
    db.refresh(depense)

    return depense


# Supprimer une dépense
@router.delete("/{depense_id}")
def supprimer_depense(
    depense_id: int,
    db: Session = Depends(get_db)
):
    depense = db.query(Depense).filter(
        Depense.id == depense_id
    ).first()

    if depense is None:
        raise HTTPException(
            status_code=404,
            detail="Dépense introuvable"
        )

    db.delete(depense)
    db.commit()

    return {
        "message": "Dépense supprimée avec succès"
    }
