"""Consumer group member with manual offset commits.

Run two instances in two terminals with the same group id to see
partition rebalancing:

    python consumer.py orders analytics
    python consumer.py orders analytics
"""
import json
import signal
import sys

from confluent_kafka import Consumer, KafkaException, TopicPartition

BOOTSTRAP = "localhost:9092"


def on_assign(consumer, partitions):
    print(f"ASSIGNED: {[(p.topic, p.partition) for p in partitions]}")


def on_revoke(consumer, partitions):
    print(f"REVOKED: {[(p.topic, p.partition) for p in partitions]}")


def main(topic: str, group: str) -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": group,
            "enable.auto.commit": False,        # commit explicitly after processing
            "auto.offset.reset": "earliest",    # first run reads from start
            "partition.assignment.strategy": "cooperative-sticky",
            "isolation.level": "read_committed",
        }
    )
    consumer.subscribe([topic], on_assign=on_assign, on_revoke=on_revoke)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        while running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            payload = json.loads(msg.value())
            print(
                f"[p={msg.partition()} o={msg.offset()}] "
                f"key={msg.key().decode()} value={payload}"
            )

            # Commit only after the message has been processed successfully.
            consumer.commit(
                offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)],
                asynchronous=False,
            )
    finally:
        consumer.close()


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "orders"
    group = sys.argv[2] if len(sys.argv) > 2 else "analytics"
    main(topic, group)
