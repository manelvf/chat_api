""" Stores data in the database 

The whole module needs to be imported in order to initialize the declarative base
"""
from datetime import datetime
import os
import secrets

from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./chat.db")


Base = declarative_base()

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Exceptions
class InvalidUsernamePasswordError(Exception):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="messages")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    user = relationship("User")


def get_user_from_session(session_id: str):
    """Retrieve the user associated with the session ID."""
    db = SessionLocal()
    session = db.query(Session).filter(Session.session_id == session_id).first()
    user = session.user if session else None
    db.close()
    return user


def get_user_by_username(username: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == username).first()
    finally:
        db.close()


def add_user(username: str, password: str):
    hashed_password = password

    db = SessionLocal()
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.close()


def login_user(username: str, password: str) -> User | None:
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if not user or not pwd_context.verify(password, user.hashed_password):
            raise InvalidUsernamePasswordError

    
        # Create a new session
        session_id = secrets.token_hex(32)
        new_session = Session(session_id=session_id, user_id=user.id)
        db.add(new_session)
        db.commit()
    finally:
        db.close()



def save_message(data, user: User):
    db = SessionLocal()

    # Save message to the database
    db_message = Message(content=data, user_id=user.id if user else None)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    db.close()
