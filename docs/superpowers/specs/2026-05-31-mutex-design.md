# Mutex Implementation Design

**Date:** 2026-05-31
**Status:** Approved

## Goal

Build a simple `MyMutex` class in Java for learning purposes, mirroring the existing `MySemaphore` implementation. The goal is to understand how a mutex works and how it differs from a semaphore.

## Structure

```
system_grinding/mutex/
  MyMutex.java   — implementation
  Main.java      — demo
```

## MyMutex.java

- Single field: `private boolean locked`
- Starts unlocked (no constructor args needed)
- `lock()` — `synchronized`, loops `while (locked) wait()`, then sets `locked = true`
- `unlock()` — `synchronized`, sets `locked = false`, calls `notifyAll()`

The `while` loop (not `if`) is required: `notifyAll()` wakes all waiting threads, but only one should proceed — the rest must re-check the condition and go back to waiting.

## Main.java

Two threads each call `lock()`, print a message, sleep briefly to simulate work, then call `unlock()`. Demonstrates that only one thread holds the mutex at a time.

## Key Contrast with MySemaphore

| | `MySemaphore` | `MyMutex` |
|---|---|---|
| State | `int permits` | `boolean locked` |
| Capacity | N concurrent threads | exactly 1 |
| Gate condition | `permits == 0` | `locked == true` |
| Acquire | `permits--` | `locked = true` |
| Release | `permits++` | `locked = false` |

A mutex is conceptually a semaphore with `permits=1`, but the boolean makes the binary (locked/unlocked) nature explicit.

## Out of Scope

- Ownership enforcement (only acquiring thread can release) — kept simple intentionally
- Reentrant locking
- Fairness guarantees
