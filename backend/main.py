from fastapi import FastAPI
from database import engine, Base
import models
from routers import depenses, budget

# Création automatique des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MesDepenses API",
    description="API de gestion des dépenses personnelles",
    version="1.0.0"
)

app.include_router(depenses.router)
app.include_router(budget.router)


@app.get("/")
def accueil():
    return {
        "message": "Bienvenue dans MesDepenses API",
        "database": "SQLite connectée"
    }