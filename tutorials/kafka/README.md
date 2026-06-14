# Apache Kafka — Advanced Tutorial with Live Demo (Python)

A hands-on tutorial that walks from Kafka's storage model all the way to exactly-once read-process-write pipelines. Every concept is paired with a command or a Python script you can run against a local Docker cluster.

**Stack:** Kafka 3.6 (Confluent 7.6) + Zookeeper, Docker Compose, Python 3.10+, `confluent-kafka` client.
**Audience:** developers who already understand queues, REST, and basic distributed systems.

---

## Table of contents

1. [Why Kafka exists](#1-why-kafka-exists)
2. [The mental model: log, partition, offset](#2-the-mental-model-log-partition-offset)
3. [Cluster anatomy: brokers, controller, ISR](#3-cluster-anatomy-brokers-controller-isr)
4. [Producers: keys, batching, durability](#4-producers-keys-batching-durability)
5. [Consumers and consumer groups](#5-consumers-and-consumer-groups)
6. [Delivery semantics: at-most / at-least / exactly-once](#6-delivery-semantics)
7. [Log compaction & retention](#7-log-compaction--retention)
8. [Kafka Streams & ksqlDB (concepts)](#8-kafka-streams--ksqldb-concepts)
9. [Operational concerns: lag, rebalances, back-pressure](#9-operational-concerns)
10. [Live lab walkthrough](#10-live-lab-walkthrough)
11. [Troubleshooting cheatsheet](#11-troubleshooting-cheatsheet)
12. [Further reading](#12-further-reading)

---

## 1. Why Kafka exists

Traditional message queues (RabbitMQ, ActiveMQ) treat messages as ephemeral — once a consumer acks, the broker deletes the message. That model breaks down when:

- **Multiple independent consumers** need the same data (analytics, search, audit).
- **Replaying history** is needed for backfills, debugging, or a new consumer.
- **Throughput** must scale horizontally beyond what a single broker can fan out.

Kafka reframes the problem: a topic is an **append-only, partitioned, replicated commit log**. Producers append; consumers read at their own pace and remember their position. The broker doesn't track per-consumer delivery — consumers do. That single design choice is what makes Kafka horizontally scalable and replay-friendly.

> **Rule of thumb:** if you need a durable, replayable event stream that multiple systems consume independently, Kafka. If you need work-queue semantics with per-message ack/nack and priority, a traditional broker is usually simpler.

---

## 2. The mental model: log, partition, offset

A **topic** is split into one or more **partitions**. Each partition is an ordered, immutable sequence of records identified by a monotonically increasing **offset**.

```
topic "orders" (3 partitions)

partition 0:  [o0][o1][o2][o3][o4] ...        → log on disk
partition 1:  [o0][o1][o2][o3] ...
partition 2:  [o0][o1][o2][o3][o4][o5] ...
                                    ^ log-end offset (LEO)
```

Key facts:

- **Ordering is per-partition**, never global. If you need ordering by some entity (e.g. user, order_id), set the message **key** — Kafka hashes the key to pick a partition, so all events for that key land in the same partition in order.
- **Offset is per-partition.** Offset 42 in partition 0 has nothing to do with offset 42 in partition 1.
- **Records are immutable** once written. "Updates" are new records; "deletes" are tombstones (see compaction).

### Why partitions

Partitions are Kafka's unit of parallelism, replication, and ordering:

| Dimension | Effect |
|---|---|
| Throughput | More partitions → more producers/consumers can work in parallel |
| Ordering | Strict order only within a partition, so design keys carefully |
| Consumer parallelism | A consumer group can have at most `N` active consumers if the topic has `N` partitions |
| Rebalance cost | More partitions = longer rebalances and more metadata to replicate |

Practical guidance: start with `partitions = max(expected peak throughput / per-partition throughput, target consumer parallelism)`. A common starting point is 6–12 for medium-traffic topics; you can always increase later (but never decrease without recreating the topic, and increasing breaks key-based ordering for in-flight keys).

---

## 3. Cluster anatomy: brokers, controller, ISR

A Kafka **cluster** is a set of **brokers** (servers). Each partition is stored on one broker (the **leader**) and replicated to `replication.factor - 1` **follower** brokers.

- **Leader** handles all reads and writes for the partition.
- **Followers** continuously fetch from the leader.
- **ISR (in-sync replicas)** = the set of replicas that are caught up with the leader within `replica.lag.time.max.ms`.

Producer durability is controlled by `acks`:

| acks | Meaning | Risk |
|---|---|---|
| `0` | Fire and forget | Data loss on broker failure |
| `1` | Leader wrote it | Data loss if leader crashes before followers replicate |
| `all` (`-1`) | All in-sync replicas wrote it | Slowest, strongest durability |

Combine `acks=all` with `min.insync.replicas=2` on a topic with `replication.factor=3` to tolerate one broker failure without data loss and without producer downtime.

**Controller** is one elected broker that handles cluster-wide metadata (leader election, partition reassignment). In Zookeeper mode (this tutorial), it's stored in ZK. In KRaft mode, the controllers form their own quorum and Zookeeper is gone.

---

## 4. Producers: keys, batching, durability

A producer batches records destined for the same partition and flushes in the background. The important knobs:

| Setting | Default | What it does |
|---|---|---|
| `acks` | `all` (3.x) | Durability (see above) |
| `enable.idempotence` | `true` (3.x) | Dedupes retries with a producer ID + sequence number |
| `linger.ms` | `0` | Wait this long to fill a batch — increasing trades latency for throughput |
| `batch.size` | 16 KB | Max batch size per partition |
| `compression.type` | `none` | `zstd` or `lz4` typically wins on CPU vs. ratio |
| `max.in.flight.requests.per.connection` | 5 | With idempotence, up to 5 is safe and preserves order |
| `retries` | `Integer.MAX` | Retry on retriable errors |
| `delivery.timeout.ms` | 120000 | Hard upper bound on a record's send including retries |

### Keys and partitioning

```python
producer.produce(topic="orders", key=b"user-42", value=b"...")
```

- Key present → hash partitioner (`murmur2` by default) picks a partition deterministically. Same key → same partition → in-order delivery for that key.
- Key absent → "sticky" partitioner picks one partition per batch to maximize batching, then rotates. Records have no ordering guarantee across the topic.

Custom partitioners are supported but rarely needed; designing the right key is almost always the right answer.

See [`src/producer.py`](src/producer.py) for a working idempotent producer with delivery callbacks.

---

## 5. Consumers and consumer groups

A **consumer group** is a set of consumer processes sharing a `group.id`. The group coordinator (a broker) assigns each partition to exactly one consumer in the group. Two facts follow:

1. Within a group, messages are **load-balanced** across consumers.
2. Across groups, each group reads the **full topic independently** — that's how you get fan-out.

```
topic orders (3 partitions)  →  group "analytics" (2 consumers)
   p0 ──────────────► consumer-A
   p1 ──────────────► consumer-A
   p2 ──────────────► consumer-B

If you add consumer-C: rebalance → A:p0, B:p1, C:p2
If you add consumer-D: it sits idle — only 3 partitions exist.
```

### Assignment strategies

- **range** (legacy): groups partitions by topic; can be unbalanced.
- **round-robin**: even distribution but reshuffles everything on rebalance.
- **sticky / cooperative-sticky** (recommended): minimizes movement during rebalance. Cooperative variant does *incremental* rebalances — partitions you keep aren't paused.

Use `partition.assignment.strategy=cooperative-sticky` for any new deployment.

### Offsets and commits

Each consumer periodically commits the offset of the **next** record it will read for each partition. Commits land in the internal `__consumer_offsets` topic.

- `enable.auto.commit=true` (default): commits every `auto.commit.interval.ms`. Easy but can lose or replay messages on crash because commit timing is decoupled from processing.
- `enable.auto.commit=false` + explicit `consumer.commit()` **after** processing: gives at-least-once semantics with no surprises. This is what the demo uses.

See [`src/consumer.py`](src/consumer.py).

### Rebalances

Triggered by: a consumer joining/leaving, a heartbeat timeout, or a subscription change. During a stop-the-world rebalance (non-cooperative), all consumers pause. With cooperative-sticky, only the affected partitions pause.

Tune:
- `session.timeout.ms` — how long the coordinator waits for a heartbeat before evicting (default 45s).
- `max.poll.interval.ms` — how long `poll()` can be absent before the consumer is considered dead (default 5 min). If your processing per batch can exceed this, **either reduce `max.poll.records` or process asynchronously**.

---

## 6. Delivery semantics

| Semantics | How to get it | Trade-off |
|---|---|---|
| **At-most-once** | Commit offset *before* processing | Lose messages on crash |
| **At-least-once** | Commit offset *after* processing (default sane setup) | Duplicates on retry/crash |
| **Exactly-once** | Idempotent producer + transactions + `isolation.level=read_committed` consumers | Throughput cost, only end-to-end within Kafka |

### Idempotent producer

`enable.idempotence=true` assigns each producer a PID and each message a per-partition sequence number. The broker deduplicates retries. This eliminates duplicates **from producer retries** but doesn't help if your application code calls `produce()` twice.

### Transactions and exactly-once-semantics (EOS)

Use a **transactional producer** when you do "read from topic A, transform, write to topic B (and maybe a state store), commit consumer offset" — the canonical stream processing pattern. Either *all* of the writes and the offset commit happen, or *none* do.

```python
producer = Producer({"transactional.id": "tx-eos-app", "enable.idempotence": True, ...})
producer.init_transactions()
producer.begin_transaction()
producer.produce(out_topic, ...)
producer.send_offsets_to_transaction(offsets, consumer.consumer_group_metadata())
producer.commit_transaction()
```

The `transactional.id` is **stable across restarts** so the broker can fence out the previous (zombie) instance. Consumers must set `isolation.level=read_committed` to skip aborted records.

**Important caveat:** "exactly-once" applies to Kafka-to-Kafka pipelines. If you write to an external database or call an external API, you need idempotent writes downstream (e.g. upsert with a unique key) — Kafka can't roll back an HTTP POST.

See [`src/transactional_producer.py`](src/transactional_producer.py) for a working read-process-write EOS pipeline.

---

## 7. Log compaction & retention

A topic's `cleanup.policy` decides what happens to old data:

- **`delete`** (default): records older than `retention.ms` (default 7 days) or beyond `retention.bytes` are removed.
- **`compact`**: Kafka keeps **at least the latest record per key** forever. Older records for the same key are eventually garbage-collected by a background thread.
- **`compact,delete`**: compaction *and* a retention bound.

Compaction is how Kafka stores changelog topics: a topic whose state at any moment is "the latest value per key" — exactly what a key-value store materializes. Send `key=user-42, value=null` (a **tombstone**) and that key is eventually fully removed.

This is what powers Kafka Streams state stores, KTables, the `__consumer_offsets` topic itself, and the `__transaction_state` topic.

---

## 8. Kafka Streams & ksqlDB (concepts)

The Java **Kafka Streams** library treats a topic as a stream (every record matters) or a table (latest-per-key matters), and gives you stateful operators (joins, aggregations, windows). State stores are RocksDB instances on each app instance, backed by a compacted changelog topic — so on restart, state is rebuilt from Kafka, not from a separate database.

Python doesn't have a first-class Streams library; common alternatives:

- **[Faust](https://faust-streaming.github.io/faust/)** — Python clone of Kafka Streams (community-maintained).
- **ksqlDB** — SQL on top of Kafka, runs as a separate cluster. Define streams and tables with `CREATE STREAM ... AS SELECT ...`.
- **Apache Flink** — heavier, but the most production-grade stream processor today.

For this tutorial, the EOS pattern in [`src/transactional_producer.py`](src/transactional_producer.py) is the building block — Streams is conceptually "many of those, with state stores layered in."

---

## 9. Operational concerns

### Consumer lag

`lag = log_end_offset - committed_offset` per partition. Monitor it; sustained growth means the consumer can't keep up. Inspect with:

```bash
docker exec -it tut-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 --describe --group analytics
```

### Back-pressure

Kafka has no built-in back-pressure to the producer — if consumers fall behind, lag grows until retention deletes data. Mitigations:

1. Add partitions and scale consumers horizontally.
2. Make per-message processing faster or batch downstream writes.
3. Apply a hard ceiling: retention bounds + alerts on lag breaches.

### Rebalance storms

Symptoms: consumer logs full of "Revoking partitions / Assigning partitions" with no progress. Causes are usually `max.poll.interval.ms` exceeded, GC pauses, or flaky network. Fixes: smaller `max.poll.records`, async processing pattern (poll thread separate from work thread), cooperative-sticky assignor.

### Common configuration mistakes

- `replication.factor=1` in production. One disk failure = data loss.
- `min.insync.replicas` not set → `acks=all` doesn't actually protect you.
- Topic created with default 1 partition, then needing parallelism later.
- Auto-creating topics with broker defaults that don't match the use case.

---

## 10. Live lab walkthrough

### Prereqs

- Docker Desktop / Docker Engine with Compose v2
- Python 3.10+

### Step 0 — start the cluster

```bash
cd tutorials/kafka/demo
docker compose up -d
docker compose ps              # zookeeper, kafka, kafka-ui should be "Up"
open http://localhost:8080     # Kafka UI
```

### Step 1 — install the Python client

```bash
cd tutorials/kafka/src
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2 — create a topic with 3 partitions

```bash
python admin.py create orders 3
python admin.py describe orders
# expected: 3 partitions, leader=1, replicas=[1], isr=[1]
```

You can also use the CLI inside the container:

```bash
docker exec -it tut-kafka kafka-topics \
  --bootstrap-server localhost:9092 --create --topic orders \
  --partitions 3 --replication-factor 1   # will fail since we already created it
```

### Step 3 — produce events

```bash
python producer.py orders 50
```

You'll see delivery reports listing partition and offset. Notice how messages with the same key always land on the same partition.

### Step 4 — single consumer

```bash
python consumer.py orders analytics
```

It reads all partitions. Stop it with Ctrl-C.

### Step 5 — observe consumer-group rebalancing

Open **two terminals**, run the consumer in each with the same group `analytics`:

```bash
python consumer.py orders analytics      # terminal 1
python consumer.py orders analytics      # terminal 2
```

Watch the `ASSIGNED:` / `REVOKED:` log lines — partitions move between the two consumers. Run a third instance; the partitions split 1/1/1. Run a fourth; it sits idle (only 3 partitions exist).

Now produce more from another terminal:

```bash
python producer.py orders 100
```

Both consumers process in parallel.

### Step 6 — inspect lag

```bash
docker exec -it tut-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 --describe --group analytics
```

You'll see `CURRENT-OFFSET`, `LOG-END-OFFSET`, `LAG` per partition.

### Step 7 — exactly-once pipeline

Create the output topic, then run the transactional reader-writer:

```bash
python admin.py create orders_enriched 3
python transactional_producer.py orders orders_enriched eos-app
```

In another terminal, consume the enriched topic with `read_committed`:

```bash
python consumer.py orders_enriched eos-viewer
```

You'll see each input order appear once in `orders_enriched` with `enriched=true` and `total = amount * 1.1`. Kill the transactional process mid-stream with `kill -9` — restart it — there are still no duplicates downstream because aborted transactions are skipped by `read_committed` consumers.

### Step 8 — log compaction

```bash
python admin.py create user_profiles 1 compact
```

Produce three records with the same key and different values:

```python
# python REPL
from confluent_kafka import Producer
p = Producer({"bootstrap.servers": "localhost:9092"})
for v in [b"v1", b"v2", b"v3"]:
    p.produce("user_profiles", key=b"user-1", value=v)
p.flush()
```

Trigger compaction (or wait — defaults are slow). Read from the beginning; eventually only `v3` survives. Send `key=b"user-1", value=None` and after compaction the key is fully gone.

### Step 9 — failure drill (optional)

Stop Kafka while a producer is mid-flight:

```bash
docker compose stop kafka
python producer.py orders 50    # producer will retry
docker compose start kafka
```

The idempotent producer recovers, no duplicates appear.

### Step 10 — tear down

```bash
docker compose down -v   # -v also removes volumes (wipes data)
```

---

## 11. Troubleshooting cheatsheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `BROKER_NOT_AVAILABLE` from host | `advertised.listeners` wrong | Confirm host listener resolves to `localhost:9092` |
| Producer hangs, no delivery report | `acks=all` but `min.insync.replicas` not met | Lower MISR or add brokers; check `kafka-topics --describe` |
| Consumer stuck at the start, no progress | `auto.offset.reset=latest` and no new traffic | Use `earliest` for backfill, or produce new messages |
| Consumer reads same messages forever | Not committing offsets | Set `enable.auto.commit=true` *or* explicit commit after processing |
| Frequent rebalances | `max.poll.interval.ms` exceeded | Reduce `max.poll.records`, speed up processing |
| Duplicates downstream despite EOS | External sink (DB, HTTP) isn't idempotent | Make sink idempotent (upsert by key) |
| `OFFSET_OUT_OF_RANGE` | Consumer offset older than retention | Reset group: `kafka-consumer-groups --reset-offsets --to-earliest --execute` |
| Throughput is low | Tiny batches | Increase `linger.ms`, enable compression |

---

## 12. Further reading

- Kafka docs — [https://kafka.apache.org/documentation/](https://kafka.apache.org/documentation/)
- Confluent platform docs — [https://docs.confluent.io/platform/current/overview.html](https://docs.confluent.io/platform/current/overview.html)
- *Designing Data-Intensive Applications*, Kleppmann, chapter 11
- *Kafka: The Definitive Guide*, 2nd ed., Narkhede et al.
- KIP-98 (idempotent + transactional producer): [https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging)

---

## Repository layout

```
tutorials/kafka/
├── README.md                        # this file
├── demo/
│   └── docker-compose.yml           # Kafka + Zookeeper + Kafka UI
└── src/
    ├── requirements.txt
    ├── admin.py                     # create/describe topics
    ├── producer.py                  # idempotent producer with keys
    ├── consumer.py                  # consumer-group member with manual commits
    └── transactional_producer.py    # exactly-once read-process-write
```
