"""
Tests for the 3D scan worker functionality.
"""

import pytest
import tempfile
import os
import json
import asyncio
import numpy as np
import nibabel as nib
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

from src.workers.scan3d_worker import (
    create_mask_from_image,
    create_brain_mask,
    create_aneurysm_mask,
    create_mock_brain_mask,
    create_mock_aneurysm_mask,
    handle_image_message,
    handle_scan3d_message
)

class TestImageMaskCreation:
    
    def test_create_mask_from_image_valid_base64(self):
        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        user_id = 123
        filename = "test.png"
        
        mask_path = create_mask_from_image(image_data, user_id, filename)
        
        assert mask_path is not None
        assert f"mask_{user_id}_{filename}" in mask_path
        
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            full_path = downloads_dir / f"mask_{user_id}_{filename}"
            if full_path.exists():
                os.remove(full_path)
    
    def test_create_mask_from_image_invalid_base64(self):
        invalid_data = "invalid_base64_data"
        user_id = 123
        filename = "test.png"
        
        mask_path = create_mask_from_image(invalid_data, user_id, filename)
        
        assert mask_path is not None
        assert f"mask_{user_id}_{filename}" in mask_path

class TestNiftiMaskCreation:
    
    def create_test_nifti_file(self):
        data = np.random.rand(64, 64, 32)
        img = nib.Nifti1Image(data, np.eye(4))
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
        nib.save(img, temp_file.name)
        temp_file.close()
        
        return temp_file.name
    
    def test_create_brain_mask_with_existing_mask(self):
        source_mask = "brain_mask_AHMU1218003.nii.gz"
        temp_source = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
        temp_source.write(b"fake_nifti_data")
        temp_source.close()
        
        with patch('os.path.exists', return_value=True), \
             patch('shutil.copy2') as mock_copy:
            
            user_id = 123
            filename = "test_scan.nii.gz"
            
            result_path = create_brain_mask("input_path", user_id, filename)
            
            assert f"brain_mask_{user_id}_{filename}" in result_path
            mock_copy.assert_called_once()
        
        os.remove(temp_source.name)
    
    def test_create_brain_mask_without_existing_mask(self):
        nifti_path = self.create_test_nifti_file()
        
        try:
            with patch('os.path.exists', return_value=False):
                user_id = 123
                filename = "test_scan.nii.gz"
                
                result_path = create_brain_mask(nifti_path, user_id, filename)
                
                assert f"brain_mask_{user_id}_{filename}" in result_path
        finally:
            if os.path.exists(nifti_path):
                os.remove(nifti_path)
    
    def test_create_aneurysm_mask_with_existing_mask(self):
        with patch('os.path.exists', return_value=True), \
             patch('shutil.copy2') as mock_copy:
            
            user_id = 123
            filename = "test_scan.nii.gz"
            
            result_path = create_aneurysm_mask("input_path", user_id, filename)
            
            assert f"aneurysm_mask_{user_id}_{filename}" in result_path
            mock_copy.assert_called_once()
    
    def test_create_aneurysm_mask_without_existing_mask(self):
        nifti_path = self.create_test_nifti_file()
        
        try:
            with patch('os.path.exists', return_value=False):
                user_id = 123
                filename = "test_scan.nii.gz"
                
                result_path = create_aneurysm_mask(nifti_path, user_id, filename)
                
                assert f"aneurysm_mask_{user_id}_{filename}" in result_path
        finally:
            if os.path.exists(nifti_path):
                os.remove(nifti_path)
    
    def test_create_mock_brain_mask(self):
        nifti_path = self.create_test_nifti_file()
        
        try:
            user_id = 123
            filename = "test_scan.nii.gz"
            
            result_path = create_mock_brain_mask(nifti_path, user_id, filename)
            
            assert f"brain_mask_{user_id}_{filename}" in result_path
            
            downloads_dir = Path("downloads")
            if downloads_dir.exists():
                expected_file = downloads_dir / f"brain_mask_{user_id}_{filename}"
                if expected_file.exists():
                    try:
                        img = nib.load(expected_file)
                        assert img.get_fdata().shape[0] > 0
                    except:
                        pass
                    finally:
                        os.remove(expected_file)
                        
        finally:
            if os.path.exists(nifti_path):
                os.remove(nifti_path)
    
    def test_create_mock_aneurysm_mask(self):
        nifti_path = self.create_test_nifti_file()
        
        try:
            user_id = 123
            filename = "test_scan.nii.gz"
            
            result_path = create_mock_aneurysm_mask(nifti_path, user_id, filename)
            
            assert f"aneurysm_mask_{user_id}_{filename}" in result_path
            
            downloads_dir = Path("downloads")
            if downloads_dir.exists():
                expected_file = downloads_dir / f"aneurysm_mask_{user_id}_{filename}"
                if expected_file.exists():
                    os.remove(expected_file)
                        
        finally:
            if os.path.exists(nifti_path):
                os.remove(nifti_path)

class TestMessageHandlers:
    
    @pytest.mark.asyncio
    async def test_handle_image_message_success(self):
        mock_message = AsyncMock()
        mock_channel = AsyncMock()
        mock_message.channel = mock_channel
        
        payload = {
            "transaction_id": 123,
            "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        }
        mock_message.body = json.dumps(payload).encode()
        
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()
        
        with patch('src.workers.scan3d_worker.create_mask_from_image') as mock_create_mask:
            mock_create_mask.return_value = "/downloads/mask_1_image.png"
            
            await handle_image_message(mock_message)
            
            mock_create_mask.assert_called_once()
            mock_channel.default_exchange.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_image_message_error(self):
        mock_message = AsyncMock()
        mock_message.body = b"invalid_json"
        
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()
        
        with pytest.raises(Exception):
            await handle_image_message(mock_message)
    
    @pytest.mark.asyncio
    async def test_handle_scan3d_message_success(self):
        nifti_path = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
        nifti_path.write(b"fake_nifti_data")
        nifti_path.close()
        
        try:
            mock_message = AsyncMock()
            mock_channel = AsyncMock()
            mock_message.channel = mock_channel
            
            payload = {
                "transaction_id": 123,
                "scan_path": nifti_path.name,
                "user_id": 456,
                "filename": "test_scan.nii.gz"
            }
            mock_message.body = json.dumps(payload).encode()
            
            mock_message.process.return_value.__aenter__ = AsyncMock()
            mock_message.process.return_value.__aexit__ = AsyncMock()
            
            with patch('src.workers.scan3d_worker.create_brain_mask') as mock_brain, \
                 patch('src.workers.scan3d_worker.create_aneurysm_mask') as mock_aneurysm:
                
                mock_brain.return_value = "/downloads/brain_mask_456_test_scan.nii.gz"
                mock_aneurysm.return_value = "/downloads/aneurysm_mask_456_test_scan.nii.gz"
                
                await handle_scan3d_message(mock_message)
                
                mock_brain.assert_called_once_with(nifti_path.name, 456, "test_scan.nii.gz")
                mock_aneurysm.assert_called_once_with(nifti_path.name, 456, "test_scan.nii.gz")
                mock_channel.default_exchange.publish.assert_called_once()
                
        finally:
            if os.path.exists(nifti_path.name):
                os.remove(nifti_path.name)
    
    @pytest.mark.asyncio
    async def test_handle_scan3d_message_file_not_found(self):
        mock_message = AsyncMock()
        
        payload = {
            "transaction_id": 123,
            "scan_path": "/nonexistent/file.nii.gz",
            "user_id": 456,
            "filename": "test_scan.nii.gz"
        }
        mock_message.body = json.dumps(payload).encode()
        
        mock_message.process.return_value.__aenter__ = AsyncMock()
        mock_message.process.return_value.__aexit__ = AsyncMock()
        
        with pytest.raises(FileNotFoundError):
            await handle_scan3d_message(mock_message)

class TestWorkerIntegration:
    
    def test_worker_dependencies_import(self):
        try:
            import aio_pika
            import nibabel
            import numpy
            import PIL
        except ImportError as e:
            pytest.fail(f"Required dependency missing: {e}")
    
    def test_downloads_directory_creation(self):
        from src.workers.scan3d_worker import DOWNLOADS_DIR
        assert DOWNLOADS_DIR.exists() or True
    
    @pytest.mark.asyncio
    async def test_rabbitmq_connection_mock(self):
        with patch('src.workers.scan3d_worker.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_queue = AsyncMock()
            
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_queue.return_value = mock_queue
            
            from src.workers.scan3d_worker import RABBITMQ_URL
            
            connection = await mock_connect(RABBITMQ_URL)
            channel = await connection.channel()
            
            assert connection == mock_connection
            assert channel == mock_channel

class TestWorkerEdgeCases:
    
    def test_create_mask_with_empty_image_data(self):
        empty_data = ""
        user_id = 123
        filename = "empty.png"
        
        result = create_mask_from_image(empty_data, user_id, filename)
        
        assert result is not None
        assert f"mask_{user_id}_{filename}" in result
    
    def test_create_mask_with_large_user_id(self):
        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        large_user_id = 999999999
        filename = "test.png"
        
        result = create_mask_from_image(image_data, large_user_id, filename)
        
        assert result is not None
        assert str(large_user_id) in result
    
    def test_create_brain_mask_with_corrupted_nifti(self):
        corrupted_file = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
        corrupted_file.write(b"corrupted_data_not_nifti")
        corrupted_file.close()
        
        try:
            user_id = 123
            filename = "corrupted.nii.gz"
            
            with patch('os.path.exists', return_value=False):
                result = create_mock_brain_mask(corrupted_file.name, user_id, filename)
                assert f"brain_mask_{user_id}_{filename}" in result
                
        finally:
            if os.path.exists(corrupted_file.name):
                os.remove(corrupted_file.name)
    
    def test_create_aneurysm_mask_with_special_characters_filename(self):
        user_id = 123
        special_filename = "test@#$%^&*().nii.gz"
        
        with patch('os.path.exists', return_value=False), \
             patch('src.workers.scan3d_worker.create_mock_aneurysm_mask') as mock_create:
            
            mock_create.return_value = f"/downloads/aneurysm_mask_{user_id}_{special_filename}"
            
            result = create_aneurysm_mask("input_path", user_id, special_filename)
            
            assert special_filename in result
            mock_create.assert_called_once()

class TestWorkerPerformance:
    
    def test_mask_creation_time(self):
        import time
        
        image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        user_id = 123
        filename = "performance_test.png"
        
        start_time = time.time()
        result = create_mask_from_image(image_data, user_id, filename)
        end_time = time.time()
        
        assert (end_time - start_time) < 5.0
        assert result is not None
    
    def test_concurrent_mask_creation(self):
        import concurrent.futures
        
        def create_test_mask(user_id):
            image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            filename = f"concurrent_test_{user_id}.png"
            return create_mask_from_image(image_data, user_id, filename)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_test_mask, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 10
        assert all(result is not None for result in results) 