from sqlalchemy import *
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

import settings


Base = declarative_base()
engine = None
session = None


def init_db():
    global engine, session

    engine = create_engine(settings.DB_URI, echo=False)

    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()

    Base.metadata.create_all(bind=engine)


class Tweet(Base):
    __tablename__ = 'tweets'

    tweet = Column(Integer(unsigned=True), primary_key=True, autoincrement=True)
    tweet_id  = Column(String(32), unique=True)
    user_id = Column(String(32))
    text = Column(Text())
    media = Column(LargeBinary())
    gone = Column(Boolean(), default=False)
