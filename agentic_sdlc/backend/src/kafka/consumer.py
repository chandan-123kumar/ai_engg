import json
import threading
from kafka import KafkaConsumer
from src.config import settings

class BaseConsumer(threading.Thread):
    topic: str

    def __init__(self):
        super().__init__(daemon=True)
        self._consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=f"{self.topic}.consumer",
        )

    def handle(self, message: dict):
        raise NotImplementedError

    def run(self):
        for msg in self._consumer:
            self.handle(msg.value)
