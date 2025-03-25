from abc import ABC, abstractmethod

class hugging_face_model(ABC):
    @abstractmethod
    def load_model(self, repo_id: str, model_name: str):
        pass
    