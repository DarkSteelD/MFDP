"""
Tests for authentication endpoints and security functions.
"""

import pytest
from fastapi import status
from faker import Faker

from src.core.security import verify_password, get_password_hash, create_access_token
from src.db.models import User

fake = Faker()

class TestUserRegistration:
    
    def test_register_user_success(self, test_client, test_user_data):
        response = test_client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data
        assert data["balance"] == 0.0
        assert data["is_admin"] is False
        assert data["is_active"] is True
    
    def test_register_user_duplicate_email(self, test_client, test_user, test_user_data):
        response = test_client.post("/auth/register", json={
            "email": test_user.email,
            "password": "different_password"
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_user_invalid_email(self, test_client):
        response = test_client.post("/auth/register", json={
            "email": "invalid-email",
            "password": "valid_password123"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_user_weak_password(self, test_client):
        response = test_client.post("/auth/register", json={
            "email": fake.email(),
            "password": "123"
        })
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]

class TestUserLogin:
    
    def test_login_success(self, test_client, test_user, test_user_data):
        response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_email(self, test_client):
        response = test_client.post("/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "any_password"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_wrong_password(self, test_client, test_user, test_user_data):
        response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": "wrong_password"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_inactive_user(self, test_client, test_db_session, test_user_data):
        inactive_user = User(
            email=test_user_data["email"],
            hashed_password=get_password_hash(test_user_data["password"]),
            balance=0.0,
            is_admin=False,
            is_active=False
        )
        test_db_session.add(inactive_user)
        test_db_session.commit()
        
        response = test_client.post("/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == status.HTTP_200_OK

class TestSecurityFunctions:
    
    def test_password_hashing(self):
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self):
        user_id = "12345"
        token = create_access_token(data={"sub": user_id})
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
        assert token.count('.') == 2

class TestAuthenticationIntegration:
    
    def test_register_and_login_flow(self, test_client):
        user_data = {
            "email": fake.email(),
            "password": fake.password(length=12)
        }
        
        register_response = test_client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        login_response = test_client.post("/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == status.HTTP_200_OK
        assert "access_token" in login_response.json()
    
    def test_protected_endpoint_with_valid_token(self, authenticated_client):
        response = authenticated_client.get("/balance/")
        assert response.status_code == status.HTTP_200_OK
    
    def test_protected_endpoint_without_token(self, test_client):
        response = test_client.get("/balance/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_invalid_token(self, test_client):
        response = test_client.get("/balance/", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 