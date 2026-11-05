
from sqlalchemy import Column, Integer, String, Float, Date
from database import Base


class Depense(Base):
    __tablename__ = "depenses"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(100), nullable=False)
    montant = Column(Float, nullable=False)
    categorie = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String(500), nullable=True)
class Budget(Base):
    __tablename__ = "budget"

    id = Column(Integer, primary_key=True, index=True)
    montant = Column(Float, nullable=False)