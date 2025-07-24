"""
Tests for balance management endpoints.
"""

import pytest
from fastapi import status
from faker import Faker

from src.db.models import Transaction

fake = Faker()

class TestGetBalance:
    """Test balance retrieval functionality."""
    
    def test_get_balance_success(self, authenticated_client, test_user):
        """Test successful balance retrieval."""
        response = authenticated_client.get("/balance/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["balance"] == test_user.balance
        assert isinstance(data["balance"], (int, float))
    
    def test_get_balance_unauthorized(self, test_client):
        """Test balance retrieval without authentication."""
        response = test_client.get("/balance/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_balance_with_transactions(self, authenticated_client, test_user, test_db_session):
        """Test balance retrieval after transactions."""
        # Add some transactions
        deposit = Transaction(
            user_id=test_user.id,
            type="deposit",
            amount=50.0,
            comment="Test deposit"
        )
        prediction = Transaction(
            user_id=test_user.id,
            type="prediction",
            amount=25.0
        )
        test_db_session.add(deposit)
        test_db_session.add(prediction)
        test_db_session.commit()
        
        response = authenticated_client.get("/balance/")
        assert response.status_code == status.HTTP_200_OK
        # Balance should remain same as transactions don't affect balance in this endpoint
        assert response.json()["balance"] == test_user.balance

class TestTopUpBalance:
    """Test balance top-up functionality."""
    
    def test_topup_success(self, authenticated_client, test_user, test_db_session):
        """Test successful balance top-up."""
        initial_balance = test_user.balance
        topup_amount = 100.0
        
        response = authenticated_client.post("/balance/topup", json={
            "amount": topup_amount,
            "comment": "Test top-up"
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == test_user.id
        assert data["balance"] == initial_balance + topup_amount
        
        # Verify transaction was created
        transaction = test_db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.type == "deposit"
        ).order_by(Transaction.timestamp.desc()).first()
        
        assert transaction is not None
        assert transaction.amount == topup_amount
        assert transaction.comment == "Test top-up"
    
    def test_topup_without_comment(self, authenticated_client, test_user):
        """Test top-up without comment."""
        response = authenticated_client.post("/balance/topup", json={
            "amount": 50.0
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["balance"] == test_user.balance + 50.0
    
    def test_topup_negative_amount(self, authenticated_client):
        """Test top-up with negative amount."""
        response = authenticated_client.post("/balance/topup", json={
            "amount": -50.0
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_topup_zero_amount(self, authenticated_client):
        """Test top-up with zero amount."""
        response = authenticated_client.post("/balance/topup", json={
            "amount": 0.0
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_topup_invalid_amount_type(self, authenticated_client):
        """Test top-up with invalid amount type."""
        response = authenticated_client.post("/balance/topup", json={
            "amount": "invalid"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_topup_unauthorized(self, test_client):
        """Test top-up without authentication."""
        response = test_client.post("/balance/topup", json={
            "amount": 100.0
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_topup_large_amount(self, authenticated_client, test_user):
        """Test top-up with large amount."""
        large_amount = 999999.99
        response = authenticated_client.post("/balance/topup", json={
            "amount": large_amount
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["balance"] == test_user.balance + large_amount
    
    def test_topup_decimal_precision(self, authenticated_client, test_user):
        """Test top-up with decimal precision."""
        precise_amount = 123.456789
        response = authenticated_client.post("/balance/topup", json={
            "amount": precise_amount
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        # Check that decimal precision is handled correctly
        expected_balance = test_user.balance + precise_amount
        assert abs(response.json()["balance"] - expected_balance) < 0.01

class TestBalanceIntegration:
    """Integration tests for balance operations."""
    
    def test_multiple_topups(self, authenticated_client, test_user, test_db_session):
        """Test multiple consecutive top-ups."""
        initial_balance = test_user.balance
        amounts = [50.0, 25.5, 100.0, 75.25]
        
        for amount in amounts:
            response = authenticated_client.post("/balance/topup", json={
                "amount": amount,
                "comment": f"Top-up {amount}"
            })
            assert response.status_code == status.HTTP_201_CREATED
        
        # Check final balance
        response = authenticated_client.get("/balance/")
        expected_balance = initial_balance + sum(amounts)
        assert abs(response.json()["balance"] - expected_balance) < 0.01
        
        # Check transactions count
        transactions = test_db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.type == "deposit"
        ).all()
        assert len(transactions) >= len(amounts)
    
    def test_balance_persistence(self, test_client, test_user_data, test_db_session):
        """Test that balance persists across sessions."""
        # Register and login
        test_client.post("/auth/register", json=test_user_data)
        login_response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Top up balance
        topup_amount = 150.0
        test_client.post("/balance/topup", json={"amount": topup_amount}, headers=headers)
        
        # Check balance persists
        balance_response = test_client.get("/balance/", headers=headers)
        assert balance_response.json()["balance"] == topup_amount
        
        # Simulate new session (new login)
        new_login_response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        new_token = new_login_response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        # Balance should still be there
        new_balance_response = test_client.get("/balance/", headers=new_headers)
        assert new_balance_response.json()["balance"] == topup_amount
    
    def test_concurrent_topups(self, test_client, test_user_data, test_db_session):
        """Test handling of concurrent balance operations."""
        # Register user
        test_client.post("/auth/register", json=test_user_data)
        login_response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Simulate concurrent top-ups
        amounts = [10.0, 20.0, 30.0]
        responses = []
        
        for amount in amounts:
            response = test_client.post("/balance/topup", json={
                "amount": amount
            }, headers=headers)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED
        
        # Final balance should be sum of all top-ups
        final_response = test_client.get("/balance/", headers=headers)
        assert final_response.json()["balance"] == sum(amounts) 