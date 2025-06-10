from io import BytesIO

from fastapi import UploadFile
import torch
from PIL import Image
from transformers import (
    AutoModel,
)
from transformers import BlipProcessor, BlipForConditionalGeneration

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

print(f"Using device: {device}")

embeddings_model = AutoModel.from_pretrained(
    "jinaai/jina-embeddings-v3", trust_remote_code=True
)

image_processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-large"
)
image_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-large"
)
embeddings_model.to(device)
image_model.to(device)


def get_embeddings(text: str) -> list[float]:
    embeddings = embeddings_model.encode([text])
    return embeddings.tolist()[0]


def get_image_from_upload_file(image: UploadFile) -> Image.Image:
    image_bytes = image.file.read()
    pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    return pil_image


def extract_data_from_image(image: Image.Image, task: str) -> str:
    inputs = image_processor(images=image, text=task, return_tensors="pt")
    device = next(image_model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    out = image_model.generate(**inputs)
    return image_processor.decode(out[0], skip_special_tokens=True)


def extract_description_from_image(image: Image.Image) -> str:
    return extract_data_from_image(image, "a photography of")

