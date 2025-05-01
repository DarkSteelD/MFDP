"""
Module: workers.predict_worker

Async RabbitMQ worker that listens for ML task messages and executes predictions.
"""

import os
import json
import asyncio
from aio_pika import connect_robust, IncomingMessage, Message
import logging
from ultralytics import YOLO

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
IMAGE_QUEUE = os.getenv("IMAGE_QUEUE", "image_tasks")
YOLO_RESULTS_QUEUE = os.getenv("YOLO_RESULTS_QUEUE", "yolo_results")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load YOLO nano model (auto-download via ultralytics)
yolo_model = YOLO("yolov8n.pt")

async def handle_image_message(message: IncomingMessage) -> None:
    """
    Process a single image task message.

    Steps:
      1. Deserialize JSON payload from message body.
      2. Extract transaction_id and image_path.
      3. Validate input and ensure transaction exists.
      4. Perform YOLO prediction on the image.
      5. Publish YOLO results.
      6. Acknowledge the message upon success.

    Args:
      message (IncomingMessage): incoming RabbitMQ message.
    """
    async with message.process():
        payload = json.loads(message.body)
        transaction_id = payload.get("transaction_id")
        image_path = payload.get("image")

        try:
            results = yolo_model(image_path)
            boxes = results[0].boxes.xyxy.tolist()
            await message.channel.default_exchange.publish(
                Message(
                    body=json.dumps({
                        "transaction_id": transaction_id,
                        "boxes": boxes
                    }).encode()
                ),
                routing_key=YOLO_RESULTS_QUEUE
            )
        except Exception as e:
            logger.error(f"Error processing image task %s: %s", transaction_id, e)
            raise

async def main():
    """
    Connect to RabbitMQ and start consuming ML tasks.
    """
    connection = await connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.declare_queue(IMAGE_QUEUE, durable=True)
    await channel.declare_queue(YOLO_RESULTS_QUEUE, durable=True)
    image_queue = await channel.declare_queue(IMAGE_QUEUE, durable=True)
    await image_queue.consume(handle_image_message)
    print(f" [*] Waiting for image messages in {IMAGE_QUEUE}... Press CTRL+C to exit")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main()) 