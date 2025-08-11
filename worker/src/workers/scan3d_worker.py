"""
Module: workers.scan3d_worker

Async RabbitMQ worker that listens for image and 3D scan analysis tasks.
"""

import os
import json
import asyncio
import shutil
import base64
from pathlib import Path
from aio_pika import connect_robust, IncomingMessage, Message
import logging
import nibabel as nib
import numpy as np
from PIL import Image
import io

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
IMAGE_QUEUE = os.getenv("IMAGE_QUEUE", "image_tasks")
SCAN3D_QUEUE = os.getenv("SCAN3D_QUEUE", "scan3d_tasks")
RESULTS_QUEUE = os.getenv("RESULTS_QUEUE", "results")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create downloads directory if it doesn't exist
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

def create_mask_from_image(image_data: str, user_id: int, filename: str) -> str:
    """
    Create a mask from an image (mock implementation).
    
    Args:
        image_data (str): base64 encoded image data
        user_id (int): user ID for file naming
        filename (str): original filename
        
    Returns:
        str: path to the generated mask
    """
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create a simple mask (center region)
        mask = Image.new('L', image.size, 0)
        center_x, center_y = image.size[0] // 2, image.size[1] // 2
        size_x, size_y = image.size[0] // 3, image.size[1] // 3
        
        # Create a simple rectangular mask in the center
        x_start = max(0, center_x - size_x // 2)
        x_end = min(image.size[0], center_x + size_x // 2)
        y_start = max(0, center_y - size_y // 2)
        y_end = min(image.size[1], center_y + size_y // 2)
        
        # Fill the mask region
        for x in range(x_start, x_end):
            for y in range(y_start, y_end):
                mask.putpixel((x, y), 128)  # Semi-transparent
        
        # Save the mask
        mask_filename = f"mask_{user_id}_{filename}"
        mask_path = DOWNLOADS_DIR / mask_filename
        mask.save(mask_path, 'PNG')
        
        return str(mask_path)
    except Exception as e:
        logger.error(f"Error creating mask from image: {e}")
        return f"/downloads/mask_{user_id}_{filename}"

def create_brain_mask(nifti_path: str, user_id: int, filename: str) -> str:
    """
    Create a brain mask from the input scan.
    
    For now, this is a mock implementation that returns the existing brain mask.
    In a real implementation, this would use a brain segmentation model.
    
    Args:
        nifti_path (str): path to the input NIfTI file
        user_id (int): user ID for file naming
        filename (str): original filename
        
    Returns:
        str: path to the generated brain mask
    """
    # For now, copy the existing brain mask as a mock
    source_brain_mask = "brain_mask_AHMU1218003.nii.gz"
    if os.path.exists(source_brain_mask):
        output_path = DOWNLOADS_DIR / f"brain_mask_{user_id}_{filename}"
        shutil.copy2(source_brain_mask, output_path)
        return str(output_path)
    else:
        # If no existing mask, create a simple mock mask
        logger.warning(f"Brain mask file {source_brain_mask} not found, creating mock mask")
        return create_mock_brain_mask(nifti_path, user_id, filename)

def create_aneurysm_mask(nifti_path: str, user_id: int, filename: str) -> str:
    """
    Create an aneurysm mask from the input scan.
    
    For now, this is a mock implementation that returns the existing aneurysm mask.
    In a real implementation, this would use an aneurysm detection model.
    
    Args:
        nifti_path (str): path to the input NIfTI file
        user_id (int): user ID for file naming
        filename (str): original filename
        
    Returns:
        str: path to the generated aneurysm mask
    """
    # For now, copy the existing aneurysm mask as a mock
    source_aneurysm_mask = "aneurysm_mask_AHMU1218003.nii.gz"
    if os.path.exists(source_aneurysm_mask):
        output_path = DOWNLOADS_DIR / f"aneurysm_mask_{user_id}_{filename}"
        shutil.copy2(source_aneurysm_mask, output_path)
        return str(output_path)
    else:
        # If no existing mask, create a simple mock mask
        logger.warning(f"Aneurysm mask file {source_aneurysm_mask} not found, creating mock mask")
        return create_mock_aneurysm_mask(nifti_path, user_id, filename)

def create_mock_brain_mask(nifti_path: str, user_id: int, filename: str) -> str:
    """
    Create a mock brain mask for testing purposes.
    
    Args:
        nifti_path (str): path to the input NIfTI file
        user_id (int): user ID for file naming
        filename (str): original filename
        
    Returns:
        str: path to the generated mock brain mask
    """
    try:
        # Load the original scan to get dimensions
        img = nib.load(nifti_path)
        data = img.get_fdata()
        
        # Create a simple brain mask (center region)
        mask = np.zeros_like(data)
        center_x, center_y, center_z = np.array(data.shape) // 2
        size_x, size_y, size_z = np.array(data.shape) // 3
        
        x_start = max(0, center_x - size_x // 2)
        x_end = min(data.shape[0], center_x + size_x // 2)
        y_start = max(0, center_y - size_y // 2)
        y_end = min(data.shape[1], center_y + size_y // 2)
        z_start = max(0, center_z - size_z // 2)
        z_end = min(data.shape[2], center_z + size_z // 2)
        
        mask[x_start:x_end, y_start:y_end, z_start:z_end] = 1
        
        # Save the mask
        mask_img = nib.Nifti1Image(mask, img.affine, img.header)
        output_path = DOWNLOADS_DIR / f"brain_mask_{user_id}_{filename}"
        nib.save(mask_img, output_path)
        
        return str(output_path)
    except Exception as e:
        logger.error(f"Error creating mock brain mask: {e}")
        # Return a fallback path
        return f"/downloads/brain_mask_{user_id}_{filename}"

def create_mock_aneurysm_mask(nifti_path: str, user_id: int, filename: str) -> str:
    """
    Create a mock aneurysm mask for testing purposes.
    
    Args:
        nifti_path (str): path to the input NIfTI file
        user_id (int): user ID for file naming
        filename (str): original filename
        
    Returns:
        str: path to the generated mock aneurysm mask
    """
    try:
        # Load the original scan to get dimensions
        img = nib.load(nifti_path)
        data = img.get_fdata()
        
        # Create a simple aneurysm mask (small region in center)
        mask = np.zeros_like(data)
        center_x, center_y, center_z = np.array(data.shape) // 2
        
        # Create a small spherical region
        x, y, z = np.ogrid[:data.shape[0], :data.shape[1], :data.shape[2]]
        radius = min(data.shape) // 10
        mask_region = (x - center_x)**2 + (y - center_y)**2 + (z - center_z)**2 <= radius**2
        mask[mask_region] = 1
        
        # Save the mask
        mask_img = nib.Nifti1Image(mask, img.affine, img.header)
        output_path = DOWNLOADS_DIR / f"aneurysm_mask_{user_id}_{filename}"
        nib.save(mask_img, output_path)
        
        return str(output_path)
    except Exception as e:
        logger.error(f"Error creating mock aneurysm mask: {e}")
        # Return a fallback path
        return f"/downloads/aneurysm_mask_{user_id}_{filename}"

async def handle_image_message(message: IncomingMessage) -> None:
    """
    Process a single image task message.

    Args:
      message (IncomingMessage): incoming RabbitMQ message.
    """
    async with message.process():
        payload = json.loads(message.body)
        transaction_id = payload.get("transaction_id")
        image_data = payload.get("image")

        try:
            logger.info(f"Processing image task: {transaction_id}")
            
            # Create mask from image
            mask_path = create_mask_from_image(image_data, 1, "image.png")  # Mock user_id
            logger.info(f"Mask created: {mask_path}")
            
            # Publish results
            await message.channel.default_exchange.publish(
                Message(
                    body=json.dumps({
                        "transaction_id": transaction_id,
                        "mask_path": mask_path,
                        "type": "image"
                    }).encode()
                ),
                routing_key=RESULTS_QUEUE
            )
            
            logger.info(f"Image processing completed for transaction {transaction_id}")
            
        except Exception as e:
            logger.error(f"Error processing image task {transaction_id}: {e}")
            raise

async def handle_scan3d_message(message: IncomingMessage) -> None:
    """
    Process a single 3D scan analysis task message.

    Args:
      message (IncomingMessage): incoming RabbitMQ message.
    """
    async with message.process():
        payload = json.loads(message.body)
        transaction_id = payload.get("transaction_id")
        scan_path = payload.get("scan_path")
        user_id = payload.get("user_id")
        filename = payload.get("filename")

        try:
            logger.info(f"Processing 3D scan: {scan_path}")
            
            # Validate scan file exists
            if not os.path.exists(scan_path):
                raise FileNotFoundError(f"Scan file not found: {scan_path}")
            
            # Create brain mask
            brain_mask_path = create_brain_mask(scan_path, user_id, filename)
            logger.info(f"Brain mask created: {brain_mask_path}")
            
            # Create aneurysm mask
            aneurysm_mask_path = create_aneurysm_mask(scan_path, user_id, filename)
            logger.info(f"Aneurysm mask created: {aneurysm_mask_path}")
            
            # Publish results
            await message.channel.default_exchange.publish(
                Message(
                    body=json.dumps({
                        "transaction_id": transaction_id,
                        "brain_mask_path": brain_mask_path,
                        "aneurysm_mask_path": aneurysm_mask_path,
                        "user_id": user_id,
                        "filename": filename,
                        "type": "scan3d"
                    }).encode()
                ),
                routing_key=RESULTS_QUEUE
            )
            
            logger.info(f"3D scan analysis completed for transaction {transaction_id}")
            
        except Exception as e:
            logger.error(f"Error processing 3D scan task {transaction_id}: {e}")
            raise

async def main():
    """
    Connect to RabbitMQ and start consuming both image and 3D scan tasks.
    """
    connection = await connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    # Declare all queues
    await channel.declare_queue(IMAGE_QUEUE, durable=True)
    await channel.declare_queue(SCAN3D_QUEUE, durable=True)
    await channel.declare_queue(RESULTS_QUEUE, durable=True)
    
    # Start consuming from both queues
    image_queue = await channel.declare_queue(IMAGE_QUEUE, durable=True)
    scan3d_queue = await channel.declare_queue(SCAN3D_QUEUE, durable=True)
    
    await image_queue.consume(handle_image_message)
    await scan3d_queue.consume(handle_scan3d_message)
    
    print(f" [*] Waiting for messages in {IMAGE_QUEUE} and {SCAN3D_QUEUE}... Press CTRL+C to exit")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main()) 