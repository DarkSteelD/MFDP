from abc import ABC, abstractmethod
from transformers import AutoTokenizer, AutoModelForMaskedLM

class Hugging_face_model(ABC):
    @abstractmethod
    def load_model(self, repo_id: str, model_name: str):
        self.__model = AutoModelForMaskedLM.from_pretrained(repo_id + "/" + model_name)
        self.__tokenizer = AutoTokenizer.from_pretrained(repo_id + "/" + model_name)
    