from sqlalchemy import Column, Integer, String
from database.db import Base


class User(Base):
    __tablename__ = 'users'

    # Поле id будет хранить Telegram user id
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=True)
    full_name = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class Group(Base):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(50), unique=True, index=True)
    group_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Group group_id={self.group_id} chat_id={self.chat_id} group_name={self.group_name}>"