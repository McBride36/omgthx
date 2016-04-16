from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


# {"id":1,"name":"gunnbr","channel":"#reprap","timestamp":"2014-01-15 18:13:48","message":"RoyOnWheels|MTW: Oh! I like it!!"}
class Seen(Base):
    __tablename__ = 'seen'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    channel = Column(String(250), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    message = Column(String(500), nullable=False)


# {"id":3030,"item":"JATMN","are":0,"value":"JAT.MN","nick":"JATMN","dateset":"2014-01-01 02:46:48","locked":null,"lastsync":null}
class Factoids(Base):
    __tablename__ = 'factoids'
    id = Column(Integer, primary_key=True)
    item = Column(String(250), nullable=False)
    are = Column(Integer, nullable=True)
    value = Column(String(500), nullable=False)
    nick = Column(String(250), nullable=True)
    dateset = Column(DateTime, default=datetime.datetime.utcnow)
    locked = Column(String(250), nullable=True)
    lastsync = Column(String(250), nullable=True)


# {"id":19,"author":"Chewonit64","recipient":"kthx","timestamp":"2014-01-10 16:36:12","message":"botsmack!","inTracked":1}
class Tell(Base):
    __tablename__ = 'tell'
    id = Column(Integer, primary_key=True)
    author = Column(String(250), nullable=False)
    recipient = Column(String(250), nullable=False)
    message = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Factoid_history(Base):
    __tablename__ = 'factoid_history'
    id = Column(Integer, primary_key=True)
    item = Column(String(250), nullable=False)
    value = Column(String(500), nullable=False)
    nick = Column(String(250), nullable=True)
    dateset = Column(DateTime, default=datetime.datetime.utcnow)


engine = create_engine('sqlite:///reprap_database.db')

Base.metadata.create_all(engine)
