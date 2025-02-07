from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50))
    full_name = Column(String(100))
    role = Column(String(20), default='user')

class Olympiad(Base):
    __tablename__ = 'olympiads'
    olympiad_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    start_date = Column(DateTime)

class Registration(Base):
    __tablename__ = 'registrations'
    registration_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    olympiad_id = Column(Integer, ForeignKey('olympiads.olympiad_id'))

class Group(Base):
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), unique=True)
    group_name = Column(String(100))