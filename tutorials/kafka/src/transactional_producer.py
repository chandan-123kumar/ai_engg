"""Exactly-once: read from input topic, transform, write to output topic
atomically with consumer offset commit inside the same transaction.

This is the canonical "read-process-write" EOS pattern.

Run:
    python transactional_producer.py orders orders_enriched eos-app
"""
import json
import sys

from confluent_kafka import Consumer, Producer, TopicPartition

BOOTSTRAP = "localhost:9092"


def main(in_topic: str, out_topic: str, group: str) -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "group.id": group,
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
            "isolation.level": "read_committed",
        }
    )
    consumer.subscribe([in_topic])

    producer = Producer(
        {
            "bootstrap.servers": BOOTSTRAP,
            "enable.idempotence": True,
            "acks": "all",
            "transactional.id": f"tx-{group}",  # stable id → fencing across restarts
        }
    )
    producer.init_transactions(30)

    try:
        while True:
            msgs = consumer.consume(num_messages=100, timeout=1.0)
            if not msgs:
                continue

            producer.begin_transaction()
            offsets = {}

            for msg in msgs:
                if msg.error():
                    continue
                event = json.loads(msg.value())
                event["enriched"] = True
                event["total"] = event["amount"] * 1.1

                producer.produce(
                    out_topic,
                    key=msg.key(),
                    value=json.dumps(event).encode(),
                )

                tp = (msg.topic(), msg.partition())
                offsets[tp] = max(offsets.get(tp, -1), msg.offset())

            # Atomically commit consumer offsets with produced output.
            tps = [TopicPartition(t, p, o + 1) for (t, p), o in offsets.items()]
            producer.send_offsets_to_transaction(tps, consumer.consumer_group_metadata(), 30)
            producer.commit_transaction(30)
            print(f"committed {len(msgs)} messages")
    except KeyboardInterrupt:
        producer.abort_transaction(30)
    finally:
        consumer.close()


if __name__ == "__main__":
    in_topic = sys.argv[1] if len(sys.argv) > 1 else "orders"
    out_topic = sys.argv[2] if len(sys.argv) > 2 else "orders_enriched"
    group = sys.argv[3] if len(sys.argv) > 3 else "eos-app"
    main(in_topic, out_topic, group)
