# Blocking Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a generic bounded blocking queue `MyBlockingQueue<T>` composed from `MySemaphore` and `MyMutex`, with a multi-producer/consumer demo.

**Architecture:** Two semaphores (`emptySlots`, `filledSlots`) coordinate producer/consumer blocking without holding a lock. A `MyMutex` protects the `LinkedList` only during the brief add/remove operation. All three primitives are copied into the new directory since the project uses no packages.

**Tech Stack:** Java (plain javac/java, no build tool, no test framework — verification via console output in Main.java)

**Spec:** `docs/superpowers/specs/2026-05-31-blocking-queue-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `system_grinding/blocking_queue/MySemaphore.java` | Create (copy) | Semaphore primitive |
| `system_grinding/blocking_queue/MyMutex.java` | Create (copy) | Mutex primitive |
| `system_grinding/blocking_queue/MyBlockingQueue.java` | Create | Bounded generic blocking queue |
| `system_grinding/blocking_queue/Main.java` | Create | Demo: 3 producers + 2 consumers |

---

### Task 1: Set up directory and copy primitives

**Files:**
- Create: `system_grinding/blocking_queue/MySemaphore.java`
- Create: `system_grinding/blocking_queue/MyMutex.java`

- [ ] **Step 1: Create the directory**

```bash
mkdir system_grinding/blocking_queue
```

- [ ] **Step 2: Copy MySemaphore**

Create `system_grinding/blocking_queue/MySemaphore.java` with this exact content:

```java
public class MySemaphore {
    private int permits;

    public MySemaphore(int permits) {
        if (permits < 0) throw new IllegalArgumentException("permits must be >= 0");
        this.permits = permits;
    }

    public synchronized void acquire() throws InterruptedException {
        while (permits == 0) {
            wait();
        }
        permits--;
    }

    public synchronized void release() {
        permits++;
        notifyAll();
    }
}
```

- [ ] **Step 3: Copy MyMutex**

Create `system_grinding/blocking_queue/MyMutex.java` with this exact content:

```java
public class MyMutex {
    private boolean locked = false;

    public synchronized void lock() throws InterruptedException {
        while (locked) {
            wait();
        }
        locked = true;
    }

    public synchronized void unlock() {
        locked = false;
        notifyAll();
    }
}
```

- [ ] **Step 4: Verify both files compile**

```bash
cd system_grinding/blocking_queue && javac MySemaphore.java MyMutex.java
```

Expected: no output, no errors. Two `.class` files appear.

- [ ] **Step 5: Commit**

```bash
git add system_grinding/blocking_queue/MySemaphore.java system_grinding/blocking_queue/MyMutex.java
git commit -m "feat: add blocking_queue directory with MySemaphore and MyMutex copies"
```

---

### Task 2: Implement MyBlockingQueue — constructor and size()

**Files:**
- Create: `system_grinding/blocking_queue/MyBlockingQueue.java`

- [ ] **Step 1: Write the skeleton with constructor and size()**

Create `system_grinding/blocking_queue/MyBlockingQueue.java`:

```java
import java.util.LinkedList;

public class MyBlockingQueue<T> {
    private final MySemaphore emptySlots;
    private final MySemaphore filledSlots;
    private final MyMutex mutex;
    private final LinkedList<T> queue;

    public MyBlockingQueue(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
        this.emptySlots = new MySemaphore(capacity);
        this.filledSlots = new MySemaphore(0);
        this.mutex = new MyMutex();
        this.queue = new LinkedList<>();
    }

    public int size() {
        return queue.size();
    }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
cd system_grinding/blocking_queue && javac MySemaphore.java MyMutex.java MyBlockingQueue.java
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add system_grinding/blocking_queue/MyBlockingQueue.java
git commit -m "feat: add MyBlockingQueue skeleton with constructor and size()"
```

---

### Task 3: Implement put()

**Files:**
- Modify: `system_grinding/blocking_queue/MyBlockingQueue.java`

- [ ] **Step 1: Add put() to MyBlockingQueue**

Add this method inside the class body, after `size()`:

```java
public void put(T item) throws InterruptedException {
    emptySlots.acquire();
    mutex.lock();
    queue.add(item);
    mutex.unlock();
    filledSlots.release();
}
```

Full file after edit:

```java
import java.util.LinkedList;

public class MyBlockingQueue<T> {
    private final MySemaphore emptySlots;
    private final MySemaphore filledSlots;
    private final MyMutex mutex;
    private final LinkedList<T> queue;

    public MyBlockingQueue(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
        this.emptySlots = new MySemaphore(capacity);
        this.filledSlots = new MySemaphore(0);
        this.mutex = new MyMutex();
        this.queue = new LinkedList<>();
    }

    public void put(T item) throws InterruptedException {
        emptySlots.acquire();
        mutex.lock();
        queue.add(item);
        mutex.unlock();
        filledSlots.release();
    }

    public int size() {
        return queue.size();
    }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
cd system_grinding/blocking_queue && javac MySemaphore.java MyMutex.java MyBlockingQueue.java
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add system_grinding/blocking_queue/MyBlockingQueue.java
git commit -m "feat: implement put() on MyBlockingQueue"
```

---

### Task 4: Implement take()

**Files:**
- Modify: `system_grinding/blocking_queue/MyBlockingQueue.java`

- [ ] **Step 1: Add take() to MyBlockingQueue**

Add this method after `put()`:

```java
public T take() throws InterruptedException {
    filledSlots.acquire();
    mutex.lock();
    T item = queue.poll();
    mutex.unlock();
    emptySlots.release();
    return item;
}
```

Full file after edit:

```java
import java.util.LinkedList;

public class MyBlockingQueue<T> {
    private final MySemaphore emptySlots;
    private final MySemaphore filledSlots;
    private final MyMutex mutex;
    private final LinkedList<T> queue;

    public MyBlockingQueue(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be > 0");
        this.emptySlots = new MySemaphore(capacity);
        this.filledSlots = new MySemaphore(0);
        this.mutex = new MyMutex();
        this.queue = new LinkedList<>();
    }

    public void put(T item) throws InterruptedException {
        emptySlots.acquire();
        mutex.lock();
        queue.add(item);
        mutex.unlock();
        filledSlots.release();
    }

    public T take() throws InterruptedException {
        filledSlots.acquire();
        mutex.lock();
        T item = queue.poll();
        mutex.unlock();
        emptySlots.release();
        return item;
    }

    public int size() {
        return queue.size();
    }
}
```

- [ ] **Step 2: Verify it compiles**

```bash
cd system_grinding/blocking_queue && javac MySemaphore.java MyMutex.java MyBlockingQueue.java
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add system_grinding/blocking_queue/MyBlockingQueue.java
git commit -m "feat: implement take() on MyBlockingQueue"
```

---

### Task 5: Write Main.java demo and verify end-to-end

**Files:**
- Create: `system_grinding/blocking_queue/Main.java`

- [ ] **Step 1: Create Main.java**

Uses the **poison pill pattern**: after all producers finish, main puts one `-1` sentinel per consumer. Each consumer loops until it receives `-1`, then exits. This avoids any race condition in consumer shutdown.

Create `system_grinding/blocking_queue/Main.java`:

```java
public class Main {
    static final int CAPACITY = 5;
    static final int ITEMS_PER_PRODUCER = 5;
    static final int NUM_PRODUCERS = 3;
    static final int NUM_CONSUMERS = 2;
    static final int POISON = -1;

    public static void main(String[] args) throws InterruptedException {
        MyBlockingQueue<Integer> queue = new MyBlockingQueue<>(CAPACITY);

        Thread[] producers = new Thread[NUM_PRODUCERS];
        Thread[] consumers = new Thread[NUM_CONSUMERS];

        for (int i = 0; i < NUM_PRODUCERS; i++) {
            final int producerId = i;
            producers[i] = new Thread(() -> {
                for (int j = 0; j < ITEMS_PER_PRODUCER; j++) {
                    try {
                        int item = producerId * ITEMS_PER_PRODUCER + j;
                        queue.put(item);
                        System.out.println(Thread.currentThread().getName() + " put " + item);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                }
            }, "Producer-" + i);
        }

        for (int i = 0; i < NUM_CONSUMERS; i++) {
            consumers[i] = new Thread(() -> {
                try {
                    while (true) {
                        Integer item = queue.take();
                        if (item == POISON) break;
                        System.out.println(Thread.currentThread().getName() + " took " + item);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "Consumer-" + i);
        }

        for (Thread c : consumers) c.start();
        for (Thread p : producers) p.start();

        for (Thread p : producers) p.join();

        // Send one poison pill per consumer to signal shutdown
        for (int i = 0; i < NUM_CONSUMERS; i++) {
            queue.put(POISON);
        }

        for (Thread c : consumers) c.join();

        System.out.println("Done.");
    }
}
```

- [ ] **Step 2: Compile everything**

```bash
cd system_grinding/blocking_queue && javac MySemaphore.java MyMutex.java MyBlockingQueue.java Main.java
```

Expected: no errors.

- [ ] **Step 3: Run and verify**

```bash
cd system_grinding/blocking_queue && java Main
```

Expected output (order of put/took lines will vary, but the final line must be):
```
Done.
```

You should see 15 "put" lines and 15 "took" lines (items 0–14). The program must exit cleanly with no deadlock or hang.

- [ ] **Step 4: Commit**

```bash
git add system_grinding/blocking_queue/Main.java
git commit -m "feat: add blocking queue demo with 3 producers and 2 consumers"
```

---

## Done

After all tasks complete, `system_grinding/blocking_queue/` contains a working generic bounded blocking queue built from `MySemaphore` + `MyMutex`, verified by a multi-producer/consumer demo that produces and consumes exactly 15 items.
