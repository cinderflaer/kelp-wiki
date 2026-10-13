---
title: "`std/pool`"
description: "A fixed thread pool: `pool.new(n)`, `Pool.spawn(closure)`, `Pool.join` and `Pool.panicked`. A panicking job is counted and its worker survives; dropping a pool joins it. One thread is created per job. Hosted only."
isPublished: true
tags: "stdlib, concurrency"
---
A fixed pool of worker threads that run closures from one first-in first-out
queue. Written in Kelp over [`Mutex`, `Condvar`](/stdlib/sync) and
[`thread.spawn`](/stdlib/thread). Hosted only.

> **Status on current `main`.** `std/pool` is refused on `main`. A program that uses
> `pool.new` is refused with `'std.pool.PoolShared' cannot be a thread's argument in a
> hosted build: 'std.pool.PoolShared' is a resource, ...`, because its `PoolShared` record
> holds a `Mutex` and a `Condvar`, which are runtime resources. The pool passes a
> `PoolShared` to each worker thread, and the checker refuses that by name.
> The job type `Job` holds a closure, which is memory, so it is not the blocker. The rest
> of this page describes the API.


```kelp
impl "std/pool"
```

It is a module of its own, not a part of `std/thread`, because a module cannot
call its own builtins (`thread.spawn`) by name.

## Surface

```
fun pool.new(workers: i32).return: Pool
fun Pool.spawn(job: move closure())
fun Pool.join()
fun Pool.panicked().return: i32
```

| Call | Returns | Notes |
| --- | --- | --- |
| `pool.new(workers)` | `Pool` | starts `workers` threads. Fewer than 1 panics |
| `p.spawn(job)` | - | queues a `move closure()`; it runs on some worker, in queue order. A job owns what it captured |
| `p.join()` | - | stops accepting work, runs everything still queued, and waits until every worker has exited. Safe to call twice |
| `p.panicked()` | `i32` | how many jobs have panicked so far |

`Drop` on a `Pool` calls `join`, so a pool that goes out of scope shuts down
cleanly: every queued job has finished when the scope ends.

## Example

Ten jobs on three workers. The job for `4` panics; the other nine add their
number to a shared atomic, and the pool counts the panic:

```kelp
impl "std/pool"
impl "std/sync"
impl "std/atomic"

pd val total: AtomicI64 = AtomicI64.new(0)

fun add(n: i64) {
    total.fetch_add(value = n, order = atomic.Ordering.SeqCst)
}

fun boom() {
    panic("job exploded")
}

fun main() {
    var p = pool.new(3)
    var i: i64 = 1
    while i <= 10 {
        val k = i
        p.spawn(fun() {
            if k == 4 {
                boom()
            }
            add(k)
        })
        i += 1
    }
    p.join()
    print(total.load(order = atomic.Ordering.SeqCst))
    print(p.panicked())
}
```

It prints:

```
51
1
```

`51` is 55 minus the missing 4, and `1` is the one panic. The job's panic did not
take its worker down: the other jobs still ran.

### Drop joins

No explicit `join` is needed when the pool goes out of scope. When `run`
returns, its pool is dropped, which joins it, so all fifty jobs have finished:

```kelp
impl "std/pool"
impl "std/atomic"

pd val ran: AtomicI64 = AtomicI64.new(0)

fun count_one() {
    ran.fetch_add(value = 1, order = atomic.Ordering.SeqCst)
}

fun run() {
    val p = pool.new(3)
    var i = 0
    while i < 50 {
        p.spawn(fun() { count_one() })
        i += 1
    }
}

fun main() {
    run()
    print(ran.load(order = atomic.Ordering.SeqCst))
}
```

```
50
```

## Getting results home

A job returns nothing, so results travel over a [channel](/stdlib/sync#channels)
the job owns a sender of (each job takes its own `tx.clone()`), or into an
atomic as above.

```kelp
impl "std/pool"
impl "std/sync"
impl "std/result"

fun main() {
    val (tx, rx) = sync.bounded<i64>(4)
    var rxm = rx
    val p = pool.new(2)
    var i: i64 = 1
    while i <= 5 {
        val mine = tx.clone()
        val n = i
        p.spawn(fun() {
            val back = mine.send(n * n)
        })
        i += 1
    }
    var sum: i64 = 0
    var got = 0
    while got < 5 {
        when rxm.recv() {
            Ok(v) -> sum += v
            Err(_) -> {}
        }
        got += 1
    }
    print(sum)
}
```

```
55
```

The loop counts five receives instead of using `for v in rx`, because `main`
still holds `tx` itself, so the channel would not close on its own.

## How a panic is survived, and what it costs

A Kelp panic ends the thread it happens in, and there is no unwinding to resume
the frame. So each worker runs **every job on a thread of its own** and joins it:
an `Err` from that join is the panic, the worker counts it and takes the next
job. The honest consequences:

- **One thread is created per job.** A pool does not save thread creation; it
  limits how many run at once and gives them a queue.
- `thread.current_id()` differs between two jobs run by the same worker.
- A panicking job's frame is abandoned, exactly as in a plain `thread.spawn`:
  values it owned are not dropped, and a `Mutex` it held inside `lock` is
  released and poisoned, so a later `lock` on it panics.
- A thread-local jump back to the worker was rejected because it would skip the
  cleanup handlers a `lock` block registers, leaving the mutex locked.

## Refusals and limits

- `pool.new(0)` panics: `pool.new: a pool needs at least one worker`.
- `p.spawn(...)` after `p.join()` panics:
  `Pool.spawn: the pool has been joined`. Queue nothing on a joined pool.
- The queue is FIFO only: no priority, no fairness policy, no cancellation of a
  queued job, and no way to ask a job for a value other than a channel or a
  shared location.
- The worker threads are detached and counted internally, not kept as handles
  (a `Thread<T>` cannot be a `List` element), so a pool cannot name them.
- **Hosted only.** A freestanding build refuses the module by name:

  ```
  error: the module 'std/pool' is unavailable in a freestanding build: it needs a hosted runtime (libc or the 'kelp_rt' helpers); the std modules a freestanding project may implement are std/arena, std/atomic, std/convert, std/frame, std/irq, std/iter, std/list, std/math, std/ops, std/option, std/regex, std/result, std/str
  ```

The tests are `pool_sum` (1000 jobs on four workers, sum 499500), `pool_panics`,
`pool_drop_joins`, `pool_spawn_after_join` and `pool_zero_workers`, each on both
backends.

## See also

- [`std/sync`](/stdlib/sync) for `Mutex`, `Condvar` and channels
- [`std/thread`](/stdlib/thread)
- [`std/atomic`](/stdlib/atomic)
- [Concurrency in v1](/language/concurrency)
- [Limits in v1](/language/limits)
