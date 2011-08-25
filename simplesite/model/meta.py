"""SQLAlchemy Metadata and Session object"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import MetaData

__all__ = ['Session', 'engine', 'metadata']

# SQLAlchemy session manager. Updated by model.init_model()
Session = scoped_session(sessionmaker())

# SQLAlchemy database engine. Updated by model.init_model()
engine = None

#Global metadata. If you have multiple databases with overlapping table 
# names, you'll need metadata for each db.
Base = declarative_base()
metadata = MetaData()


