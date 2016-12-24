from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy import String, Integer, Date, BLOB
from sqlalchemy.ext.declarative import declarative_base

from .types import DeclarationType

Base = declarative_base()


class Servant(Base):
    __tablename__ = 'servants'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    NAME = Column(String, nullable=False)
    DECL0_DEP_ID = Column(Integer, ForeignKey("dependencies.ID"))
    DECL0_TYPE = Column(DeclarationType)
    DECL0_SENT = Column(Date)

    # TODO: We are making the assumption that there is not more than
    #   one person with the same name and in the same dependency that
    #   submitted a declaration of the same type on the same day. This
    #   assumption has not been validated!
    ix_decl0_cols = 'NAME', 'DECL0_DEP_ID', 'DECL0_TYPE', 'DECL0_SENT'
    ix_decl0 = Index('ix_decl0', *ix_decl0_cols, unique=True)
    __table_args__ = (ix_decl0,)


class Declaration(Base):
    __tablename__ = 'declarations'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    SERVANT_ID = Column(Integer, ForeignKey("servants.ID"))
    DEPENDENCY_ID = Column(Integer, ForeignKey("dependencies.ID"))
    TYPE = Column(DeclarationType)
    SENT = Column(Date)
    PDF = Column(BLOB)
    SHA256 = Column(String, index=True, unique=True)


class Dependency(Base):
    __tablename__ = 'dependencies'

    ID = Column(Integer, primary_key=True, autoincrement=True)
    DEPENDENCY = Column(String, index=True, unique=True, nullable=False)
