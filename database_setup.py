import os
from sqlalchemy import create_engine, Column, String, Text, Integer, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabela para configurações gerais (como a mensagem de boas-vindas)
class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)

# NOVA TABELA para guardar o progresso dos usuários
class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True) # ID do usuário no Discord
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)

def setup_database():
    # Agora cria as duas tabelas (settings e users) se elas não existirem
    Base.metadata.create_all(bind=engine)
