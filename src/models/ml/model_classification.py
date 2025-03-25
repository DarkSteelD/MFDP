from ml.model_abstaract import Hugging_face_model

class Model_for_classification(Hugging_face_model):
    def classificate(self, input: str) -> str:
        pass