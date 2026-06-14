"""Basic producer: send keyed JSON events to a topic.

Run:
    python producer.py orders 100
"""
import json
import sys
import time
from confluent_kafka import Producer

BOOTSTRAP = "localhost:9092"


def delivery_report(err, msg):
    if err is not None:
        print(f"DELIVERY FAILED for key={msg.key()}: {err}")
    else:
        print(
            f"delivered key={msg.key().decode()} "
            f"partition={msg.partition()} offset={msg.offset()}"
        )


def main(topic: str, n: int) -> None:
    producer = Producer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "linger.ms": 10,           # batch up to 10ms for throughput
            "compression.type": "zstd",
            "acks": "all",             # wait for all in-sync replicas
            "enable.idempotence": True # no duplicates on retry
        }
    )

    for i in range(n):
        key = f"user-{i % 5}"          # 5 distinct keys → sticky partitioning
        value = {"order_id": i, "user": key, "amount": 10 + i, "ts": time.time()}
        producer.produce(
            topic=topic,
            key=key.encode(),
            value=json.dumps(value).encode(),
            on_delivery=delivery_report,
        )
        producer.poll(0)               # serve delivery callbacks

    producer.flush(15)


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "orders"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    main(topic, count)
