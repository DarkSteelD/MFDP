from ml.model_abstaract import HuggingFaceModel

class ModelForClassification(HuggingFaceModel):
    def classificate(self, input: str) -> str:
        pass