"""
Tests for transaction endpoints and functionality.
"""

import pytest
from fastapi import status
from faker import Faker
from datetime import datetime, timezone

from src.db.models import Transaction

fake = Faker()

class TestGetTransactions:
    """Test transaction retrieval functionality."""
    
    def test_get_transactions_empty(self, authenticated_client, test_user):
        """Test getting transactions when user has no transactions."""
        response = authenticated_client.get("/transactions/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_transactions_with_data(self, authenticated_client, test_user, test_db_session):
        """Test getting transactions when user has transactions."""
        # Create test transactions
        transactions = [
            Transaction(
                user_id=test_user.id,
                type="deposit",
                amount=100.0,
                comment="Test deposit 1"
            ),
            Transaction(
                user_id=test_user.id,
                type="prediction",
                amount=50.0
            ),
            Transaction(
                user_id=test_user.id,
                type="deposit",
                amount=75.5,
                comment="Test deposit 2"
            )
        ]
        
        for transaction in transactions:
            test_db_session.add(transaction)
        test_db_session.commit()
        
        response = authenticated_client.get("/transactions/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Check transactions are returned in descending timestamp order
        timestamps = [item["timestamp"] for item in data]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Verify transaction details
        for item in data:
            assert "id" in item
            assert "user_id" in item
            assert "type" in item
            assert "amount" in item
            assert "timestamp" in item
            assert item["user_id"] == test_user.id
            assert item["type"] in ["deposit", "prediction", "scan3d"]
    
    def test_get_transactions_unauthorized(self, test_client):
        """Test getting transactions without authentication."""
        response = test_client.get("/transactions/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_transactions_only_user_transactions(self, test_client, test_db_session):
        """Test that users only see their own transactions."""
        # Create two users with transactions
        from src.core.security import get_password_hash, create_access_token
        from src.db.models import User
        
        user1 = User(
            email="user1@example.com",
            hashed_password=get_password_hash("password1"),
            balance=100.0
        )
        user2 = User(
            email="user2@example.com",
            hashed_password=get_password_hash("password2"),
            balance=200.0
        )
        test_db_session.add(user1)
        test_db_session.add(user2)
        test_db_session.commit()
        
        # Create transactions for both users
        user1_transaction = Transaction(
            user_id=user1.id,
            type="deposit",
            amount=50.0,
            comment="User 1 deposit"
        )
        user2_transaction = Transaction(
            user_id=user2.id,
            type="deposit",
            amount=75.0,
            comment="User 2 deposit"
        )
        test_db_session.add(user1_transaction)
        test_db_session.add(user2_transaction)
        test_db_session.commit()
        
        # Login as user1 and check transactions
        token1 = create_access_token(data={"sub": str(user1.id)})
        response = test_client.get("/transactions/", headers={
            "Authorization": f"Bearer {token1}"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["comment"] == "User 1 deposit"
        assert data[0]["user_id"] == user1.id

class TestTransactionModel:
    """Test transaction model functionality."""
    
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
        assert isinstance(transaction.timestamp, datetime)
    
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
        
        assert transaction.id is not None
        assert transaction.type == "prediction"
        assert transaction.amount == 50.0
        assert transaction.comment is None
    
    def test_create_scan3d_transaction(self, test_db_session, test_user):
        """Test creating a 3D scan transaction."""
        transaction = Transaction(
            user_id=test_user.id,
            type="scan3d",
            amount=100.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.type == "scan3d"
        assert transaction.amount == 100.0
    
    def test_transaction_timestamp_auto_creation(self, test_db_session, test_user):
        """Test that timestamp is automatically set when creating transaction."""
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
    
    def test_transaction_user_relationship(self, test_db_session, test_user):
        """Test transaction relationship with user."""
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=50.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        # Access user through relationship
        assert transaction.user.id == test_user.id
        assert transaction.user.email == test_user.email

class TestTransactionIntegration:
    """Integration tests for transaction functionality."""
    
    def test_transaction_creation_through_topup(self, authenticated_client, test_user, test_db_session):
        """Test that transaction is created when user tops up balance."""
        response = authenticated_client.post("/balance/topup", json={
            "amount": 150.0,
            "comment": "Integration test topup"
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check transaction was created
        transactions_response = authenticated_client.get("/transactions/")
        assert transactions_response.status_code == status.HTTP_200_OK
        
        transactions = transactions_response.json()
        assert len(transactions) >= 1
        
        # Find the deposit transaction
        deposit_transaction = None
        for t in transactions:
            if t["type"] == "deposit" and t["amount"] == 150.0:
                deposit_transaction = t
                break
        
        assert deposit_transaction is not None
        assert deposit_transaction["comment"] == "Integration test topup"
    
    def test_transaction_creation_through_prediction(self, authenticated_client, test_user, test_image_base64, test_db_session):
        """Test that transaction is created when user makes prediction."""
        # Mock RabbitMQ to avoid actual message publishing
        from unittest.mock import patch, AsyncMock
        
        with patch('src.routes.prediction.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            
            response = authenticated_client.post("/predict/", json={
                "image": test_image_base64
            })
            
            assert response.status_code == status.HTTP_200_OK
        
        # Check transaction was created
        transactions_response = authenticated_client.get("/transactions/")
        assert transactions_response.status_code == status.HTTP_200_OK
        
        transactions = transactions_response.json()
        prediction_transactions = [t for t in transactions if t["type"] == "prediction"]
        assert len(prediction_transactions) >= 1
        assert prediction_transactions[0]["amount"] == 50.0
    
    def test_transaction_history_pagination(self, authenticated_client, test_user, test_db_session):
        """Test transaction history with many transactions."""
        # Create many transactions
        for i in range(25):
            transaction = Transaction(
                user_id=test_user.id,
                type="deposit",
                amount=10.0 + i,
                comment=f"Test transaction {i}"
            )
            test_db_session.add(transaction)
        test_db_session.commit()
        
        response = authenticated_client.get("/transactions/")
        assert response.status_code == status.HTTP_200_OK
        
        transactions = response.json()
        assert len(transactions) == 25
        
        # Verify they're in descending timestamp order
        for i in range(len(transactions) - 1):
            current_timestamp = datetime.fromisoformat(transactions[i]["timestamp"].replace('Z', '+00:00'))
            next_timestamp = datetime.fromisoformat(transactions[i + 1]["timestamp"].replace('Z', '+00:00'))
            assert current_timestamp >= next_timestamp

class TestTransactionEdgeCases:
    """Test edge cases and error conditions for transactions."""
    
    def test_transaction_with_zero_amount(self, test_db_session, test_user):
        """Test creating transaction with zero amount."""
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=0.0
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.amount == 0.0
    
    def test_transaction_with_large_amount(self, test_db_session, test_user):
        """Test creating transaction with very large amount."""
        large_amount = 999999999.99
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=large_amount
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.amount == large_amount
    
    def test_transaction_with_long_comment(self, test_db_session, test_user):
        """Test creating transaction with very long comment."""
        long_comment = "A" * 1000  # Very long comment
        transaction = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=50.0,
            comment=long_comment
        )
        test_db_session.add(transaction)
        test_db_session.commit()
        test_db_session.refresh(transaction)
        
        assert transaction.comment == long_comment
    
    def test_transaction_invalid_type(self, test_db_session, test_user):
        """Test creating transaction with invalid type."""
        # This should raise an error at the database level
        # since TransactionType enum only allows specific values
        with pytest.raises(Exception):  # Could be ValueError or database constraint error
            transaction = Transaction(
                user_id=test_user.id,
                type="invalid_type",
                amount=50.0
            )
            test_db_session.add(transaction)
            test_db_session.commit() 