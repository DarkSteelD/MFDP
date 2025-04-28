from ml.model_abstaract import HuggingFaceModel
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer

class ModelForGeneration(HuggingFaceModel):
    def __init__(self):
        self._model = None
        self._tokenizer = None
        
    def load_model(self, repo_id: str, model_name: str):
        """
        Load a language model and tokenizer from HuggingFace hub.
        
        Args:
            repo_id: The organization name on HuggingFace
            model_name: The model name
        """
        self._model = AutoModelForCausalLM.from_pretrained(f"{repo_id}/{model_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(f"{repo_id}/{model_name}")
        
    def generate(self, input: str, max_length: int = 100, temperature: float = 0.7) -> str:
        """
        Generate text based on the input prompt.
        
        Args:
            input: The input prompt text
            max_length: Maximum length of generated sequence
            temperature: Sampling temperature (higher = more random)
            
        Returns:
            Generated text response
        """
        if not self._model or not self._tokenizer:
            raise ValueError("Model not loaded. Call load_model first.")
            
        inputs = self._tokenizer(input, return_tensors="pt")
        generation_output = self._model.generate(
            **inputs,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            pad_token_id=self._tokenizer.eos_token_id
        )
        
        return self._tokenizer.decode(generation_output[0], skip_special_tokens=True)
        
    @classmethod
    def create_llama_model(cls, size: str = "7b") -> "ModelForGeneration":
        """
        Factory method to create a pre-configured Llama model.
        
        Args:
            size: Size variant of the model ("7b", "13b", etc)
            
        Returns:
            Configured ModelForGeneration instance
        """
        model = cls()
        model.load_model("meta-llama", f"Llama-2-{size}-hf")
        return model