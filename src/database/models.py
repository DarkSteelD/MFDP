from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from .config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    balance = Column(Integer, default=0)
    
    transactions = relationship("Transaction", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    change = Column(Integer)
    valid = Column(Boolean)
    time = Column(DateTime, default=lambda: datetime.now())

    user = relationship("User", back_populates="transactions")

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    version = Column(String)
    creation_date = Column(DateTime, default=lambda: datetime.now())
    is_active = Column(Boolean, default=True)
    model_type = Column(String)
    parameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    predictions = relationship("Prediction", back_populates="model")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("ml_models.id"))
    input_data = Column(JSON)
    output_data = Column(JSON) 
    successful = Column(Boolean)
    created_at = Column(DateTime, default=lambda: datetime.now())
    execution_time = Column(Float, nullable=True)
    user = relationship("User", back_populates="predictions")
    model = relationship("MLModel", back_populates="predictions") 