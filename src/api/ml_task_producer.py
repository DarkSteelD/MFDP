import json
import uuid
import pika
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ml_task_producer")

class MLTaskProducer:
    """Producer class that sends ML tasks to a RabbitMQ queue."""
    
    def __init__(self, rabbitmq_url: str, queue_name: str = "ml_tasks"):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.responses = {}
        self.corr_id = None
        
    def connect(self) -> bool:
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.callback_queue = result.method.queue
            
            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self._on_response,
                auto_ack=True
            )
            
            logger.info(f"Connected to RabbitMQ, publishing to queue: {self.queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def _on_response(self, ch, method, props, body):
        if props.correlation_id in self.responses:
            self.responses[props.correlation_id] = json.loads(body)
    
    def send_task(self, task_data: Dict[str, Any], wait_for_response: bool = False, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.channel:
            if not self.connect():
                return {"error": "Failed to connect to RabbitMQ"}
        
        if 'task_id' not in task_data:
            task_data['task_id'] = str(uuid.uuid4())
        
        task_id = task_data['task_id']
        
        try:
            if wait_for_response:
                self.corr_id = str(uuid.uuid4())
                self.responses[self.corr_id] = None
                
                properties = pika.BasicProperties(
                    delivery_mode=2, 
                    correlation_id=self.corr_id,
                    reply_to=self.callback_queue
                )
            else:
                properties = pika.BasicProperties(
                    delivery_mode=2
                )
            
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(task_data),
                properties=properties
            )
            
            logger.info(f"Sent task {task_id} to queue")
            
            if wait_for_response:
                start_time = 0
                while self.responses[self.corr_id] is None:
                    self.connection.process_data_events(time_limit=1)
                    start_time += 1
                    if start_time >= timeout:
                        logger.warning(f"Timeout waiting for response to task {task_id}")
                        del self.responses[self.corr_id]
                        return {"error": "Timeout waiting for response", "task_id": task_id}
                
                response = self.responses[self.corr_id]
                del self.responses[self.corr_id]
                return response
            
            return {"status": "sent", "task_id": task_id}
            
        except Exception as e:
            logger.error(f"Error sending task {task_id}: {e}")
            return {"error": str(e), "task_id": task_id}
    
    def send_text_generation_task(self, text: str, max_length: int = 100, temperature: float = 0.7, 
                                  wait_for_response: bool = True) -> Dict[str, Any]:
        task_data = {
            "task_type": "text_generation",
            "text": text,
            "max_length": max_length,
            "temperature": temperature
        }
        
        return self.send_task(task_data, wait_for_response)
    
    def send_spam_detection_task(self, text: str, detailed: bool = False,
                                wait_for_response: bool = True) -> Dict[str, Any]:
        task_data = {
            "task_type": "spam_detection",
            "text": text,
            "detailed": detailed
        }
        
        return self.send_task(task_data, wait_for_response)
    
    def send_image_caption_task(self, image_data: str, wait_for_response: bool = True) -> Dict[str, Any]:
        task_data = {
            "task_type": "image_caption",
            "image_data": image_data
        }
        
        return self.send_task(task_data, wait_for_response)
    
    def send_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        
        for task_data in tasks:
            result = self.send_task(task_data, wait_for_response=False)
            results.append(result)
        
        return results
    
    def close(self):
        if self.connection:
            try:
                self.connection.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}") 