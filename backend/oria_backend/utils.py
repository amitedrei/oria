from typing import Any
import numpy as np
import time
import inspect
from functools import wraps


def get_n_closest_embedding_documents(
    documents: list[dict[str, Any]],
    embedding: list[float],
    embedding_field: str,
    filter_category: str,
) -> tuple[str, list[dict[str, Any]]]:
    distance_field = f"{embedding_field}_{filter_category}_distance"
    for document in documents:
        doc_emb = np.array(document[embedding_field])
        emb = np.array(embedding)
        cosine_similarity = np.dot(emb, doc_emb) / (
            np.linalg.norm(emb) * np.linalg.norm(doc_emb)
        )
        document[distance_field] = cosine_similarity
    return distance_field, sorted(
        documents, key=lambda x: x[distance_field], reverse=True
    )


def timed_cache(ttl_seconds: int):
    def decorator(func):
        cache = {}

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = (args, tuple(sorted(kwargs.items())))
                now = time.time()

                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return result

                result = await func(*args, **kwargs)
                cache[key] = (result, now)
                return result

            return async_wrapper

        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = (args, tuple(sorted(kwargs.items())))
                now = time.time()

                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return result

                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result

            return sync_wrapper

    return decorator
