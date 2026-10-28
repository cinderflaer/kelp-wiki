---
title: "`std/pool`"
description: "A fixed thread pool: `pool.new(n)`, `Pool.spawn(closure)`, `Pool.join` and `Pool.panicked`. A panicking job is counted and its worker survives; dropping a pool joins it. One thread is created per job. Hosted only."
isPublished: true
tags: "stdlib, concurrency"
---
A fixed pool of worker threads that run closures from one first-in first-out
queue. Written in Kelp over [`Mutex`, `Condvar`](/stdlib/sync) and
[`thread.spawn`](/stdlib/thread). Hosted only.

> **Status on current `main`.** `std/pool` builds and runs on `main`. The test
> `a_pool_runs_a_thousand_jobs` in `kelpc/tests/compile_and_run/atomics.rs` runs
> `kelpc/tests/fixtures/pool_sum.kp`, which queues 1000 jobs on four workers and prints
> `499500` and `0`. Other pool fixtures cover a panicking job, a zero-worker pool and a
> spawn after the join. A `Pool` value is a resource with a destructor, so it stays in
> the thread that made it and does not cross to a worker.


```kelp
impl "std/pool"
```

It is a module of its own, not a part of `std/thread`, because a module cannot
call its own builtins (`thread.spawn`) by name.

## Surface

```
fun pool.new(workers: i32) => Pool
fun Pool.spawn(job: move closure fun())
fun Pool.join()
fun Pool.panicked() => i32
fun joinOrReport<t>(handle: move Thread<t>) => option.Option<t>
```

| Call | Returns | Notes |
| --- | --- | --- |
| `pool.new(workers)` | `Pool` | starts `workers` threads. Fewer than 1 panics |
| `p.spawn(job)` | - | queues a `move closure fun()`; it runs on some worker, in queue order. A job owns what it captured |
| `p.join()` | - | stops accepting work, runs everything still queued, and waits until every worker has exited. Safe to call twice |
| `p.panicked()` | `i32` | how many jobs have panicked so far |
| `pool.joinOrReport(handle)` | `Option<T>` | joins one thread handle; an `Err` prints the panic text and gives `None`. See below |

`Drop` on a `Pool` calls `join`, so a pool that goes out of scope shuts down
cleanly: every queued job has finished when the scope ends.

## Joining one handle and reporting its error

`pool.joinOrReport(handle)` joins one thread handle, the way a job's worker
joins its job thread above. It returns the worker's value as `Some`. An `Err`
prints the panic text on stdout and returns `None`. The handle is consumed, so
it joins once.

It lives in this module because a module cannot call its own builtins:
`thread.join` is reached through `impl "std/thread"`, which this module already
uses. A program that calls it writes `impl "std/pool"` and `impl "std/option"`.
The compiler does not infer the type argument from the handle yet, so the call
names it, or the binding is annotated.

```kelp
impl "std/thread"
impl "std/option"
impl "std/pool"

fun doubled(x: move i64) => i64 = x * 2

fun main() {
    val h: Thread<i64> = thread.spawn(doubled, 21)
    if let Some(v) = pool.joinOrReport<i64>(h) {
        print(v)                              // 42
    }
}
```

Use `thread.join` and its `Err` arm when the program needs the `ThreadErr`
itself.

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
- `thread.currentId()` differs between two jobs run by the same worker.
- A panicking job's owned locals are dropped on the way out, as in a plain
  `thread.spawn` worker (see [Concurrency in v1](/language/concurrency)). A `Mutex` it
  held inside `lock` is released and poisoned, so a later `lock` on it panics.
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
