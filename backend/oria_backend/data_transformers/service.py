from io import BytesIO
import os

from fastapi import UploadFile
import torch
from PIL import Image
from transformers import (
    AutoModel,
)
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch.nn.functional as F
import torch.nn as nn


HERE = os.path.dirname(os.path.abspath(__file__))
REFINER_PATH = os.path.join(HERE, "data", "refiner.pth")


class EmbedRefiner(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.fc = nn.Linear(dim, dim)

    def forward(self, x):
        h = F.relu(self.fc(x))
        return F.normalize(x + h, p=2, dim=-1)


device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)


HERE = os.path.dirname(os.path.abspath(__file__))
REFINER_PATH = os.path.join(HERE, "data", "refiner.pth")
ckpt = torch.load(REFINER_PATH, map_location="cpu")
state_dict = ckpt.get("model_state_dict", ckpt)

dim = state_dict["fc.weight"].shape[1]

refiner = EmbedRefiner(dim).to(device)
refiner.load_state_dict(state_dict)
refiner.eval()


def get_refined_embeddings(embeddings) -> list[float]:
    x = torch.tensor(embeddings, dtype=torch.float32, device=device)
    if x.dim() == 1:
        x = x.unsqueeze(0)
    x = F.normalize(x, p=2, dim=-1)
    with torch.no_grad():
        out = refiner(x)
    return out[0].cpu().tolist()


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


def extract_data_from_image(image: Image.Image, task: str | None = None) -> str:
    inputs = image_processor(images=image, text=task, return_tensors="pt")
    device = next(image_model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    out = image_model.generate(**inputs)
    return image_processor.decode(out[0], skip_special_tokens=True)


def extract_description_from_image(image: Image.Image) -> str:
    prefixes = [
        "a photography of",
        "the mood of the image is",
    ]
    descriptions = [extract_data_from_image(image, prefix) for prefix in prefixes]
    return ".\n".join(descriptions)
