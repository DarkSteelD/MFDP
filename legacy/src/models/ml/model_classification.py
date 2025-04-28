from ml.model_abstaract import HuggingFaceModel
from typing import Dict, List, Tuple
import torch
import torch.nn.functional as F

class ModelForClassification(HuggingFaceModel):
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._id2label = None
        self._label2id = None
        
    def load_model(self, repo_id: str, model_name: str):
        """
        Load a classification model and tokenizer from HuggingFace hub.
        
        Args:
            repo_id: The organization name on HuggingFace
            model_name: The model name
        """
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        
        self._model = AutoModelForSequenceClassification.from_pretrained(f"{repo_id}/{model_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(f"{repo_id}/{model_name}")
        
        if hasattr(self._model.config, "id2label"):
            self._id2label = self._model.config.id2label
            self._label2id = self._model.config.label2id
        
    def classificate(self, input: str) -> str:
        """
        Classify the input text.
        
        Args:
            input: The text to classify
            
        Returns:
            The predicted class label
        """
        if not self._model or not self._tokenizer:
            raise ValueError("Model not loaded. Call load_model first.")
            
        inputs = self._tokenizer(input, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self._model(**inputs)
        
        logits = outputs.logits
        predicted_class_id = logits.argmax(-1).item()
        
        if self._id2label:
            return self._id2label[predicted_class_id]
        return str(predicted_class_id)
        
    def classificate_with_scores(self, input: str) -> Dict[str, float]:
        """
        Classify the input text and return class probabilities.
        
        Args:
            input: The text to classify
            
        Returns:
            Dictionary mapping class labels to probabilities
        """
        if not self._model or not self._tokenizer:
            raise ValueError("Model not loaded. Call load_model first.")
            
        inputs = self._tokenizer(input, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self._model(**inputs)
        
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)[0]
        
        result = {}
        for i, p in enumerate(probs.tolist()):
            label = self._id2label[i] if self._id2label else str(i)
            result[label] = p
            
        return result
        
    @classmethod
    def create_spam_detector(cls) -> "ModelForClassification":
        """
        Factory method to create a pre-configured spam detector model.
        
        Returns:
            Configured ModelForClassification instance for spam detection
        """
        model = cls()
        model.load_model("mrm8488", "bert-tiny-finetuned-sms-spam-detection")
        return model