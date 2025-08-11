"""
Module: db.models

Contains ORM models for the application.
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
from datetime import datetime, timezone

Base = declarative_base()

class TransactionType(PyEnum):
    """
    Enum for transaction types.
    """
    DEPOSIT = "deposit"
    PREDICTION = "prediction"
    SCAN3D = "scan3d"

class User(Base):
    """
    ORM model for a user account.

    Attributes:
      id (int): primary key
      email (str): unique and indexed user email
      hashed_password (str): stored password hash
      balance (float): user credits balance
      is_admin (bool): administrative privileges flag (default False)
      is_active(bool): account active flag (default True)
      created_at (datetime): timestamp of account creation
      transactions: relationship to Transaction model
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    @validates("created_at")
    def _validate_created_at(self, key, value):
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Transaction(Base):
    """
    ORM model for user transactions (deposits or ML predictions).

    Attributes:
      id (int): primary key
      user_id (int): foreign key to users.id
      type (str): 'deposit' or 'prediction' or 'scan3d' (exposed as plain string)
      amount (float): amount of transaction
      comment (str): optional comment for the transaction
      timestamp (datetime): datetime of transaction
      user: relationship back to User model
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Store as Enum in DB but expose as string at ORM level via property below
    _type = Column("type", Enum(TransactionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    amount = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="transactions")

    @hybrid_property
    def type(self) -> str:
        return self._type.value if isinstance(self._type, TransactionType) else str(self._type)

    @type.setter
    def type(self, value: str) -> None:
        try:
            self._type = TransactionType(value)
        except ValueError as exc:
            raise ValueError(f"Invalid transaction type: {value}") from exc

    @type.expression
    def type(cls):
        return cls._type

    @validates("timestamp")
    def _validate_timestamp(self, key, value):
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    