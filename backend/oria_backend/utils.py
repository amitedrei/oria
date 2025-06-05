from typing import Any
import numpy as np


def get_n_closest_embedding_documents(
    documents: list[dict[str, Any]], embedding: list[float], embedding_field: str
) -> tuple[str, list[dict[str, Any]]]:
    distance_field = f"{embedding_field}_distance"
    for document in documents:
        document[distance_field] = np.linalg.norm(
            np.array(embedding) - np.array(document[embedding_field])
        )
    return distance_field, sorted(documents, key=lambda x: x[distance_field])
