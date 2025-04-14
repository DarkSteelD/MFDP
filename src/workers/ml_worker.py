import json
import os
import pika
import time
from typing import Dict, Any, Optional, Callable, Type
import logging
from PIL import Image
import io
import base64

from ml.model_gen import ModelForGeneration
from ml.model_classification import ModelForClassification
from ml.model_vis import ModelForVisTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ml_worker")

TASK_TEXT_GENERATION = "text_generation"
TASK_SPAM_DETECTION = "spam_detection"
TASK_IMAGE_CAPTION = "image_caption"

class MLWorker:
    
    def __init__(self, rabbitmq_url: str, queue_name: str = "ml_tasks"):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.models = {}
        self._initialize_models()
        
    def _initialize_models(self):
        self._model_initializers = {
            TASK_TEXT_GENERATION: lambda: ModelForGeneration.create_llama_model("7b"),
            TASK_SPAM_DETECTION: lambda: ModelForClassification.create_spam_detector(),
            TASK_IMAGE_CAPTION: lambda: ModelForVisTransformer.create_vit_image_captioner()
        }
        
    def _get_model(self, task_type: str):
        if task_type not in self.models:
            if task_type in self._model_initializers:
                logger.info(f"Initializing model for {task_type}")
                self.models[task_type] = self._model_initializers[task_type]()
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
        return self.models[task_type]
        
    def connect(self):
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info(f"Connected to RabbitMQ, listening on queue: {self.queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
            
    def _validate_task(self, task_data: Dict[str, Any]) -> bool:
        if not isinstance(task_data, dict):
            logger.error("Task data is not a dictionary")
            return False
            
        if 'task_type' not in task_data:
            logger.error("Task type not specified")
            return False
            
        task_type = task_data['task_type']
        
        if task_type not in self._model_initializers:
            logger.error(f"Unsupported task type: {task_type}")
            return False
            
        if task_type == TASK_TEXT_GENERATION:
            if 'text' not in task_data:
                logger.error("Missing 'text' field for text generation task")
                return False
                
        elif task_type == TASK_SPAM_DETECTION:
            if 'text' not in task_data:
                logger.error("Missing 'text' field for spam detection task")
                return False
                
        elif task_type == TASK_IMAGE_CAPTION:
            if 'image_data' not in task_data:
                logger.error("Missing 'image_data' field for image caption task")
                return False
                
        return True
        
    def _process_text_generation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        model = self._get_model(TASK_TEXT_GENERATION)
        text = task_data['text']
        max_length = task_data.get('max_length', 100)
        temperature = task_data.get('temperature', 0.7)
        
        result = model.generate(text, max_length=max_length, temperature=temperature)
        return {"generated_text": result}
        
    def _process_spam_detection(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        model = self._get_model(TASK_SPAM_DETECTION)
        text = task_data['text']
        
        if task_data.get('detailed', False):
            result = model.classificate_with_scores(text)
            return {"classification": "spam" if "spam" in result and result["spam"] > 0.5 else "ham", 
                   "scores": result}
        else:
            result = model.classificate(text)
            return {"classification": result}
            
    def _process_image_caption(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        model = self._get_model(TASK_IMAGE_CAPTION)
        
        image_data = task_data['image_data']
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Failed to decode image: {e}")
            return {"error": "Invalid image data"}
            
        caption = model.generate(input_image=image)
        return {"caption": caption}
        
    def _process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data['task_type']
        task_id = task_data.get('task_id', 'unknown')
        
        logger.info(f"Processing task {task_id} of type {task_type}")
        
        try:
            if task_type == TASK_TEXT_GENERATION:
                return self._process_text_generation(task_data)
            elif task_type == TASK_SPAM_DETECTION:
                return self._process_spam_detection(task_data)
            elif task_type == TASK_IMAGE_CAPTION:
                return self._process_image_caption(task_data)
            else:
                return {"error": f"Unsupported task type: {task_type}"}
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            return {"error": str(e)}
            
    def _callback(self, ch, method, properties, body):
        try:
            task_data = json.loads(body)
            task_id = task_data.get('task_id', 'unknown')
            
            logger.info(f"Received task {task_id}")
            
            if not self._validate_task(task_data):
                logger.error(f"Invalid task data for task {task_id}")
                result = {"error": "Invalid task data"}
            else:
                result = self._process_task(task_data)
                
            result['task_id'] = task_id
            
            if properties.reply_to:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    ),
                    body=json.dumps(result)
                )
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
            logger.info(f"Completed task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
    def start(self):
        if not self.channel:
            if not self.connect():
                return False
                
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._callback
            )
            
            logger.info("Starting to consume messages. Press CTRL+C to exit.")
            self.channel.start_consuming()
            
            return True
        except KeyboardInterrupt:
            logger.info("Interrupted by user, shutting down...")
            self.stop()
            return True
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            return False
            
    def stop(self):
        if self.channel:
            try:
                self.channel.stop_consuming()
            except Exception:
                pass
                
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
                
        logger.info("Worker stopped")
        
def run_worker(rabbitmq_url: str, queue_name: str = "ml_tasks"):
    worker = MLWorker(rabbitmq_url, queue_name)
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    finally:
        worker.stop()

if __name__ == "__main__":
    rabbitmq_url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    queue_name = os.environ.get("QUEUE_NAME", "ml_tasks")
    
    run_worker(rabbitmq_url, queue_name) 