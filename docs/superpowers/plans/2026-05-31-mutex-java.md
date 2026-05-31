# Mutex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `MyMutex` Java class using `synchronized + wait/notifyAll` that mirrors the semaphore folder structure, for learning how a mutex differs from a semaphore.

**Architecture:** A boolean `locked` field guards entry — `lock()` waits while `locked == true` then sets it `true`; `unlock()` sets it `false` and wakes all waiters. The `Main.java` demo runs two threads competing for the mutex to show mutual exclusion.

**Tech Stack:** Java (plain javac, no build tool)

---

### Task 1: Create MyMutex.java

**Files:**
- Create: `system_grinding/mutex/MyMutex.java`

- [ ] **Step 1: Create the file**

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

- [ ] **Step 2: Compile to verify no syntax errors**

```bash
cd system_grinding/mutex
javac MyMutex.java
```

Expected: no output, `MyMutex.class` created.

- [ ] **Step 3: Commit**

```bash
git add system_grinding/mutex/MyMutex.java
git commit -m "feat: add MyMutex with lock/unlock using wait/notifyAll"
```

---

### Task 2: Create Main.java demo

**Files:**
- Create: `system_grinding/mutex/Main.java`

- [ ] **Step 1: Create the file**

```java
public class Main {
    public static void main(String[] args) throws InterruptedException {
        MyMutex mutex = new MyMutex();

        Thread threadA = new Thread(() -> work(mutex), "Thread-A");
        Thread threadB = new Thread(() -> work(mutex), "Thread-B");

        threadA.start();
        threadB.start();

        threadA.join();
        threadB.join();

        System.out.println("Done.");
    }

    static void work(MyMutex mutex) {
        try {
            mutex.lock();
            System.out.println(Thread.currentThread().getName() + " acquired lock");
            Thread.sleep(1000);
            mutex.unlock();
            System.out.println(Thread.currentThread().getName() + " released lock");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

- [ ] **Step 2: Compile both files**

```bash
cd system_grinding/mutex
javac MyMutex.java Main.java
```

Expected: no errors, both `.class` files created.

- [ ] **Step 3: Run the demo**

```bash
cd system_grinding/mutex
java Main
```

Expected output (order of A/B may vary, but they never interleave):
```
Thread-A acquired lock
Thread-A released lock
Thread-B acquired lock
Thread-B released lock
Done.
```

The key observation: the second thread's "acquired lock" line never appears before the first thread's "released lock" line — that's mutual exclusion.

- [ ] **Step 4: Commit**

```bash
git add system_grinding/mutex/Main.java system_grinding/mutex/Main.class system_grinding/mutex/MyMutex.class
git commit -m "feat: add mutex demo with two competing threads"
```

---

## Spec Coverage Check

| Spec requirement | Task |
|---|---|
| `boolean locked` field | Task 1 |
| `lock()` with `while/wait` | Task 1 |
| `unlock()` with `notifyAll` | Task 1 |
| Two-thread demo | Task 2 |
| Mirrors semaphore folder structure | Both tasks |
