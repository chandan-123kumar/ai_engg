# Blocking Queue — Design Spec

**Date:** 2026-05-31  
**Language:** Java (no packages, no frameworks)  
**Location:** `system_grinding/blocking_queue/`

## Goal

Implement a generic, bounded blocking queue from scratch in Java, composed on top of the existing `MySemaphore` and `MyMutex` primitives already built in this project.

## Components

| File | Role |
|---|---|
| `MyBlockingQueue.java` | Generic bounded blocking queue |
| `Main.java` | Demo: multiple producers and consumers |

The queue reuses `MySemaphore` from `system_grinding/semaphore/` and `MyMutex` from `system_grinding/mutex/` by copying them into the new directory (no packages, so they must live alongside the queue).

## Internal State

```java
MySemaphore emptySlots  // initialized to capacity — producers acquire before adding
MySemaphore filledSlots // initialized to 0       — consumers acquire before taking
MyMutex     mutex       // guards LinkedList during add/remove
LinkedList<T> queue     // internal storage
```

## Public API

```java
MyBlockingQueue(int capacity)        // capacity > 0, else IllegalArgumentException
void put(T item)   throws InterruptedException  // blocks if full
T    take()        throws InterruptedException  // blocks if empty
int  size()                                     // current item count (approximate)
```

## Data Flow

### `put(item)`
1. `emptySlots.acquire()` — blocks if no empty slots (queue full)
2. `mutex.lock()` — exclusive access to the list
3. `queue.add(item)`
4. `mutex.unlock()`
5. `filledSlots.release()` — wake a waiting consumer

### `take()`
1. `filledSlots.acquire()` — blocks if no filled slots (queue empty)
2. `mutex.lock()` — exclusive access to the list
3. `item = queue.poll()`
4. `mutex.unlock()`
5. `emptySlots.release()` — wake a waiting producer
6. `return item`

The mutex is held only during the brief list operation. No thread blocks while holding the mutex — all waiting happens on the semaphores.

## Demo (Main.java)

- Queue capacity: 5
- 3 producer threads, each puts 5 items (15 total)
- 2 consumer threads, each takes items in a loop until all 15 are consumed
- Each producer/consumer prints its thread name and the item value
- Main thread joins all threads and prints "Done."

## Error Handling

- `capacity <= 0` throws `IllegalArgumentException` in the constructor
- `InterruptedException` is propagated to callers (not swallowed)
- `item == null` is not validated — callers are trusted (internal code)
