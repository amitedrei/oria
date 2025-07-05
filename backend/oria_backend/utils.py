import time
import inspect
from functools import wraps
import json
import numpy as np


def timed_cache(ttl_seconds: int):
    def hash_key(*args, **kwargs):
        return (args, json.dumps(kwargs, sort_keys=True))

    def decorator(func):
        cache = {}

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = hash_key(*args, **kwargs)
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
                key = hash_key(*args, **kwargs)
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


def normalize_vector(vector):
    np_vector = np.array(vector)
    return np_vector / np.linalg.norm(np_vector)
