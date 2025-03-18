from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Integer
from database.db import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=True)
    full_name = Column(String(100), nullable=True)
    class_number = Column(String(10), index=True)
    class_letter = Column(String(1), index=True)
    contact_info = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)


    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), unique=True, index=True)
    group_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Group group_id={self.group_id} chat_id={self.chat_id} group_name={self.group_name}>"

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)  # Название события
    description = Column(String(500), nullable=True)  # Описание
    date = Column(DateTime, nullable=False)  # Дата и время события
    is_important = Column(Boolean, default=False)  # Важное событие
    created_by = Column(Integer, nullable=False)  # ID создателя (учителя/админа)

    def __repr__(self):
        return f"<Event {self.title} ({self.date})>"

