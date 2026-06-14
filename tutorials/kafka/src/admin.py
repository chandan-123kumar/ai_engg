"""Topic admin helpers used by the tutorial labs."""
import sys

from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource

BOOTSTRAP = "localhost:9092"


def create(topic: str, partitions: int = 3, rf: int = 1, compact: bool = False) -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP})
    config = {"cleanup.policy": "compact"} if compact else {}
    new_topic = NewTopic(topic, num_partitions=partitions, replication_factor=rf, config=config)
    futures = admin.create_topics([new_topic])
    for t, f in futures.items():
        try:
            f.result()
            print(f"created {t} partitions={partitions} compact={compact}")
        except Exception as e:
            print(f"create {t} failed: {e}")


def describe(topic: str) -> None:
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP})
    md = admin.list_topics(topic, timeout=10)
    t = md.topics[topic]
    if t.error:
        print(f"error: {t.error}")
        return
    for p in t.partitions.values():
        print(
            f"partition={p.id} leader={p.leader} "
            f"replicas={p.replicas} isr={p.isrs}"
        )


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "create":
        # python admin.py create <topic> <partitions> [compact]
        create(
            sys.argv[2],
            int(sys.argv[3]),
            compact=(len(sys.argv) > 4 and sys.argv[4] == "compact"),
        )
    elif cmd == "describe":
        describe(sys.argv[2])
    else:
        print("usage: admin.py {create|describe} <topic> ...")
