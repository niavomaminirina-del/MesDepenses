
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class DepenseBase(BaseModel):
    titre: str
    montant: float
    categorie: str
    date: date
    description: Optional[str] = None


class DepenseCreate(DepenseBase):
    pass


class DepenseResponse(DepenseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
