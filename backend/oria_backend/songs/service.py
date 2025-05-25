from typing import List

from fastapi import UploadFile
import os

# from oria_backend.data_transformers.models import UploadPost
# from oria_backend.data_transformers.route import get_song_for_post_data
from oria_backend.utils import save_upload_file
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
import librosa
import torch
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SONG_TO_EMOTIONS_MODEL_ID = (
    "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
)
song_to_emotions_model = AutoModelForAudioClassification.from_pretrained(
    SONG_TO_EMOTIONS_MODEL_ID
)

song_to_emotions_model = song_to_emotions_model.to(device)
feature_extractor = AutoFeatureExtractor.from_pretrained(
    SONG_TO_EMOTIONS_MODEL_ID, do_normalize=True
)
ID_TO_EMOTIONS = song_to_emotions_model.config.id2label
EMOTIONS_THRESHOLD = 0.5

async def get_all_songs() -> List[SongResponseModel]:
    songs = await mongodb.get_all_songs()
    return [
        SongResponseModel(
            id=song["_id"],
            name=song["name"],
            artists=song["artists"],
            url=song["url"],
            thumbnail=song["thumbnail"],
            source=song["source"],
            playlists=song["playlists"],
            distance=-1,
        )
        for song in songs
    ]


# async def find_top_songs(data: UploadPost) -> List[SongResponseModel]:
#     song_data = await get_song_for_post_data(data.text, data.image)
#     embedding = song_data.embeddings
#     similar_songs = await mongodb.find_similar_songs(embedding, 5)

#     return [
#         SongResponseModel(
#             id=song["_id"],
#             name=song["name"],
#             artists=song["artists"],
#             url=song["url"],
#             thumbnail=song["thumbnail"],
#             source=song["source"],
#             playlists=song["playlists"],
#             distance=song["distance"],
#         )
#         for song in similar_songs
#     ]


def preprocess_audio(audio_path: str, feature_extractor, max_duration: float):
    audio_array, _ = librosa.load(audio_path, sr=feature_extractor.sampling_rate)

    max_length = int(feature_extractor.sampling_rate * max_duration)
    if len(audio_array) > max_length:
        audio_array = audio_array[:max_length]
    else:
        audio_array = np.pad(audio_array, (0, max_length - len(audio_array)))

    inputs = feature_extractor(
        audio_array,
        sampling_rate=feature_extractor.sampling_rate,
        max_length=max_length,
        truncation=True,
        return_tensors="pt",
    )
    return inputs


def predict_emotion(audio_path, max_duration=30.0) -> dict[str, float]:
    print(f"Processing audio file: {audio_path}")
    inputs = preprocess_audio(audio_path, feature_extractor, max_duration)

    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = song_to_emotions_model(**inputs)
    
    logits = outputs.logits           # shape (1, num_emotions)
    probs = torch.softmax(logits, dim=-1).tolist()[0]
    return {ID_TO_EMOTIONS[i]: float(probs[i]) for i in range(len(probs)) if probs[i] > EMOTIONS_THRESHOLD}
    

async def get_emotions(song: UploadFile) -> dict[str, float]:
    audio_path = None
    try:
        audio_path = save_upload_file(song)
        emotions = predict_emotion(audio_path)
        return emotions
    except Exception as e:
        print(f"Error processing song: {e}")
    finally:
        if audio_path:
            os.remove(audio_path)
    return {}
