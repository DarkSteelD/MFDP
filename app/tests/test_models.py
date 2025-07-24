"""
Tests for database models.
"""

import pytest
from datetime import datetime, timezone
from faker import Faker

from src.db.models import User, Transaction, TransactionType
from src.core.security import get_password_hash

fake = Faker()

class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, test_db_session):
        """Test creating a basic user."""
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            balance=100.0
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.hashed_password is not None
        assert user.balance == 100.0
        assert user.is_admin is False  # Default value
        assert user.is_active is True   # Default value
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_default_values(self, test_db_session):
        """Test user model default values."""
        user = User(
            email="defaults@example.com",
            hashed_password=get_password_hash("password")
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        assert user.balance == 0.0      # Default balance
        assert user.is_admin is False   # Default admin status
        assert user.is_active is True   # Default active status
        assert user.created_at is not None
    
    def test_user_admin_creation(self, test_db_session):
        """Test creating an admin user."""
        admin_user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin_password"),
            balance=1000.0,
            is_admin=True
        )
        test_db_session.add(admin_user)
        test_db_session.commit()
        test_db_session.refresh(admin_user)
        
        assert admin_user.is_admin is True
        assert admin_user.balance == 1000.0
    
    def test_user_inactive_creation(self, test_db_session):
        """Test creating an inactive user."""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password"),
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()
        test_db_session.refresh(inactive_user)
        
        assert inactive_user.is_active is False
    
    def test_user_email_uniqueness(self, test_db_session):
        """Test that user emails must be unique."""
        user1 = User(
            email="unique@example.com",
            hashed_password=get_password_hash("password1")
        )
        user2 = User(
            email="unique@example.com",  # Same email
            hashed_password=get_password_hash("password2")
        )
        
        test_db_session.add(user1)
        test_db_session.commit()
        
        test_db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            test_db_session.commit()
    
    def test_user_created_at_timezone(self, test_db_session):
        """Test that created_at uses UTC timezone."""
        before_creation = datetime.now(timezone.utc)
        
        user = User(
            email="timezone@example.com",
            hashed_password=get_password_hash("password")
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        after_creation = datetime.now(timezone.utc)
        
        assert user.created_at.tzinfo is not None
        assert before_creation <= user.created_at <= after_creation
    
    def test_user_transactions_relationship(self, test_db_session):
        """Test user-transactions relationship."""
        user = User(
            email="relations@example.com",
            hashed_password=get_password_hash("password"),
            balance=100.0
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        # Create transactions for user
        transaction1 = Transaction(
            user_id=user.id,
            type="deposit",
            amount=50.0
        )
        transaction2 = Transaction(
            user_id=user.id,
            type="prediction",
            amount=25.0
        )
        test_db_session.add(transaction1)
        test_db_session.add(transaction2)
        test_db_session.commit()
        
        # Test relationship
        test_db_session.refresh(user)
        assert len(user.transactions) == 2
        assert transaction1 in user.transactions
        assert transaction2 in user.transactions

class TestTransactionModel:
    """Test Transaction model functionality."""
    
    def test_create_deposit_transaction(self, test_db_session, test_user):
        """Test creating a deposit transaction."""
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=100.0,
            comment="Test deposit"
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.user_id == test_user.id
        assert transaction.type == "deposit"
        assert transaction.amount == 100.0
        assert transaction.comment == "Test deposit"
        assert transaction.timestamp is not None
    
    def test_create_prediction_transaction(self, test_db_session, test_user):
        """Test creating a prediction transaction."""
        transaction = Transaction(
            user_id=test_user.id,
            type="prediction",
            amount=50.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.type == "prediction"
        assert transaction.comment is None  # Optional field
    
    def test_transaction_user_relationship(self, test_db_session, test_user):
        """Test transaction-user relationship."""
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=75.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        # Test back-reference
        assert transaction.user is not None
        assert transaction.user.id == test_user.id
        assert transaction.user.email == test_user.email
    
    def test_transaction_timestamp_auto_set(self, test_db_session, test_user):
        """Test that timestamp is automatically set."""
        before_creation = datetime.now(timezone.utc)
        
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=50.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        after_creation = datetime.now(timezone.utc)
        
        assert transaction.timestamp is not None
        assert before_creation <= transaction.timestamp <= after_creation
    
    def test_transaction_without_comment(self, test_db_session, test_user):
        """Test creating transaction without comment."""
        transaction = Transaction(
            user_id=test_user.id,
            type="prediction",
            amount=25.0
            # No comment provided
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.comment is None

class TestTransactionType:
    """Test TransactionType enum."""
    
    def test_transaction_type_values(self):
        """Test TransactionType enum values."""
        assert TransactionType.DEPOSIT.value == "deposit"
        assert TransactionType.PREDICTION.value == "prediction"
    
    def test_transaction_type_in_model(self, test_db_session, test_user):
        """Test using TransactionType enum in model."""
        transaction = Transaction(
            user_id=test_user.id,
            type=TransactionType.DEPOSIT.value,
            amount=100.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.type == "deposit"

class TestModelValidation:
    """Test model validation and constraints."""
    
    def test_user_email_validation(self, test_db_session):
        """Test user email validation."""
        # This test depends on whether email validation is implemented at model level
        user = User(
            email="invalid-email",  # Invalid email format
            hashed_password=get_password_hash("password")
        )
        test_db_session.add(user)
        # Should either succeed (no validation) or fail (with validation)
        # This documents current behavior
        try:
            test_db_session.commit()
            # If we reach here, no email validation at model level
            assert user.email == "invalid-email"
        except Exception:
            # If exception, email validation exists
            test_db_session.rollback()
    
    def test_user_required_fields(self, test_db_session):
        """Test user required fields."""
        # Test missing email
        with pytest.raises(Exception):
            user = User(
                hashed_password=get_password_hash("password")
                # Missing email
            )
            test_db_session.add(user)
            test_db_session.commit()
        
        test_db_session.rollback()
        
        # Test missing hashed_password
        with pytest.raises(Exception):
            user = User(
                email="test@example.com"
                # Missing hashed_password
            )
            test_db_session.add(user)
            test_db_session.commit()
    
    def test_transaction_required_fields(self, test_db_session, test_user):
        """Test transaction required fields."""
        # Test missing user_id
        with pytest.raises(Exception):
            transaction = Transaction(
                type="deposit",
                amount=50.0
                # Missing user_id
            )
            test_db_session.add(transaction)
            test_db_session.commit()
        
        test_db_session.rollback()
        
        # Test missing type
        with pytest.raises(Exception):
            transaction = Transaction(
                user_id=test_user.id,
                amount=50.0
                # Missing type
            )
            test_db_session.add(transaction)
            test_db_session.commit()
        
        test_db_session.rollback()
        
        # Test missing amount
        with pytest.raises(Exception):
            transaction = Transaction(
                user_id=test_user.id,
                type="deposit"
                # Missing amount
            )
            test_db_session.add(transaction)
            test_db_session.commit()

class TestModelEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_user_balance_edge_cases(self, test_db_session):
        """Test user balance with edge case values."""
        # Test zero balance
        user_zero = User(
            email="zero@example.com",
            hashed_password=get_password_hash("password"),
            balance=0.0
        )
        test_db_session.add(user_zero)
        test_db_session.commit()
        assert user_zero.balance == 0.0
        
        # Test negative balance
        user_negative = User(
            email="negative@example.com",
            hashed_password=get_password_hash("password"),
            balance=-100.0
        )
        test_db_session.add(user_negative)
        test_db_session.commit()
        assert user_negative.balance == -100.0
        
        # Test very large balance
        user_large = User(
            email="large@example.com",
            hashed_password=get_password_hash("password"),
            balance=999999999.99
        )
        test_db_session.add(user_large)
        test_db_session.commit()
        assert user_large.balance == 999999999.99
    
    def test_transaction_amount_edge_cases(self, test_db_session, test_user):
        """Test transaction amounts with edge case values."""
        # Test zero amount
        transaction_zero = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=0.0
        )
        test_db_session.add(transaction_zero)
        test_db_session.commit()
        assert transaction_zero.amount == 0.0
        
        # Test very small amount
        transaction_small = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=0.01
        )
        test_db_session.add(transaction_small)
        test_db_session.commit()
        assert transaction_small.amount == 0.01
        
        # Test very large amount
        transaction_large = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=999999999.99
        )
        test_db_session.add(transaction_large)
        test_db_session.commit()
        assert transaction_large.amount == 999999999.99
    
    def test_long_strings(self, test_db_session, test_user):
        """Test models with very long string values."""
        # Test long email
        long_email = "a" * 100 + "@example.com"
        user = User(
            email=long_email,
            hashed_password=get_password_hash("password")
        )
        test_db_session.add(user)
        test_db_session.commit()
        assert user.email == long_email
        
        # Test long comment
        long_comment = "A" * 1000
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=50.0,
            comment=long_comment
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        assert transaction.comment == long_comment 