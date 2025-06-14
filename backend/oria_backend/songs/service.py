from typing import List

from oria_backend.data_transformers.models import UploadPost
from oria_backend.data_transformers.route import get_song_for_post_data
from oria_backend.songs.models import SongResponseModel
from oria_backend.songs.mongo import mongodb
from sklearn.neighbors import NearestNeighbors
from bson import ObjectId
from enum import Enum
import numpy as np

class data_options(Enum):
  CHORUS_DATA = 1
  MOOD_DATA = 2
  CHOURS_NAME_DATA = 3 # name + chours
  NAME_DATA = 4


KNN_CHORUS_DATA = None
KNN_MOOD_DATA = None
KNN_NAME_DATA = None
KNN_LABLES = None
KNN_MODEL = None
KNN_DATA = None
DATA_DICT = None

async def get_all_songs(count):
    labels = await mongodb.list_all_songs(count)
    songs = []
    for label in labels:
        songs.append(SongResponseModel(id=str(label['_id']),
                            name=label['name'],
                            artists=label['artists'],
                            url=label['url'],
                            source=label['source'],
                            thumbnail=label['thumbnail'],
                            percentage=0))
        
    return songs


async def init_knn():
  global KNN_MOOD_DATA, KNN_CHORUS_DATA, KNN_NAME_DATA, KNN_DATA, KNN_LABLES, KNN_MODEL, DATA_DICT
  KNN_MOOD_DATA, KNN_CHORUS_DATA, KNN_NAME_DATA,  KNN_LABLES = await mongodb.get_all_songs()

  if not mongodb.is_changed():
      return

  KNN_CHOURS_NAME_DATA = np.concatenate((KNN_CHORUS_DATA, KNN_NAME_DATA), axis=1)
 
  DATA_DICT = {
    data_options.CHORUS_DATA : KNN_CHORUS_DATA,
    data_options.MOOD_DATA : KNN_MOOD_DATA,
    data_options.CHOURS_NAME_DATA : KNN_CHOURS_NAME_DATA,
    data_options.NAME_DATA : KNN_NAME_DATA
  }

  KNN_MODEL = NearestNeighbors(n_neighbors=20, metric='euclidean')
  KNN_MODEL.fit(KNN_NAME_DATA)

def cosine_similarity_for_precentage(vec1, vec2):
    """
      get precentage of vector similiarity
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
   
    if norm1 == 0 or norm2 == 0:
        raise ValueError("One or both vectors have zero magnitude.")
   
    vec1_normalized = vec1 / norm1
    vec2_normalized = vec2 / norm2

    cosine_sim = np.dot(vec1_normalized, vec2_normalized)

    similarity_percentage = ((cosine_sim + 1) / 2) * 100
    return similarity_percentage

def top_k_cosine_similar(query_vector: np.ndarray, matrix: np.ndarray, top_k: int = 5):
    """
    Finds the top_k most similar vectors to query_vector in the matrix using cosine similarity.

    Parameters:
    - query_vector: A 1D numpy array of shape (D,)
    - matrix: A 2D numpy array of shape (N, D)
    - top_k: Number of most similar vectors to return

    Returns:
    - indices: Indices of the top_k most similar vectors in the matrix
    - similarities: Corresponding cosine similarity scores
    """
    # Normalize query_vector and matrix
    query_norm = query_vector / np.linalg.norm(query_vector)
    matrix_norm = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

    # Compute cosine similarities
    similarities = matrix_norm @ query_norm

    # Get top_k indices
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    top_similarities = similarities[top_indices]

    return top_indices, top_similarities

def top_k_euclidean_distance(query_vector: np.ndarray, matrix: np.ndarray, top_k: int = 5):
    """
    Finds the top_k most similar vectors to query_vector in the matrix using Euclidean distance.

    Parameters:
    - query_vector: A 1D numpy array of shape (D,)
    - matrix: A 2D numpy array of shape (N, D)
    - top_k: Number of closest vectors to return

    Returns:
    - indices: Indices of the top_k closest vectors in the matrix
    - distances: Corresponding Euclidean distance scores (lower = more similar)
    """
    # Compute Euclidean distances to all rows in the matrix
    diff = matrix - query_vector
    distances = np.linalg.norm(diff, axis=1)

    # Get top_k indices (smallest distances)
    top_indices = np.argsort(distances)[:top_k]
    top_distances = distances[top_indices]

    return top_indices, top_distances

async def repetitive_cosine_similarity(input_list, data_list, prediction_amount_list, indices, top_k_function):
    """
    input_list -> list of input vectors for the knn procedure
    data_list -> list of data to search in(it contains keys for KNN_DICT)
    prediction_amount_list -> list of prediction amount for each input vector
    indices -> list of indices to start from
    top_k_function -> knn function to use (top_k_cosine_similar / top_k_euclidean_distance)
    """
    current_indices = indices
    for i in range(len(input_list)):
        input = input_list[i]
        data = DATA_DICT[data_list[i]]
        predict_amount = prediction_amount_list[i]
        indices, similarities = top_k_function[i](input, data[current_indices], predict_amount)
        current_indices = current_indices[indices]
    return current_indices, similarities

async def get_song_for_post(data: UploadPost):
    await init_knn()
    global KNN_MODEL, KNN_LABLES, KNN_DATA, KNN_MOOD_DATA, KNN_CHORUS_DATA
    
    res = await get_song_for_post_data(data)
    description_embedding, emotions_embedding = res
    double_description_embedding = np.concatenate((description_embedding, description_embedding))
    distances, indices = KNN_MODEL.kneighbors([description_embedding])
    k_labels = [KNN_LABLES[i] for i in indices[0]]

    indecies, similarities = await repetitive_cosine_similarity(
    input_list = [
        description_embedding,
        emotions_embedding,
        double_description_embedding
    ],
    data_list = [
        data_options.CHORUS_DATA,
        data_options.MOOD_DATA,
        data_options.CHOURS_NAME_DATA
        ],
    prediction_amount_list = [
        15,
        10,
        5
    ],
    top_k_function = [
        top_k_cosine_similar,
        top_k_cosine_similar,
        top_k_euclidean_distance
    ],
    indices = indices[0]
    )

    k_labels = []
    for i in range(5):
        percentage = cosine_similarity_for_precentage(
                np.concatenate((
                    KNN_CHORUS_DATA[indecies[i]],
                    KNN_NAME_DATA[indecies[i]],
                    KNN_MOOD_DATA[indecies[i]]
                )),
                np.concatenate((
                    description_embedding,
                    description_embedding,
                    emotions_embedding
                    ))

            )
        
        id, name, artists, source, url, thumbnail = KNN_LABLES[indecies[i]]

        k_labels.append(SongResponseModel(id=str(id),
                        name=name,
                        artists=artists,
                        url=url,
                        source=source,
                        thumbnail=thumbnail,
                        percentage=percentage))

    return k_labels