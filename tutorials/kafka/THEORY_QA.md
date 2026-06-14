# Kafka Theory — Brainstorming Q&A

Self-quiz / interview-prep companion to the [main tutorial](README.md). Each section is a question with a collapsible answer — click **▶ Show answer** to reveal. Try to answer in your head first.

> Rendering note: the hide/show works on GitHub, GitLab, and any Markdown viewer that supports `<details>`/`<summary>` (VS Code preview, Obsidian, MkDocs, most static-site generators).

---

## Section 1 — Why Kafka?

### Q1.1 — Why isn't a traditional message queue (RabbitMQ, SQS) enough when many consumers want the same data?

<details>
<summary>▶ Show answer</summary>

Traditional queues are **destructive reads**: once a consumer acks, the message is gone. If three independent systems (analytics, search, audit) all need the same event, you have to fan-out at the producer or maintain three separate queues.

Kafka decouples **storage** from **delivery**. The log persists for `retention.ms` (default 7 days) regardless of who has read it. Each consumer group tracks its own offset, so N independent groups can read the same topic at their own pace, replay history, or join later and start from the beginning.

That single design choice — broker doesn't track per-consumer delivery, consumers track their own position — is what enables fan-out, replay, and horizontal scale.

</details>

### Q1.2 — When should you NOT use Kafka and pick a traditional broker instead?

<details>
<summary>▶ Show answer</summary>

Pick a traditional broker when you need **work-queue semantics**:

- Per-message ack / nack / requeue
- Priority queues
- Delayed / scheduled delivery
- Dead-letter handling at the broker
- Low volume where Kafka's operational overhead isn't worth it

Kafka is a log, not a task queue. You can build retry-with-DLQ on Kafka, but RabbitMQ does it natively.

</details>

---

## Section 2 — The mental model: log, partition, offset

### Q2.1 — What exactly is a partition, and why do we need more than one?

<details>
<summary>▶ Show answer</summary>

A partition is an **ordered, immutable, append-only sequence of records** stored as segment files on a single broker's disk. Each record has a 64-bit offset unique within that partition.

Partitions give Kafka four properties simultaneously:

1. **Parallelism** — different partitions can be written and read concurrently.
2. **Replication unit** — replication is per-partition, not per-topic.
3. **Ordering unit** — order is guaranteed only within a partition.
4. **Consumer fan-out unit** — within a group, each partition is owned by exactly one consumer.

A single-partition topic is a sequential log with no parallelism — fine for small command streams, useless for high throughput.

</details>

### Q2.2 — Is offset 42 in partition 0 related to offset 42 in partition 1?

<details>
<summary>▶ Show answer</summary>

**No.** Offsets are per-partition counters with no cross-partition meaning. Partition 0 offset 42 and partition 1 offset 42 are completely unrelated records that happen to be the 43rd record in their respective partitions.

This is why Kafka has no global "message ID" — the identifier is the tuple `(topic, partition, offset)`.

</details>

### Q2.3 — How does the producer decide which partition a record lands in?

<details>
<summary>▶ Show answer</summary>

Three cases:

1. **Explicit partition** in `produce(partition=N, ...)` — that partition is used.
2. **Key provided, no partition** — `partition = murmur2(key) % num_partitions`. Deterministic: same key → same partition (until you resize the topic).
3. **No key, no partition** — modern clients use the "sticky partitioner": one partition per batch to maximize batching, then rotate.

Custom partitioners are pluggable but rarely the right answer — designing a good key (user_id, order_id, tenant_id) almost always solves the problem.

</details>

### Q2.4 — What breaks if I add partitions to an existing topic?

<details>
<summary>▶ Show answer</summary>

**Key-based ordering breaks for in-flight keys.** Adding partitions changes the `hash(key) % N` denominator, so a given key may now hash to a different partition. Records for that key that existed in the old partition stay there; new records go to the new partition. Strict per-key ordering across the change boundary is lost.

You also **cannot shrink** partitions — Kafka has no remove-partition operation. Plan partition count up front: it's easier to over-provision and consolidate consumers than to grow under load.

</details>

---

## Section 3 — Cluster anatomy

### Q3.1 — What is the ISR and why does it matter?

<details>
<summary>▶ Show answer</summary>

**ISR (In-Sync Replicas)** is the set of replicas — including the leader — that are caught up to the leader within `replica.lag.time.max.ms` (default 30s). A follower that falls behind is kicked out of the ISR; if it catches up, it's added back.

ISR matters because:

- `acks=all` waits for **all in-sync replicas**, not all replicas. A slow follower doesn't block production.
- `min.insync.replicas` is the topic-level floor: if ISR drops below it, `acks=all` producers get `NotEnoughReplicasException`. This prevents silent data-loss windows.
- Leader election picks the new leader from the ISR — so a non-ISR replica becoming leader (via `unclean.leader.election.enable=true`) means accepting data loss.

</details>

### Q3.2 — Which `acks` setting do you pick in production, and what's the catch?

<details>
<summary>▶ Show answer</summary>

`acks=all` plus `min.insync.replicas=2` on a topic with `replication.factor=3`.

Why those numbers:

- `acks=all` guarantees every accepted write is on all in-sync replicas → no data loss when leader crashes.
- `replication.factor=3` lets you tolerate one broker failure.
- `min.insync.replicas=2` means you can lose one replica without producer downtime; if you lose two, producers fail loudly rather than silently writing to a single broker.

The catch: latency. Every write waits for the slowest in-sync follower. Without idempotence + retries configured, you also risk duplicates on retry — so always pair with `enable.idempotence=true` (the 3.x default).

</details>

### Q3.3 — Zookeeper vs. KRaft — what changed and should I care?

<details>
<summary>▶ Show answer</summary>

**Zookeeper mode** (legacy): a separate ZK ensemble stores cluster metadata (broker registry, controller election, ACLs, topic config). One broker is the elected controller and applies metadata changes to ZK.

**KRaft mode** (Kafka Raft, default in 3.5+, ZK removed in 4.0): a dedicated set of controller brokers form a Raft quorum and store metadata in an internal `__cluster_metadata` topic. No more ZK process to run, monitor, or upgrade.

Why care:

- Fewer moving parts to operate (one cluster, not two).
- Faster controller failover and metadata propagation.
- Higher partition counts per cluster (millions feasible).
- New deployments should be KRaft. Existing ZK clusters can migrate online in modern versions.

This tutorial uses ZK because it's the most common production deployment still in the wild, and the producer/consumer code is identical either way.

</details>

---

## Section 4 — Producers

### Q4.1 — What does `enable.idempotence=true` actually do under the hood?

<details>
<summary>▶ Show answer</summary>

The broker assigns each producer a **Producer ID (PID)** on first connection. The producer attaches a per-partition monotonically-increasing **sequence number** to every record batch.

When the broker receives a batch, it checks: is this sequence number exactly one greater than the last one I saw from this PID for this partition?

- If yes → append.
- If equal to the last seen → it's a retry; ack again without re-appending (dedup).
- If less → out of order; reject.
- If greater than +1 → gap; reject (`OutOfOrderSequenceException`).

This eliminates duplicates from network-induced producer retries. It does **not** dedupe application-level double-sends — if your code calls `produce()` twice with the same payload, you get two records with different sequence numbers.

</details>

### Q4.2 — Why use `linger.ms > 0` if it adds latency?

<details>
<summary>▶ Show answer</summary>

`linger.ms` is the producer's wait-and-batch window. With `linger.ms=0` the producer sends as soon as a record is enqueued, often with batches of 1. With `linger.ms=10` it waits up to 10 ms for more records to fill the batch.

Why accept latency:

- **Throughput** — fewer requests, larger batches, better compression ratios, lower per-message broker overhead. Going from `linger=0` to `linger=10` often 5-10x throughput at the cost of a few ms.
- **Network efficiency** — one request with 1000 records is much cheaper than 1000 requests with 1 each.

Rule of thumb: latency-sensitive UIs → keep `linger.ms` low (0–2 ms). Pipeline / analytics / log shipping → set it to 10–50 ms with compression on.

</details>

### Q4.3 — `acks=all` + `enable.idempotence=true` + `max.in.flight.requests.per.connection=5` — is ordering preserved?

<details>
<summary>▶ Show answer</summary>

**Yes.** This is the magic of the idempotent producer.

Before idempotence, having >1 in-flight request per connection could cause reordering: batch B succeeds while batch A is being retried, so A ends up *after* B in the log. The old rule was to set `max.in.flight=1` if you needed strict ordering, which crushed throughput.

With idempotence, the broker uses the sequence number to detect out-of-order batches and reject them, forcing the producer to retry in order. The official safe limit is **5 in-flight requests per connection**, which is plenty for throughput.

So the modern recipe is: idempotence on, `max.in.flight=5`, `acks=all` — high throughput, strict per-partition order, no duplicates from retries.

</details>

---

## Section 5 — Consumers and consumer groups

### Q5.1 — Two consumers in the same group vs. two consumers in different groups — what's the difference?

<details>
<summary>▶ Show answer</summary>

- **Same group** → **load balancing**. The group coordinator divides partitions between them. Each record is processed by exactly one of the two.
- **Different groups** → **fan-out**. Each group reads the full topic independently with its own committed offsets. Each record is processed by both.

You combine these patterns all the time: one "search-indexer" group with 4 consumers (load-balanced), one "audit-logger" group with 1 consumer, one "analytics" group with 8 — all reading the same topic.

</details>

### Q5.2 — Why is the max useful parallelism in a consumer group equal to the number of partitions?

<details>
<summary>▶ Show answer</summary>

A partition is owned by exactly one consumer in the group at any time — that's the only way Kafka can guarantee per-partition ordering inside a group. So:

- If the topic has 6 partitions and the group has 3 consumers → each consumer gets 2 partitions.
- If the group has 6 consumers → each gets 1.
- If the group has 10 consumers → 6 get one partition each, 4 sit idle as hot spares.

This is why partition count is a capacity-planning decision: it caps your maximum horizontal scale per consumer group.

</details>

### Q5.3 — Why prefer `cooperative-sticky` over `range` or `round-robin`?

<details>
<summary>▶ Show answer</summary>

**Range** and **round-robin** are *eager* rebalance protocols: when one consumer joins or leaves, every consumer in the group revokes all its partitions, the coordinator computes a new assignment, and everyone re-joins. Everyone pauses processing during the rebalance — a "stop-the-world" event that can last seconds and cause cascading lag.

**Cooperative-sticky** does *incremental* rebalances:

1. Coordinator identifies only the partitions that need to move.
2. Only the losing consumers revoke their affected partitions.
3. Consumers keep processing partitions they're retaining.
4. New owners pick up the moved partitions.

Result: rebalances become quick, partial, and non-disruptive. You should use cooperative-sticky on every new deployment.

</details>

### Q5.4 — Auto-commit vs. manual commit — when does auto-commit lose data, and when does it duplicate?

<details>
<summary>▶ Show answer</summary>

`enable.auto.commit=true` commits the latest polled offsets every `auto.commit.interval.ms` (default 5s).

- **Loss scenario:** you `poll()` 100 records, the auto-commit timer fires and commits the new offset, then your process crashes before processing record 100. On restart, the consumer skips it. **At-most-once.**
- **Duplicate scenario:** you `poll()`, process records 1–80, crash before the next auto-commit. On restart, you re-poll records 1–80. **At-least-once duplicates.**

Auto-commit gives you whichever you get less wrong — neither guarantee. Manual commit *after* successful processing gives clean at-least-once: you may duplicate on crash, but you never lose.

For exactly-once Kafka-to-Kafka, you need transactional commits (see Section 6).

</details>

### Q5.5 — `session.timeout.ms` vs. `max.poll.interval.ms` — what's the difference?

<details>
<summary>▶ Show answer</summary>

Both detect "dead" consumers, but they measure different things:

- **`session.timeout.ms`** (default 45s) — heartbeat liveness. A background thread sends heartbeats every `heartbeat.interval.ms`. If the coordinator hasn't seen one within `session.timeout.ms`, the consumer is evicted. This catches process crashes and network partitions.
- **`max.poll.interval.ms`** (default 5 min) — *processing* liveness. The user thread must call `poll()` within this interval. If it doesn't (e.g. stuck in a long-running message handler), the consumer is evicted even though heartbeats are still flowing. This catches "alive but stuck" consumers.

If your batches take longer than `max.poll.interval.ms`, you need to either reduce `max.poll.records` or move processing onto a worker thread that doesn't block the poll loop.

</details>

---

## Section 6 — Delivery semantics

### Q6.1 — Walk through how to actually get exactly-once in a Kafka-to-Kafka pipeline.

<details>
<summary>▶ Show answer</summary>

Four pieces:

1. **Idempotent producer** — `enable.idempotence=true`. Broker dedupes retries.
2. **Transactional producer** — `transactional.id=<stable-id>`. Wrap each batch in `begin_transaction()` … `commit_transaction()`.
3. **Commit consumer offsets inside the transaction** — call `producer.send_offsets_to_transaction(offsets, consumer.consumer_group_metadata())` before `commit_transaction()`. This atomically commits "I processed these inputs" with "I produced these outputs".
4. **`isolation.level=read_committed`** on downstream consumers. They skip records from aborted transactions and from in-flight (not-yet-committed) transactions.

Result: every input record contributes exactly once to the output, even across producer crashes. The stable `transactional.id` lets the broker fence out zombie instances after a restart.

</details>

### Q6.2 — Why doesn't "exactly-once" extend to writes against an external database?

<details>
<summary>▶ Show answer</summary>

Kafka's EOS is a Kafka-internal protocol. Transactions span the producer log + consumer offsets, both stored in Kafka. The broker can roll back uncommitted records by marking them aborted in the log.

But Kafka has no way to roll back an `INSERT` into Postgres, an HTTP `POST` to Stripe, or a `kubectl apply`. If your consumer reads, then writes to Postgres, then commits its offset — and crashes between the write and the commit — you replay on restart and the Postgres write happens twice.

The fix is to make external writes **idempotent**:

- Upsert by a unique key (e.g. event_id).
- Conditional writes (`IF NOT EXISTS`, optimistic concurrency).
- Outbox pattern: write a Kafka event and a DB row in the *same DB transaction*, let a CDC connector forward to Kafka. Now the DB is the source of truth, and Kafka EOS handles the forwarding.

</details>

---

## Section 7 — Log compaction & retention

### Q7.1 — Compaction vs. deletion — when do I want each?

<details>
<summary>▶ Show answer</summary>

- **`cleanup.policy=delete`** (default) — time- or size-based eviction. Use for event streams where the *history* matters and old events become irrelevant: clickstreams, logs, metrics, audit trails.
- **`cleanup.policy=compact`** — keep at least the latest record per key forever. Use for changelog / state topics where the *current value per key* is what matters: user profiles, configuration, materialized views, `__consumer_offsets`, Kafka Streams state stores.
- **`cleanup.policy=compact,delete`** — compact, plus a retention bound. Use for changelogs that you also want to prune (e.g. drop tombstones older than 30 days).

</details>

### Q7.2 — How do you delete a key from a compacted topic?

<details>
<summary>▶ Show answer</summary>

Produce a **tombstone**: a record with the key set and the value set to `null`.

The compactor keeps the tombstone until `delete.retention.ms` (default 24h) has elapsed since the tombstone became the latest record for that key, then physically removes both the tombstone and any older records for that key. The lag is intentional — it gives downstream consumers a window to observe the deletion before it's gone.

This is the only deletion mechanism for compacted topics — you can't directly delete arbitrary offsets.

</details>

---

## Section 8 — Streams concepts

### Q8.1 — What's the difference between a KStream and a KTable?

<details>
<summary>▶ Show answer</summary>

Two interpretations of the same underlying topic:

- **KStream** — every record is an independent fact. "User 42 placed order 1001 at 12:00." Past records don't get overwritten by new ones; they accumulate.
- **KTable** — records are *updates* to a keyed state. The latest record per key is the current value. "User 42's current address is X" — a later record for key 42 overwrites the previous one.

Backed by a compacted topic, a KTable is essentially "the current state of a key-value store, materialized from a log." Join a KStream of orders to a KTable of users → enriched stream where each order carries the user's current data.

</details>

### Q8.2 — Where does Streams keep its state, and what happens if the app dies?

<details>
<summary>▶ Show answer</summary>

State stores are local **RocksDB** instances on each app instance — fast embedded key-value stores. But every write to a state store is also written to a **changelog topic** in Kafka (a compacted topic).

When an instance dies and its partitions migrate to another instance:

1. The new owner reads the changelog topic from the beginning.
2. It rebuilds the RocksDB state locally.
3. Once caught up, it starts processing live input.

So Kafka itself is the source of truth for state. The local store is just a cache. This is why Streams apps can be stateless from a deployment perspective — kill them, restart anywhere, state rebuilds from Kafka.

</details>

---

## Section 9 — Operational concerns

### Q9.1 — What is consumer lag and how do you act on it?

<details>
<summary>▶ Show answer</summary>

**Lag** = `log_end_offset - committed_offset` per partition. It's the count of records produced but not yet acknowledged as processed by a given consumer group.

What it tells you:

- Constant low lag → consumer is keeping up.
- Growing lag → consumer can't keep up. Either traffic spiked or processing slowed.
- Stuck lag (no growth, no shrinkage) → consumer is alive but not processing (deadlock, stuck handler).
- Lag = LEO → consumer is offline.

Acting on it:

1. Scale out consumers, up to the partition count.
2. Speed up per-message processing (batch downstream calls, async I/O).
3. Add partitions (offline, plan ahead).
4. Alert on lag SLOs, not on raw numbers — what matters is "how stale is the data the consumer is producing."

</details>

### Q9.2 — A consumer keeps getting kicked out of the group and rejoining ("rebalance storm"). What do you check?

<details>
<summary>▶ Show answer</summary>

Top suspects, in order:

1. **`max.poll.interval.ms` exceeded** — processing per batch is too slow. Reduce `max.poll.records`, move work off the poll thread, or raise the interval (last resort — masks the real problem).
2. **GC pauses or CPU starvation** — JVM consumers with poorly tuned heap can pause longer than `session.timeout.ms`. Profile pauses; tune the GC.
3. **Network flapping between consumer and coordinator** — heartbeats time out. Check broker logs and network metrics.
4. **Static membership not used despite frequent rolling restarts** — set `group.instance.id` to make planned restarts skip rebalance.
5. **Non-cooperative assignor** — every join/leave is a stop-the-world. Switch to `cooperative-sticky`.

</details>

### Q9.3 — Three production config choices that hurt teams the most often.

<details>
<summary>▶ Show answer</summary>

1. **`replication.factor=1`** — one disk = single point of data loss. Production topics should be `rf=3` and `min.insync.replicas=2`. Default new-topic settings at the broker level so nobody can accidentally create RF=1 in production.
2. **`min.insync.replicas` left unset / equal to 1 with `acks=all`** — gives a false sense of durability. A producer can be writing to a single in-sync replica and an `acks=all` ack still arrives. When that broker dies, data is gone.
3. **Auto-creating topics** (`auto.create.topics.enable=true`) with default partition count — typo'd topic names create real topics; throughput-critical topics inherit 1 partition and can't scale. Turn auto-create off; force topic creation through an explicit operation (CLI, IaC, admin client).

</details>

---

## Section 10 — Self-test scenario questions

### Q10.1 — You have a topic `payments` with 12 partitions and a consumer group with 4 instances. You add 8 more instances. What happens?

<details>
<summary>▶ Show answer</summary>

A rebalance is triggered. The 12 partitions are redistributed across 12 consumers — each gets exactly 1. The new throughput ceiling is hit: adding a 13th instance would leave one idle. To scale further, you'd need to add partitions (with the caveats from Q2.4).

</details>

### Q10.2 — You set `acks=all`, `replication.factor=3`, `min.insync.replicas=3`. One broker goes down for maintenance. What happens to producers?

<details>
<summary>▶ Show answer</summary>

The ISR for affected partitions drops to 2, below `min.insync.replicas=3`. Producers writing to those partitions get `NotEnoughReplicasException` and stall (retry until `delivery.timeout.ms`, then fail).

Lesson: `min.insync.replicas` should be `replication.factor - 1`, not `replication.factor`. With RF=3, set MISR=2 — you can lose one broker without producer downtime, and still have two copies of every accepted write.

</details>

### Q10.3 — Your consumer commits offsets manually after processing. A bug crashes the consumer halfway through processing record N. What does the next run see?

<details>
<summary>▶ Show answer</summary>

The next run resumes at offset N (the last committed offset + 1, where the last commit was N-1 → next-to-read is N). Record N is reprocessed. This is at-least-once: record N is delivered twice in total.

If your handler is not idempotent (e.g. inserts into a DB without a unique key), you'll get duplicate side effects. The fix is idempotent processing, not changing the commit position.

</details>

### Q10.4 — A consumer in `read_committed` mode reads a partition that contains a producer's in-flight (uncommitted) transaction. What does it see?

<details>
<summary>▶ Show answer</summary>

It reads everything *up to* the first uncommitted transactional record (the **Last Stable Offset**, LSO) and then stops, waiting. It will not advance past the LSO until the transaction either commits (records become visible) or aborts (records are skipped).

This is what makes EOS possible end-to-end: downstream consumers never observe partial or aborted transactions. The cost is read latency — a stuck producer transaction can stall consumers until it times out and aborts.

</details>

---

## How to use this file

- **Solo study:** read a question, give yourself 30 seconds, then expand to check.
- **Pair / interview prep:** one person asks, the other answers without peeking.
- **Reference:** when something at runtime confuses you ("why is the consumer stuck?"), Ctrl-F here before opening the full README.

Pair this with the [README's live lab](README.md#10-live-lab-walkthrough) — read the theory question, then run the matching command and see the behavior firsthand.
