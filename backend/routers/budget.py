from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Budget, Depense

router = APIRouter(
    prefix="/budget",
    tags=["Budget"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def obtenir_budget(db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == 1).first()

    if budget is None:
        return {"montant": None}

    return {"montant": budget.montant}


@router.put("/")
def modifier_budget(donnees: dict = Body(...), db: Session = Depends(get_db)):
    montant = donnees.get("montant")

    if montant is None or montant < 0:
        return {"erreur": "Le budget doit être un nombre positif ou nul."}

    budget = db.query(Budget).filter(Budget.id == 1).first()

    if budget is None:
        budget = Budget(id=1, montant=montant)
        db.add(budget)
    else:
        budget.montant = montant

    db.commit()
    db.refresh(budget)

    return {"message": "Budget enregistré avec succès", "montant": budget.montant}


@router.get("/stats")
def statistiques_budget(db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == 1).first()
    total_depenses = sum(
        depense.montant for depense in db.query(Depense).all()
    )

    montant_initial = budget.montant if budget else 0
    restant = montant_initial - total_depenses

    return {
        "budget_initial": montant_initial,
        "total_depenses": total_depenses,
        "solde_restant": restant,
        "nombre_depenses": db.query(Depense).count()
    }