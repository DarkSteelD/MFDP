from ml.model_abstaract import hugging_face_model

class Model_for_classification(hugging_face_model):
    def classificate(self, input: str) -> str:
        pass