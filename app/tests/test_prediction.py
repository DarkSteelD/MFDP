"""
Tests for prediction endpoints and ML functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status
from faker import Faker
import tempfile
import os
from io import BytesIO

from src.db.models import Transaction

fake = Faker()

class TestImagePrediction:
    """Test image prediction functionality."""
    
    @patch('src.routes.prediction.connect_robust')
    def test_predict_image_success(self, mock_connect, authenticated_client, test_user, test_image_base64, test_db_session):
        """Test successful image prediction."""
        # Mock RabbitMQ connection
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_queue = AsyncMock()
        
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_queue.return_value = mock_queue
        
        initial_balance = test_user.balance
        
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["credits_spent"] == 50.0
        assert data["text_prediction"] is None
        assert data["image_prediction"] is not None
        assert f"mask_{test_user.id}_image.png" in data["image_prediction"]
        
        # Verify balance was deducted
        test_db_session.refresh(test_user)
        assert test_user.balance == initial_balance - 50.0
        
        # Verify transaction was created
        transaction = test_db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.type == "prediction"
        ).first()
        assert transaction is not None
        assert transaction.amount == 50.0
    
    def test_predict_image_insufficient_balance(self, authenticated_client, test_user, test_image_base64, test_db_session):
        """Test image prediction with insufficient balance."""
        # Set user balance to 0
        test_user.balance = 0.0
        test_db_session.commit()
        
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient balance" in response.json()["detail"]
    
    def test_predict_image_unauthorized(self, test_client, test_image_base64):
        """Test image prediction without authentication."""
        response = test_client.post("/predict/", json={
            "image": test_image_base64
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_predict_image_invalid_data(self, authenticated_client):
        """Test image prediction with invalid base64 data."""
        response = authenticated_client.post("/predict/", json={
            "image": "invalid_base64_data"
        })
        
        # Should still process but may fail in worker
        assert response.status_code == status.HTTP_200_OK
    
    def test_predict_image_missing_data(self, authenticated_client):
        """Test image prediction without image data."""
        response = authenticated_client.post("/predict/", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestScan3DPrediction:
    """Test 3D scan prediction functionality."""
    
    def create_test_nifti_file(self):
        """Create a temporary test NIfTI file."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
        temp_file.write(b"fake_nifti_data")
        temp_file.close()
        return temp_file.name
    
    @patch('src.routes.prediction.connect_robust')
    def test_predict_3d_scan_success(self, mock_connect, authenticated_client, test_user, test_db_session):
        """Test successful 3D scan prediction."""
        # Mock RabbitMQ connection
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_queue = AsyncMock()
        
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_queue.return_value = mock_queue
        
        # Create test file
        test_file_path = self.create_test_nifti_file()
        
        try:
            initial_balance = test_user.balance
            
            with open(test_file_path, 'rb') as f:
                response = authenticated_client.post("/predict/3d-scan", 
                    files={"scan": ("test_scan.nii.gz", f, "application/gzip")}
                )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["credits_spent"] == 100.0
            assert "brain_mask_url" in data
            assert "aneurysm_mask_url" in data
            assert "original_scan_url" in data
            assert f"brain_mask_{test_user.id}_test_scan.nii.gz" in data["brain_mask_url"]
            assert f"aneurysm_mask_{test_user.id}_test_scan.nii.gz" in data["aneurysm_mask_url"]
            
            # Verify balance was deducted
            test_db_session.refresh(test_user)
            assert test_user.balance == initial_balance - 100.0
            
            # Verify transaction was created
            transaction = test_db_session.query(Transaction).filter(
                Transaction.user_id == test_user.id,
                Transaction.type == "scan3d"
            ).first()
            assert transaction is not None
            assert transaction.amount == 100.0
            
        finally:
            # Cleanup
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_predict_3d_scan_invalid_format(self, authenticated_client):
        """Test 3D scan prediction with invalid file format."""
        # Create a regular text file
        test_data = BytesIO(b"not a nifti file")
        
        response = authenticated_client.post("/predict/3d-scan", 
            files={"scan": ("test_scan.txt", test_data, "text/plain")}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file format" in response.json()["detail"]
    
    def test_predict_3d_scan_insufficient_balance(self, authenticated_client, test_user, test_db_session):
        """Test 3D scan prediction with insufficient balance."""
        # Set user balance to 0
        test_user.balance = 0.0
        test_db_session.commit()
        
        test_file_path = self.create_test_nifti_file()
        
        try:
            with open(test_file_path, 'rb') as f:
                response = authenticated_client.post("/predict/3d-scan", 
                    files={"scan": ("test_scan.nii.gz", f, "application/gzip")}
                )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Insufficient balance" in response.json()["detail"]
            
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_predict_3d_scan_unauthorized(self, test_client):
        """Test 3D scan prediction without authentication."""
        test_data = BytesIO(b"fake_nifti_data")
        
        response = test_client.post("/predict/3d-scan", 
            files={"scan": ("test_scan.nii.gz", test_data, "application/gzip")}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_predict_3d_scan_no_file(self, authenticated_client):
        """Test 3D scan prediction without file."""
        response = authenticated_client.post("/predict/3d-scan")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestPredictionIntegration:
    """Integration tests for prediction functionality."""
    
    @patch('src.routes.prediction.connect_robust')
    def test_multiple_predictions_balance_deduction(self, mock_connect, authenticated_client, test_user, test_image_base64, test_db_session):
        """Test multiple predictions correctly deduct balance."""
        # Mock RabbitMQ
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        initial_balance = test_user.balance
        num_predictions = 3
        
        for i in range(num_predictions):
            response = authenticated_client.post("/predict/", json={
                "image": test_image_base64
            })
            assert response.status_code == status.HTTP_200_OK
        
        # Check final balance
        test_db_session.refresh(test_user)
        expected_balance = initial_balance - (50.0 * num_predictions)
        assert test_user.balance == expected_balance
        
        # Check transactions
        transactions = test_db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.type == "prediction"
        ).all()
        assert len(transactions) == num_predictions
    
    @patch('src.routes.prediction.connect_robust')
    def test_prediction_after_topup(self, mock_connect, authenticated_client, test_user, test_image_base64, test_db_session):
        """Test prediction works after balance top-up."""
        # Mock RabbitMQ
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        # Set balance to exactly enough for one prediction
        test_user.balance = 50.0
        test_db_session.commit()
        
        # Make one prediction
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        assert response.status_code == status.HTTP_200_OK
        
        # Now balance should be 0
        test_db_session.refresh(test_user)
        assert test_user.balance == 0.0
        
        # Try another prediction - should fail
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Top up balance
        topup_response = authenticated_client.post("/balance/topup", json={
            "amount": 100.0
        })
        assert topup_response.status_code == status.HTTP_201_CREATED
        
        # Now prediction should work again
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        assert response.status_code == status.HTTP_200_OK
    
    @patch('src.routes.prediction.connect_robust')
    def test_rabbitmq_connection_failure(self, mock_connect, authenticated_client, test_image_base64):
        """Test prediction handling when RabbitMQ connection fails."""
        # Mock RabbitMQ connection to raise exception
        mock_connect.side_effect = Exception("RabbitMQ connection failed")
        
        response = authenticated_client.post("/predict/", json={
            "image": test_image_base64
        })
        
        # Should return 500 Internal Server Error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_prediction_file_upload_size_limit(self, authenticated_client):
        """Test 3D scan prediction with large file."""
        # Create a large file (simulating size limit testing)
        large_data = BytesIO(b"x" * (10 * 1024 * 1024))  # 10MB
        
        response = authenticated_client.post("/predict/3d-scan", 
            files={"scan": ("large_scan.nii.gz", large_data, "application/gzip")}
        )
        
        # Should either process or reject based on file size limits
        # This test documents current behavior
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, status.HTTP_400_BAD_REQUEST]

class TestPredictionSecurity:
    """Security tests for prediction endpoints."""
    
    def test_prediction_with_expired_token(self, test_client, test_image_base64):
        """Test prediction with expired JWT token."""
        # Create an expired token (this would need actual token expiry logic)
        expired_token = "expired.jwt.token"
        
        response = test_client.post("/predict/", 
            json={"image": test_image_base64},
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_prediction_with_malformed_token(self, test_client, test_image_base64):
        """Test prediction with malformed JWT token."""
        malformed_token = "malformed_token"
        
        response = test_client.post("/predict/", 
            json={"image": test_image_base64},
            headers={"Authorization": f"Bearer {malformed_token}"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_prediction_sql_injection_attempt(self, authenticated_client):
        """Test prediction endpoints against SQL injection."""
        # Try to inject SQL in image data
        malicious_input = "'; DROP TABLE users; --"
        
        response = authenticated_client.post("/predict/", json={
            "image": malicious_input
        })
        
        # Should not cause SQL injection (handled by ORM)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY] 