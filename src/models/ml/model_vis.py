from ml.model_abstaract import Hugging_face_model
from PIL import Image
class Model_for_classification(Hugging_face_model):
    def generate(self, input_str: str, input_image: Image) -> str:
        pass