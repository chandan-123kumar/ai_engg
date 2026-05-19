import json
from kafka import KafkaProducer as _KafkaProducer
from src.config import settings

_producer = None

def get_producer() -> _KafkaProducer:
    global _producer
    if _producer is None:
        _producer = _KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
    return _producer

def publish(topic: str, message: dict, key: str = None):
    producer = get_producer()
    producer.send(topic, value=message, key=key)

def flush():
    get_producer().flush()
