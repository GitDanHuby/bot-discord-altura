import os
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# Pega o link do banco de dados das variáveis de ambiente
DATABASE_URL = os.getenv('DATABASE_URL')

# Um pequeno ajuste para o SQLAlchemy funcionar com o link da Railway
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Cria a "ponte" de conexão com o banco de dados
engine = create_engine(DATABASE_URL)

# Cria uma sessão para conversar com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para nossos modelos de tabela
Base = declarative_base()

# Define a nossa "gaveta" de configurações
class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True) # Ex: "welcome_message"
    value = Column(Text, nullable=False)               # Ex: "Bem-vindo ao servidor..."

# Função que cria a tabela no banco de dados se ela não existir
def setup_database():
    Base.metadata.create_all(bind=engine)
