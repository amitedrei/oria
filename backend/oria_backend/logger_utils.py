import json
from functools import partial

from loguru import logger


def json_sink(message, serializer):
    serialized = serializer(message.record)
    print(serialized)
    return False


def json_serializer(record):
    log_record = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    if record["exception"]:
        log_record["exception"] = record["exception"].split("\n")

    for key, value in record["extra"].items():
        log_record[key] = value

    return json.dumps(log_record)


def initialize_logger():
    logger.remove()

    logger.add(
        partial(json_sink, serializer=json_serializer),
        format="",
        serialize=False,
    )
