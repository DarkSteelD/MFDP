from ml.model_abstaract import HuggingFaceModel
from PIL import Image
from typing import List, Dict, Union, Optional
import torch

class ModelForVisTransformer(HuggingFaceModel):
    def __init__(self):
        self._model = None
        self._processor = None
        self._tokenizer = None
        
    def load_model(self, repo_id: str, model_name: str):
        from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
        
        self._model = VisionEncoderDecoderModel.from_pretrained(f"{repo_id}/{model_name}")
        self._processor = ViTImageProcessor.from_pretrained(f"{repo_id}/{model_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(f"{repo_id}/{model_name}")
        
    def generate(self, input_str: str = "", input_image: Image = None) -> str:
        if not self._model or not self._processor:
            raise ValueError("Model not loaded. Call load_model first.")
            
        if input_image is None:
            raise ValueError("An image must be provided")
            
        pixel_values = self._processor(input_image, return_tensors="pt").pixel_values
        
        with torch.no_grad():
            output_ids = self._model.generate(
                pixel_values,
                max_length=50,
                num_beams=4,
                early_stopping=True
            )
        
        preds = self._tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return preds
    
    def classify_image(self, input_image: Image) -> Dict[str, float]:
        if not self._model or not self._processor:
            raise ValueError("Model not loaded. Call load_model first.")
            
        pixel_values = self._processor(input_image, return_tensors="pt").pixel_values
        
        with torch.no_grad():
            outputs = self._model(pixel_values)
        
        if hasattr(outputs, "logits"):
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)[0]
            
            result = {}
            for i, p in enumerate(probs.tolist()):
                label = self._model.config.id2label[i] if hasattr(self._model.config, "id2label") else str(i)
                result[label] = p
                
            return result
        else:
            # If we can't do classification, return info about the model type
            return {"error": "This model doesn't support direct classification"}
    
    @classmethod
    def create_vit_image_captioner(cls) -> "ModelForVisTransformer":
        model = cls()
        model.load_model("nlpconnect", "vit-gpt2-image-captioning")
        return model