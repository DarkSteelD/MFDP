from ml.model_abstaract import HuggingFaceModel
from PIL import Image

class ModelForVisTransformer(HuggingFaceModel):
    def generate(self, input_str: str, input_image: Image) -> str:
        pass