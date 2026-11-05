
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Adresse de notre base de données SQLite
DATABASE_URL = "sqlite:///./mesdepenses.db"

# Création du moteur de connexion
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Création des sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base des modèles
Base = declarative_base()
