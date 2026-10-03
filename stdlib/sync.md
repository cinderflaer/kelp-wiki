---
title: "`std/sync`"
description: "`Mutex<T>`, `RwLock<T>` and `Condvar`: guarded access through scoped blocks, released on every exit and poisoned by a panic, plus `wait_while` for waiting on a condition. Hosted only. Channels and a thread pool are not shipped."
isPublished: true
tags: "stdlib, concurrency"
---
`Mutex<T>`, `RwLock<T>` and `Condvar`: guarded access through scoped blocks,
released on every exit and poisoned by a panic, and a condition wait that
releases the lock around the sleep. Hosted only.

```kelp
impl "std/sync"
```

`Mutex<T>` is a compiler builtin in the shape `Atomic<T>`/`Thread<T>` have: one
monomorphized type per element, **not `Copy`**, with a drop. `T` is any owned,
borrow-free value, so `Mutex<i64>`, `Mutex<String>` and `Mutex<List<i32>>` all
work. The type is reachable without the import; naming `std/sync` is how a
program declares the module's surface it is using. It is ungated, like
`std/atomic`.

## Surface

```
fun Mutex.new(value: move T).R: Mutex<T>
fun Mutex<T>.lock(block: scoped fun(mut T).R: R).R: R
fun Mutex<T>.into_inner().R: T
```

| Call | Returns | Notes |
| --- | --- | --- |
| `Mutex.new(value: move T)` | `Mutex<T>` | takes the guarded value by move |
| `Mutex<T>.lock(block: scoped fun(mut T).R: R)` | `R` | runs the block while the lock is held; the block's tail is the call's value |
| `Mutex<T>.into_inner()` | `T` | consumes the mutex and hands the value out |

`Mutex<T>` also has `wait_while` and `wait_while_timeout`, which pair it with a
[`Condvar`](#condvar-and-wait_while) below. `RwLock<T>` follows right after.

## Example

This program compiles and runs with the output shown:

```kelp
fun take_then_return(c: &Mutex<i64>) {
    c.lock { v ->
        *v = *v + 1
        return
    }
}

fun main() {
    val m: Mutex<i64> = Mutex.new(7)
    print(m.lock { v -> *v + 1 })
    take_then_return(&m)
    print(m.lock { v -> *v })
    print(m.into_inner())
}
```

```
8
8
8
```

The second call's `return` ends the block, the lock is released, and the later
`lock` works: it would deadlock if the first block had left the mutex held.

## The scoped lock block

- `m.lock { v -> ... }` passes `v: mut T` to a `scoped fun(mut T).R: R`, so the
  mutable borrow is the existing non-escaping one: it cannot be stored in a
  `datac`, returned, put in a container, or captured by an ordinary closure,
  because those are all ordinary type mismatches. The block's tail is the call's
  value.
- The block's return type is inferred from the block. `R` is not known before
  the block is checked (`m.lock { v -> *v }` writes no type), so the literal is
  checked with its parameter types from the expected `scoped fun(mut T).R: R`
  and its return from the body's tail. When the call site names a type
  (`return m.lock { v -> ... }` in a function returning `Result<_, _>`), that
  type is used instead, which is what lets a `?` inside the block propagate the
  block's return.
- A `return` inside the block returns from the **block literal**, and a `?`
  returns the failure from the block literal, so the runtime call still returns
  and the unlock still runs. A `break` or `continue` inside the block cannot leave a loop outside the block: a `break` written there is refused as having no enclosing loop.

## Release and poisoning

- `lock` lowers to the runtime's `kelp_mutex_run(record, body, code, env, out)`,
  which acquires the lock, checks the poison flag, calls the generated block
  body with the `&mut T`, and releases the lock on the normal way out.
- A panic inside the block is the one exit the ordinary call cannot see. The
  block body calls `kelp_panic`, which in a worker ends the thread with
  `pthread_exit`. The runtime registers a cleanup handler before the body runs,
  so `pthread_exit` runs it: the lock is released and the mutex is marked
  **POISONED**. A later `lock` panics with `mutex poisoned`. There is no
  unwinding, so the panicking frame's owned values are still abandoned; the
  mutex itself is not, which is the point of the cleanup handler.
- `into_inner` is the only other way out, and it consumes the whole mutex.

## Crossing a thread boundary

A `&Mutex<T>` is a shared borrow whose pointee has no reachable `&mut` path: the
only way to reach `T` is the lock, which the runtime serializes. The crossing
rule therefore accepts it for the same reason it accepts `&Atomic<T>`, so a
`pd val` mutex can be handed to `thread.spawn` exactly as a `pd val` atomic can.
That holds whatever `T` is, including a `datac` with a `var` field, because the
field is unreachable without the lock. The element predicate keeps a borrow,
`str` or `View` out of the slot in the first place.

```kelp
impl "std/thread"
impl "std/result"

pd val counter: Mutex<i64> = Mutex.new(0)

fun bump(c: &Mutex<i64>).R: i64 {
    c.lock { v -> *v = *v + 1 }
    0
}

fun main() {
    val t = thread.spawn(bump, &counter)
    val r = thread.join(t)
    print(counter.lock { v -> *v })   // 1
}
```

## `RwLock<T>`

A reader/writer lock in the same shape as `Mutex<T>`: a compiler builtin, not
`Copy`, reachable without the import, guarding one owned borrow-free value that
is reached only through a scoped block.

```
fun RwLock.new(value: move T).R: RwLock<T>
fun RwLock<T>.read(block: scoped fun(&T).R: R).R: R
fun RwLock<T>.write(block: scoped fun(mut T).R: R).R: R
fun RwLock<T>.try_read(block: scoped fun(&T).R: R).R: Option<R>
fun RwLock<T>.try_write(block: scoped fun(mut T).R: R).R: Option<R>
fun RwLock<T>.into_inner().R: T
```

| Call | Returns | Notes |
| --- | --- | --- |
| `RwLock.new(value: move T)` | `RwLock<T>` | takes the guarded value by move |
| `read(block)` | `R` | the block gets a shared `&T`; many readers run at once |
| `write(block)` | `R` | the block gets `mut T`; one writer runs alone |
| `try_read(block)` / `try_write(block)` | `Option<R>` | the block runs only if the lock was free; `None` means it was busy and the block did not run |
| `into_inner()` | `T` | consumes the lock |

This program shares one lock between the main thread and a worker. It prints, on
the LLVM backend and under `KELPC_ORACLE=c` alike:

```kelp
impl "std/thread"
impl "std/result"
impl "std/option"

pd val config: RwLock<i64> = RwLock.new(10)

fun bump(c: &RwLock<i64>).R: i64 {
    c.write { v -> *v += 5 }
    c.read { v -> *v }
}

fun probe(c: &RwLock<i64>) {
    c.read { v ->
        val w = c.try_write { x -> *x = 0 }
        print(option.is_none(o = w))
    }
}

fun main() {
    print(config.read { v -> *v })
    val t = thread.spawn(bump, &config)
    when thread.join(t) {
        Ok(v) -> print(v)
        Err(e) -> print(e.message)
    }
    print(config.read { v -> *v * 2 })
    // a read is busy for a writer, and a write is busy for everyone
    probe(&config)
    val last = config.try_write { v ->
        *v += 1
        *v
    }
    print(option.unwrap(o = last))
}
```

```
10
15
30
true
16
```

- The worker adds 5 under `write` and reads back 15; the main thread reads 15
  and doubles it to 30.
- Inside `probe`'s `read`, `try_write` finds the lock busy (`true` for
  `is_none`). A `read` block cannot name the passdown directly, so the lock is
  passed to `probe` as a parameter, the same rule every `pd` follows in a `fun`
  literal.
- After the reads end, `try_write` gets the lock and the block's value, 16, comes
  back as `Some`.

**Policy.** The lock is **writer-preferring**: a waiting writer blocks new
readers, so a stream of readers cannot starve it, and a busy `try_read` also
fails while a writer is waiting. It is a runtime built from a mutex, two
condition variables and three counters rather than `pthread_rwlock_t`, whose
policy is unspecified.

**Poisoning.** A panic inside `write` releases the lock and **poisons** it: every
later `read` or `write` panics with `rwlock poisoned`. A panic inside `read`
releases the read and does **not** poison, because a reader never changes the
value. `try_read` and `try_write` never poison. This worker panics inside
`write`:

```kelp
impl "std/thread"
impl "std/result"

pd val rw: RwLock<i64> = RwLock.new(0)

fun boom(r: &RwLock<i64>).R: i64 {
    r.write { v ->
        *v = 99
        panic("writer exploded")
    }
}

fun main() {
    val t = thread.spawn(boom, &rw)
    when thread.join(t) {
        Ok(_) -> print("joined")
        Err(e) -> print(e.message)
    }
    print(rw.read { v -> *v })
}
```

Standard output carries the worker's panic text, standard error carries the
second panic, and the exit status is 1, on both backends:

```
writer exploded
panic: rwlock poisoned
```

`RwLock<T>` crosses a thread boundary the same way `Mutex<T>` does (a `&RwLock<T>`
in a `pd`, as above), and `T` is held to the same element rule as `Mutex`.

## `Condvar` and `wait_while`

A condition variable. A wait has to release the mutex's own lock around the
sleep, which a scoped guard cannot express, so the wait is a method **on the
mutex** that takes the `Condvar`:

```
fun Condvar.new().R: Condvar
fun Condvar.notify_one()
fun Condvar.notify_all()
fun Mutex<T>.wait_while(cv: &Condvar, pred: fun(&T).R: bool, block: scoped fun(mut T).R: R).R: R
fun Mutex<T>.wait_while_timeout(cv: &Condvar, pred: fun(&T).R: bool, millis: i64, block: scoped fun(mut T).R: R).R: Option<R>
```

`m.wait_while(&cv, pred) { v -> ... }` sleeps while `pred(&v)` is true, re-tests
it after every wakeup, and then runs the block with the lock held. A spurious
wakeup is invisible to the caller, and there is no bare `wait`. A panic in the
predicate or the block releases and poisons the mutex like a panic in `lock`.

```kelp
impl "std/thread"
impl "std/result"

pd val shared: Shared = Shared(
    box = Mutex.new(Mailbox(ready = false, value = 0)),
    cv = Condvar.new(),
)

datac Mailbox(var ready: bool, var value: i64)
datac Shared(val box: Mutex<Mailbox>, val cv: Condvar)

fun not_ready(m: &Mailbox).R: bool = !m.ready

fun consumer(s: &Shared).R: i64 {
    s.box.wait_while(&s.cv, not_ready) { m -> m.value }
}

fun main() {
    val t = thread.spawn(consumer, &shared)
    shared.box.lock { m ->
        m.value = 42
        m.ready = true
    }
    shared.cv.notify_all()
    when thread.join(t) {
        Ok(v) -> print(v)
        Err(e) -> print(e.message)
    }
}
```

It prints `42` on both backends:

```
42
```

The consumer waits until `ready` is set; the main thread sets it under `lock` and
calls `notify_all`. Whichever side runs first, the wakeup cannot be missed,
because the predicate is tested under the lock before sleeping. The mutex and the
condition variable travel together as one shared borrow of a `pd`.

`wait_while_timeout` also gives up after `millis` milliseconds. It shares `try_*`'s
shape: `None` means the deadline passed with the predicate still true and the
block did not run.

```kelp
impl "std/option"

fun not_ready(v: &i64).R: bool = v == 0

fun main() {
    val m: Mutex<i64> = Mutex.new(0)
    val cv: Condvar = Condvar.new()
    val first = m.wait_while_timeout(&cv, not_ready, 30) { v -> *v }
    print(option.is_none(o = first))
    m.lock { v -> *v = 7 }
    val second = m.wait_while_timeout(&cv, not_ready, 30) { v -> *v }
    print(option.unwrap(o = second))
}
```

```
true
7
```

Nothing notifies, so the first wait times out (`is_none` is `true`); after the
value changes the predicate is already false and the second returns `Some(7)`.

## Channels and a thread pool

**Not shipped.** A design for channels (`Sender<T>`/`Receiver<T>`, `for v in rx`)
and a worker pool (`Pool.spawn`/`join`) is written down in
[`plan/sync.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/sync.md),
and its status file says neither was started: a channel needs tuple construction
in both code generators and a builtin iterator, and the pool needs the panic path
to be able to catch a job's panic so the same worker survives. There is no `chan`
module, no `Sender`, `Receiver` or `Pool`, and nothing to call. Today a program
shares state through `Atomic<T>`, `Mutex<T>`, `RwLock<T>` and `Condvar`, or gives
each worker its own copy and joins it.

## Hosted only

The runtime half is libc's pthread primitives, so a freestanding manifest refuses
`Mutex<T>`, `RwLock<T>` and `Condvar` by name. The `Mutex` message, for
example:

```
error: the binding 'm' has type 'Mutex', whose runtime half is a pthread mutex: a freestanding program has no threads and no libc, so a kernel would use a spin lock over an `Atomic<T>` instead
```

The message names the alternative a kernel would use. Freestanding is LLVM-only
by design, and neither backend can lower a mutex without the hosted runtime.

## Refusals

- The slot holds any owned, borrow-free value. `unit` and a borrowed type are
  refused by name:

  ```
  error: 'Mutex.new' needs a value to guard, found 'unit'
  error: 'str' cannot be a 'Mutex' element: a mutex is shared across threads, and a borrow, a 'str' or a 'View' in the slot would be a thread reading data another frame owns. Guard an owned value instead
  ```

- The borrow cannot escape the block. Returning `v` from a function with no
  declared return type is `return type mismatch: expected 'unit', found 'mut
  i64'`, and a `fun` literal that tries to capture `v` is refused because the
  environment it would be stored in outlives the frame the borrow points into.

## What is deliberately out of scope

- A try-lock or timed lock on `Mutex<T>` itself (`RwLock<T>` has `try_read` and
  `try_write`), and an ordering slot.
- A `lock` that returns a guard value: the scoped block is the whole reason the
  borrow cannot escape, and a returned guard would reintroduce the escape.
- A blocking `Condvar.wait` that hands back a guard; `wait_while` is the shape.
- Cross-process semaphores, and a `select` over several waits.
- A spin-lock `Mutex` for freestanding (named in the refusal, not built).

## See also

- [`std/atomic`](/stdlib/atomic)
- [`std/thread`](/stdlib/thread)
- [Concurrency in v1](/language/concurrency)
- [Limits in v1](/language/limits)
