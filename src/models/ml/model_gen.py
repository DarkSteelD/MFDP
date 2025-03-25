from ml.model_abstaract import HuggingFaceModel

class ModelForGeneration(HuggingFaceModel):
    def generate(self, input: str) -> str:
        pass