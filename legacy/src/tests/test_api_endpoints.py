import pytest
import pytest_asyncio
import json
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from sqlalchemy.future import select
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
import io
from datetime import datetime
import uuid

from src.main import app # Import app normally
from src.database.models import User, MLModel, Prediction, Transaction
from src.api.auth import create_access_token, get_password_hash, get_current_active_user, verify_password
from src.api.schemas import TransactionResponse

# --- Fixtures for Patching Core DB Functions ---

@pytest.fixture(scope="session", autouse=True)
def patch_init_db():
    """Patches init_db for the entire test session."""
    with patch("src.database.init_db.init_db", return_value=None) as p:
        yield p

@pytest.fixture(scope="session", autouse=True)
def patch_create_engine():
    """Patches create_async_engine for the entire test session."""
    # Return a mock engine that can be used by sessionmaker
    mock_engine = MagicMock()
    # Mock dispose if it's called during cleanup
    mock_engine.dispose = MagicMock()
    # If using AsyncEngine, mock required async methods if needed
    # mock_engine.connect = AsyncMock() 
    with patch("src.database.config.create_async_engine", return_value=mock_engine) as p:
        yield p

# Create a fixture for a mock user
@pytest.fixture
def mock_user_fixture():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.balance = 100
    user.is_admin = False
    return user

# Create a fixture for a mock admin user
@pytest.fixture
def mock_admin_fixture():
    admin = MagicMock(spec=User)
    admin.id = 2
    admin.username = "testadmin"
    admin.email = "admin@example.com"
    admin.balance = 1000
    admin.is_admin = True
    return admin

# Test client for FastAPI using the app with overridden dependency
client = TestClient(app)

# --- Helper Context Manager for Dependency Override ---
@contextmanager
def override_dependency(dependency, mock_object):
    """Temporarily overrides a FastAPI dependency for a test."""
    original_dependency = app.dependency_overrides.get(dependency)
    app.dependency_overrides[dependency] = lambda: mock_object
    try:
        yield
    finally:
        # Restore original override or remove if none existed
        if original_dependency:
            app.dependency_overrides[dependency] = original_dependency
        else:
            del app.dependency_overrides[dependency]

# Test user registration with a mocked database
@patch("src.api.endpoints.users.get_session")
def test_user_registration(mock_get_session):
    # Configure mock session
    mock_session = MagicMock()
    # Mock the async context manager behavior
    mock_get_session.return_value.__aenter__.return_value = mock_session 
    # Mock database query results
    mock_session.execute.return_value.scalar_one_or_none.side_effect = [
        None, # First check for "testuser" - doesn't exist
        MagicMock(), # Second check for "existing_user" - exists
    ] 
    
    # Test valid registration
    response = client.post(
        "/users/register", 
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    
    # Test with duplicate username
    response = client.post(
        "/users/register", 
        json={
            "username": "existing_user",
            "email": "new@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    
    # Test with invalid data
    response = client.post(
        "/users/register", 
        json={
            "username": "user"  # Missing required fields
        }
    )
    assert response.status_code == 422

# Test login with a mocked database
@patch("src.api.auth.get_session") # Patch session used by authenticate_user
@patch("src.api.auth.authenticate_user")
def test_login(mock_auth, mock_auth_get_session):
    # Configure mock session for authenticate_user
    mock_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_session
    # Mock user found by authenticate_user's query
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_user.password_hash = get_password_hash("password123") # Need a valid hash for verify
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

    # Configure mock auth function (will use the fetched mock_user)
    mock_auth.side_effect = lambda username, password, session: \
        mock_user if username == "testuser" and verify_password(password, mock_user.password_hash) else None

    # Test valid login
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Configure mock to return failed authentication
    mock_auth.return_value = None
    
    # Test invalid login
    response = client.post(
        "/token",
        data={
            "username": "wronguser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

# Test balance endpoint with a mocked database
@patch("src.api.auth.get_session") # Patch session used by get_current_user
def test_get_balance(mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_session
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency for this test
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Test get balance
        response = client.get("/users/balance", headers={"Authorization": "Bearer dummytoken"})
        assert response.status_code == 200
        assert response.json()["balance"] == 100

# Test authenticated endpoints
@patch("src.api.auth.get_session") # Patch session used by get_current_user
def test_get_user_info(mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_session
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Use a dummy token
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer dummytoken"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

def test_get_user_info_no_token():
    response = client.get("/users/me")
    assert response.status_code == 401 # Unauthorized

# Test balance endpoints
@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.api.endpoints.balance.get_session") 
def test_add_balance(mock_balance_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Reset balance for idempotency
    mock_user_fixture.balance = 100
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for balance endpoint
        mock_session = MagicMock()
        mock_balance_get_session.return_value.__aenter__.return_value = mock_session 
        mock_session.execute.return_value.scalar_one.return_value = mock_user_fixture

        # Use a dummy token
        response = client.post(
            "/users/balance/add",
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": 50}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["change"] == 50
        assert data["valid"] == True
        # Verify the balance was conceptually updated 
        assert mock_user_fixture.balance == 150 

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.api.endpoints.balance.get_session") 
def test_add_balance_negative_amount(mock_balance_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Reset balance for this test case
    mock_user_fixture.balance = 100 
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for balance endpoint
        mock_session = MagicMock()
        mock_balance_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one.return_value = mock_user_fixture
        
        # Use a dummy token
        response = client.post(
            "/users/balance/add",
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": -50}  # Negative amount
        )
        
        # Assuming negative amounts are invalid input, expect 422
        assert response.status_code == 422 # Adjusted expectation
        # Optional: Check error detail if needed
        # assert "Value must be positive" in response.json()["detail"][0]["msg"]

# Test prediction endpoints
@patch("src.api.endpoints.predictions.time.time") 
@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_make_prediction(mock_pred_get_session, mock_auth_get_session, mock_time, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Reset balance
    mock_user_fixture.balance = 100
    # Mock time.time() calls
    mock_time.side_effect = [1000.0, 1000.5] # Start and end times
    
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session

        mock_model = MagicMock()
        mock_model.id = 1
        mock_model.cost = 50 # Set cost if needed by logic (seems hardcoded in endpoint)
        # Mock the select(...).filter(...).scalar_one_or_none()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_model

        # Use a dummy token
        response = client.post(
            "/ml/predict",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "model_id": 1,
                "input_data": {"text": "This is a test message"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["model_id"] == 1
        assert data["successful"] == True
        assert data["execution_time"] == 500.0 # (1000.5 - 1000.0) * 1000
        # Check balance deduction happened on the fixture
        assert mock_user_fixture.balance == 50

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_make_prediction_insufficient_balance(mock_pred_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Configure mock user with insufficient balance
    mock_user_fixture.balance = 10 
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session

        mock_model = MagicMock()
        mock_model.id = 1
        mock_model.cost = 50 
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_model

        # Use a dummy token
        response = client.post(
            "/ml/predict",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "model_id": 1,
                "input_data": {"text": "This is a test message"}
            }
        )
        
        assert response.status_code == 402 # Payment Required
        assert "Insufficient balance" in response.json()["detail"]

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_get_user_predictions(mock_pred_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session

        # Mock the database query result for predictions
        mock_prediction = MagicMock()
        mock_prediction.id = 1
        mock_prediction.input_data = {"text": "input"}
        mock_prediction.output_data = {"result": "output"}
        # ... other attributes ...
        # Mock the select(...).filter(...).scalars().all()
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_prediction]

        # Use a dummy token
        response = client.get(
            "/ml/predictions",
            headers={"Authorization": "Bearer dummytoken"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "input_data" in data[0]
        assert "output_data" in data[0]

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_get_specific_prediction(mock_pred_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session

        # Mock the database query result for a specific prediction
        mock_prediction = MagicMock()
        mock_prediction.id = 123
        mock_prediction.user_id = mock_user_fixture.id 
        # ... other attributes ...
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_prediction

        # Use a dummy token
        response = client.get(
            "/ml/predictions/123", # Specific prediction ID
            headers={"Authorization": "Bearer dummytoken"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123

# Test spam detection endpoint
@patch("src.api.ml_api.get_task_producer") # Patch the dependency function
@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.api.ml_api.check_user_balance", return_value=True) # Patch balance check directly
def test_spam_detection(mock_check_balance, mock_auth_get_session, mock_get_producer, mock_user_fixture):
    # Mock the auth session lookup
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Configure mock producer and its method
    mock_producer = MagicMock()
    # Mock the specific method called by the endpoint
    mock_producer.send_spam_detection_task.return_value = {"task_id": "spam-123", "status": "completed", "classification": "not_spam"} 
    mock_get_producer.return_value = mock_producer
    
    # Reset balance if needed (though patched)
    mock_user_fixture.balance = 100
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Use a dummy token
        response = client.post(
            "/ml-tasks/detect-spam", # Path defined in ml_api.py
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "text": "This is a test message for spam detection",
                "detailed": True # wait=True is default in endpoint
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "spam-123"
        assert data["status"] == "completed"
        assert data["classification"] == "not_spam"
        # Check if the correct method was called on the mock producer
        mock_producer.send_spam_detection_task.assert_called_once()
        # Assert balance check was called
        mock_check_balance.assert_called_once()

# Test text generation endpoint
@patch("src.api.ml_api.get_task_producer") # Patch the dependency function
@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.api.ml_api.check_user_balance", return_value=True) # Patch balance check
def test_text_generation(mock_check_balance, mock_auth_get_session, mock_get_producer, mock_user_fixture):
    # Mock the auth session lookup
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Configure mock producer
    mock_producer = MagicMock()
    mock_producer.send_text_generation_task.return_value = {"task_id": "gen-456", "status": "completed", "generated_text": "mock text"}
    mock_get_producer.return_value = mock_producer
    # Reset balance
    mock_user_fixture.balance = 100
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Use a dummy token
        response = client.post(
            "/ml-tasks/generate-text", # Path defined in ml_api.py
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "text": "This is a prompt for text generation",
                "max_length": 50,
                "temperature": 0.7 # wait=True is default
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "gen-456"
        assert data["status"] == "completed"
        assert data["generated_text"] == "mock text"
        mock_producer.send_text_generation_task.assert_called_once()
        mock_check_balance.assert_called_once()

# Test admin-only endpoints
@patch("src.api.ml_api.get_session") 
@patch("src.api.auth.get_session") # Patch session used by get_current_admin_user -> get_current_user
def test_update_user_balance_as_admin(mock_auth_get_session, mock_ml_api_get_session, mock_admin_fixture):
    # Mock the auth session lookup for get_current_admin_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_admin_fixture

    # Override dependency with admin user
    # Need to use get_current_admin_user here for the endpoint check
    with override_dependency(get_current_active_user, mock_admin_fixture): # Use admin fixture
        # Configure mock session for the endpoint itself
        mock_endpoint_session = MagicMock()
        mock_ml_api_get_session.return_value.__aenter__.return_value = mock_endpoint_session
        
        # Mock the target user being fetched by the endpoint session
        mock_target_user = MagicMock()
        mock_target_user.id = 1
        mock_target_user.balance = 50
        # Mock the select(...).filter(...).scalar_one_or_none() call in endpoint
        mock_endpoint_session.execute.return_value.scalar_one_or_none.return_value = mock_target_user

        # Use a dummy token
        response = client.post(
            "/ml-tasks/admin/update-balance/1",  # Path defined in ml_api.py
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": 100} # Sending JSON, not form data
        )
        assert response.status_code == 200
        data = response.json()
        # The endpoint returns the updated user object, check balance there
        assert data["balance"] == 150 # 50 + 100

@patch("src.api.auth.get_session") # Patch session used by get_current_admin_user -> get_current_user
def test_update_user_balance_as_regular_user(mock_auth_get_session, mock_user_fixture):
    # Mock the auth session lookup for get_current_admin_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    # Simulate user found by get_current_user, but they are not admin
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture 

    # Override dependency with regular user
    # Endpoint uses Depends(get_current_admin_user), which internally calls Depends(get_current_user)
    # So overriding get_current_active_user should suffice for the internal check
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Use a dummy token
        response = client.post(
            "/ml-tasks/admin/update-balance/1", # Path from ml_api.py
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": 100}
        )
        # Expect Forbidden because the user from the token is not admin
        assert response.status_code == 403  

# Tests for invalid data formats
@patch("src.api.endpoints.users.get_session")
def test_register_with_invalid_data(mock_get_session):
    # Configure mock session for duplicate check
    mock_session = MagicMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session 
    # Mock check for username "testuser" - assume it exists for this check
    mock_session.execute.return_value.scalar_one_or_none.return_value = MagicMock() 

    # Test with missing required fields
    response = client.post(
        "/users/register",
        json={
            "username": "testuser"  # Missing email and password
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test with invalid email format
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123"
        }
    )
    assert response.status_code == 422  # Validation error

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_predict_with_invalid_model_id(mock_pred_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock execute to return None for the invalid model ID
        mock_session.execute.return_value.scalar_one_or_none.return_value = None # Model not found

        # Use dummy token
        response = client.post(
            "/ml/predict",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "model_id": 9999,  # Non-existent model ID
                "input_data": {"text": "This is a test message"}
            }
        )
        assert response.status_code == 404
    
@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.api.endpoints.balance.get_session") 
def test_add_balance_with_zero_amount(mock_balance_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for balance endpoint
        mock_session = MagicMock()
        mock_balance_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.return_value.scalar_one.return_value = mock_user_fixture

        # Use dummy token
        response = client.post(
            "/users/balance/add",
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": 0}  # Zero amount
        )
        
        # Assuming zero is invalid based on previous logic
        assert response.status_code in [400, 422]

def test_invalid_token_format():
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token_format"}
    )
    assert response.status_code == 401

@patch("src.api.auth.get_session") # Patch session used by get_current_user
@patch("src.database.config.get_session") # Patch session used by prediction endpoint
def test_predict_zero_balance_check(mock_pred_get_session, mock_auth_get_session, mock_user_fixture):
    # Mock the session execute call within get_current_user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Mock user with zero balance
    mock_user_fixture.balance = 0
    # Override dependency
    with override_dependency(get_current_active_user, mock_user_fixture):
        # Configure mock session for prediction endpoint
        mock_session = MagicMock()
        mock_pred_get_session.return_value.__aenter__.return_value = mock_session
        
        mock_model = MagicMock(cost=50) 
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_model
        
        response = client.post(
            "/ml/predict",
            headers={"Authorization": "Bearer dummytoken"},
            json={"model_id": 1, "input_data": {"text": "Test"}}
        )
        assert response.status_code == 402

@patch("src.api.ml_api.check_user_balance", return_value=True) # Assume user has balance
@patch("src.api.auth.get_session") 
def test_text_generation_with_invalid_data(mock_auth_get_session, mock_check_balance, mock_user_fixture):
    # Mock auth session lookup
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    with override_dependency(get_current_active_user, mock_user_fixture):
        # Test with negative max_length
        response = client.post(
            "/ml-tasks/generate-text",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "text": "This is a prompt",
                "max_length": -50,  # Invalid negative value
                "temperature": 0.7
            }
        )
        assert response.status_code == 422  # Validation error
        
        # Test with temperature out of range
        response = client.post(
            "/ml-tasks/generate-text",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "text": "This is a prompt",
                "max_length": 50,
                "temperature": 2.5  # Should be <= 1.0 based on common sense
            }
        )
        assert response.status_code == 422  # Validation error

# Test spam detection with empty text (Endpoint now active)
@patch("src.api.ml_api.get_task_producer")
@patch("src.api.ml_api.check_user_balance", return_value=True)
@patch("src.api.auth.get_session")
def test_spam_detection_with_empty_text(mock_auth_get_session, mock_check_balance, mock_get_producer, mock_user_fixture):
    # Mock auth session
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Mock producer
    mock_producer = MagicMock()
    mock_producer.send_spam_detection_task.return_value = {"task_id": "spam-empty", "status": "completed", "classification": "not_spam"} 
    mock_get_producer.return_value = mock_producer

    with override_dependency(get_current_active_user, mock_user_fixture):
        response = client.post(
            "/ml-tasks/detect-spam",
            headers={"Authorization": "Bearer dummytoken"},
            json={
                "text": "",
                "detailed": True
            }
        )
        # Empty text might be valid input, should get a result
        assert response.status_code == 200 
        data = response.json()
        assert data["task_id"] == "spam-empty"
        mock_producer.send_spam_detection_task.assert_called_once()
        mock_check_balance.assert_called_once()

# Patch balance check directly to return False
@patch("src.api.ml_api.check_user_balance", return_value=False)
@patch("src.api.auth.get_session") 
def test_spam_detection_zero_balance_check(mock_auth_get_session, mock_check_balance, mock_user_fixture):
    # Mock auth session
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    with override_dependency(get_current_active_user, mock_user_fixture):
        response = client.post(
            "/ml-tasks/detect-spam",
            headers={"Authorization": "Bearer dummytoken"},
            json={"text": "Test"}
        )
        assert response.status_code == 402 # Payment required
        mock_check_balance.assert_called_once()

# Remove redundant test_admin_view_all_transactions (already commented out above)

# Remove redundant test_prediction_with_mixed_valid_invalid_data (keep commented out for now) 

# --- New tests to cover full spec per requirements ---

@patch("src.database.config.get_session")
def test_list_models(mock_get_session):
    """GET /ml/models should return a list of active ML models."""
    mock_session = MagicMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session

    # Create a fake MLModel
    from src.database.models import MLModel
    now = datetime.utcnow()
    mock_model = MagicMock(spec=MLModel)
    mock_model.id = 1
    mock_model.name = "TestModel"
    mock_model.description = "A test ML model"
    mock_model.version = "v1.0"
    mock_model.creation_date = now
    mock_model.is_active = True
    mock_model.model_type = "classification"
    mock_model.parameters = {"param": "value"}
    mock_model.metrics = {"accuracy": 0.95}

    fake_result = MagicMock()
    fake_result.scalars.return_value.all.return_value = [mock_model]
    mock_session.execute.return_value = fake_result

    response = client.get("/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["name"] == "TestModel"
    assert data[0]["model_type"] == "classification"
    assert data[0]["parameters"] == {"param": "value"}
    assert data[0]["metrics"] == {"accuracy": 0.95}

@patch("src.database.config.get_session")
def test_get_model_by_id(mock_get_session):
    """GET /ml/models/{id} should return the specific model when it exists."""
    mock_session = MagicMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session

    from src.database.models import MLModel
    now = datetime.utcnow()
    mock_model = MagicMock(spec=MLModel)
    mock_model.id = 2
    mock_model.name = "OtherModel"
    mock_model.description = "Another model"
    mock_model.version = "v2.1"
    mock_model.creation_date = now
    mock_model.is_active = True
    mock_model.model_type = "regression"
    mock_model.parameters = {}
    mock_model.metrics = {}

    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_model

    response = client.get("/ml/models/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["version"] == "v2.1"
    assert data["is_active"] is True

@patch("src.api.endpoints.balance.get_session")
@patch("src.api.auth.get_session")
def test_get_transactions(mock_balance_get_session, mock_auth_get_session, mock_user_fixture):
    """GET /users/transactions should return a user's transaction history."""
    # Mock current_user lookup
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    with override_dependency(get_current_active_user, mock_user_fixture):
        # Mock transactions query
        mock_session = MagicMock()
        mock_balance_get_session.return_value.__aenter__.return_value = mock_session

        from src.database.models import Transaction
        now = datetime.utcnow()
        mock_trans = MagicMock(spec=Transaction)
        mock_trans.id = 1
        mock_trans.user_id = mock_user_fixture.id
        mock_trans.change = 50
        mock_trans.valid = True
        mock_trans.time = now

        fake_result = MagicMock()
        fake_result.scalars.return_value.all.return_value = [mock_trans]
        mock_session.execute.return_value = fake_result

        response = client.get("/users/transactions", headers={"Authorization": "Bearer dummytoken"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) and data[0]["change"] == 50 and data[0]["valid"] is True

@patch("src.api.ml_api.get_task_producer")
@patch("src.api.auth.get_session")
@patch("src.api.ml_api.check_user_balance", return_value=True)
def test_caption_image(mock_check_balance, mock_auth_get_session, mock_get_producer, mock_user_fixture):
    """POST /ml-tasks/caption-image should enqueue and return a caption task result."""
    # Mock auth & balance
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # Mock producer
    mock_producer = MagicMock()
    mock_producer.send_image_caption_task.return_value = {
        "task_id": "image-123",
        "caption": "A sample caption",
        "execution_time": 123.4,
        "prediction_id": 7
    }
    mock_get_producer.return_value = mock_producer

    with override_dependency(get_current_active_user, mock_user_fixture):
        files = {"file": ("test.png", b"fakeimagebytes", "image/png")}
        response = client.post(
            "/ml-tasks/caption-image",
            headers={"Authorization": "Bearer dummytoken"},
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "image-123"
        assert data["caption"] == "A sample caption"
        assert data["prediction_id"] == 7

@patch("src.api.auth.get_session")
def test_initiate_payment(mock_auth_get_session, mock_user_fixture):
    """POST /payments/initiate should return a pending payment with redirect_url."""
    # Mock user context
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    with override_dependency(get_current_active_user, mock_user_fixture):
        response = client.post(
            "/payments/initiate",
            headers={"Authorization": "Bearer dummytoken"},
            json={"amount": 100, "payment_method": "card", "payment_details": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_id" in data
        assert data["status"] == "pending"
        assert data["amount"] == 100
        assert data["redirect_url"].startswith("https://")

@patch("src.api.ml_api.get_session")
def test_payment_callback_success(mock_get_session):
    """GET /payments/callback with status=completed should credit the user."""
    mock_session = MagicMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session

    from src.database.models import User
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.balance = 0

    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

    params = {"payment_id": "pay123", "status": "completed", "amount": 50, "signature": "sig"}
    response = client.get("/payments/callback", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Payment processed successfully" in data["message"]
    assert mock_user.balance == 50

@patch("src.api.ml_api.get_session")
def test_payment_callback_error(mock_get_session):
    """GET /payments/callback with non‐completed status should return an error."""
    mock_session = MagicMock()
    mock_get_session.return_value.__aenter__.return_value = mock_session

    params = {"payment_id": "pay123", "status": "failed", "amount": 50, "signature": "sig"}
    response = client.get("/payments/callback", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "failed" in data["message"].lower()

def test_root_and_health():
    """GET / and GET /health should report service status."""
    # Root
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert "message" in json_data

    # Health
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 

# --- Admin‐only transaction listing tests ---

@patch("src.api.ml_api.get_session")
@patch("src.api.auth.get_session")
def test_admin_list_all_transactions(mock_auth_get_session, mock_ml_api_get_session, mock_admin_fixture):
    """
    GET /ml-tasks/admin/transactions should return all transactions
    for an admin user.
    """
    # 1) Mock authentication to return the admin fixture
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_admin_fixture

    # 2) Override admin dependency so get_current_admin_user() yields our admin
    with override_dependency(get_current_admin_user, mock_admin_fixture):
        # 3) Prepare the DB session mock to return a list of transactions
        mock_session = MagicMock()
        mock_ml_api_get_session.return_value.__aenter__.return_value = mock_session

        from src.database.models import Transaction
        now = datetime.utcnow()
        mock_txn = MagicMock(spec=Transaction)
        mock_txn.id = 42
        mock_txn.user_id = 7
        mock_txn.change = 250
        mock_txn.valid = True
        mock_txn.time = now

        fake_result = MagicMock()
        fake_result.scalars.return_value.all.return_value = [mock_txn]
        mock_session.execute.return_value = fake_result

        # 4) Fire the request
        response = client.get(
            "/ml-tasks/admin/transactions",
            headers={"Authorization": "Bearer dummytoken"}
        )

        # 5) Assert correct behavior
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["id"] == 42
        assert data[0]["change"] == 250
        assert data[0]["valid"] is True

@patch("src.api.auth.get_session")
def test_admin_list_all_transactions_forbidden(mock_auth_get_session, mock_user_fixture):
    """
    Non-admin users get 403 Forbidden when accessing
    GET /ml-tasks/admin/transactions.
    """
    # Mock get_session for auth to return a regular user
    mock_auth_session = MagicMock()
    mock_auth_get_session.return_value.__aenter__.return_value = mock_auth_session
    mock_auth_session.execute.return_value.scalar_one_or_none.return_value = mock_user_fixture

    # No override for get_current_admin_user → should raise 403
    response = client.get(
        "/ml-tasks/admin/transactions",
        headers={"Authorization": "Bearer dummytoken"}
    )
    assert response.status_code == 403 

@app.get("/admin/transactions", response_model=List[TransactionResponse])
async def list_all_transactions(
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Admin view: list every transaction in the system."""
    query = select(Transaction)
    result = await session.execute(query)
    return result.scalars().all() 