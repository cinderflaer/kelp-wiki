---
title: "Tutorial 13: Concurrency"
description: "Chapter 13 of the Kelp tutorial: thread.spawn and join, shared state through a pd Mutex and RwLock, channels between threads, a thread pool, and the compile error that stops a borrow of a local crossing to a worker."
isPublished: true
tags: "tutorial, concurrency, threads"
---
Kelp has real threads, and a data race does not compile. The rule is simple: a thread
can take an **owned value, moved in**, or one shared borrow of a `pd` global that
has no way to be written without a lock or an atomic. The reference is
[Concurrency in v1](/language/concurrency), [`std/thread`](/stdlib/thread),
[`std/sync`](/stdlib/sync) and [`std/pool`](/stdlib/pool). All of it is hosted only.

## Threads, locks

```kelp
impl "std/thread"
impl "std/result"
impl "std/sync"

pd val hits: Mutex<i64> = Mutex.new(0)

// a worker takes ONE argument (moved in) and returns a value
fun sum_to(n: i64).return: i64 {
    var total: i64 = 0
    var i: i64 = 1
    while i <= n {
        total += i
        i += 1
    }
    return total
}

// a shared borrow of a `pd` Mutex may cross to a worker
fun bump(m: &Mutex<i64>).return: i64 {
    var i = 0
    while i < 100 {
        m.lock { v -> *v += 1 }
        i += 1
    }
    return 0
}

fun main() {
    val h = thread.spawn(sum_to, 100)
    when thread.join(h) {
        Ok(v) -> print("worker returned ${v}")
        Err(e) -> print("worker failed: ${e.message}")
    }

    val a = thread.spawn(bump, &hits)
    val b = thread.spawn(bump, &hits)
    val ra = thread.join(a)
    val rb = thread.join(b)
    print("both joined: ${result.is_ok(ra)} ${result.is_ok(rb)}")
    print("hits ${hits.lock { v -> *v }}")

    val config: RwLock<i64> = RwLock.new(10)
    config.write { v -> *v += 5 }
    print("config ${config.read { v -> *v }}")
}
```

```text
worker returned 5050
both joined: true true
hits 200
config 15
```

Both backends agree.

- **`thread.spawn(entry, arg)`** starts a worker. `entry` is a function taking
  exactly **one** parameter; `arg` is moved into it, and the thread's result type is
  the entry's return type. It returns a `Thread<T>`.
- **`thread.join(handle)`** waits, consumes the handle, and returns
  `Result<T, ThreadErr>`. A panic in a worker ends only that worker, and the joiner sees
  it as `Err` with the panic text. That `Result` is an owned value you must use: the
  compiler refuses to let it be dropped silently, which is why the program binds the
  two joins to `ra` and `rb`.
- **`Mutex<T>`** guards one owned value, reached only through a scoped block:
  `m.lock { v -> *v += 1 }` (the exclusive-capture mechanics of chapter 10). The
  block's last expression is the call's value, so `hits.lock { v -> *v }` reads it. The
  lock is released on every exit; a panic inside poisons the mutex.
- **`RwLock<T>`** has `read` (many readers, a shared `&T`) and `write` (one writer,
  `mut T`), plus `try_read` and `try_write` returning an `Option`.
- A `&Mutex<T>` of a `pd val` crosses to a worker, which is how two workers each did a
  hundred increments of `hits` and the total was exactly 200.

What does not cross is a borrow of a local:

```kelp
impl "std/thread"
impl "std/result"

fun show(n: &i64).return: i64 = n

fun main() {
    var local: i64 = 5
    val t = thread.spawn(show, &local)
    val r = thread.join(t)
    print("done")
}
```

```text
$ kelpc check c13bad1.kp
error: 'thread.spawn' cannot send '&i64': a shared borrow may cross to a worker only when the place it borrows has process lifetime, which in v1 means a 'pd' global, and this one borrows a frame local that ends before the worker does; share a 'pd' value instead, or move an owned value in
  --> c13bad1.kp:8:32
```

The message gives both fixes: share a `pd` value, or move an owned value in.

## Channels

A channel moves owned values between threads instead of sharing a location.

```kelp
impl "std/thread"
impl "std/result"
impl "std/sync"

// thread.spawn takes ONE argument, so the sender travels inside a datac
datac Job(val tx: sync.Sender<i64>, val count: i64)

fun produce(job: move Job) {
    val tx = job.tx
    val n = job.count
    var i: i64 = 1
    while i <= n {
        val back = tx.send(i * i)
        i += 1
    }
}

fun main() {
    var (tx, rx) = sync.bounded<i64>(2)
    val worker = thread.spawn(produce, Job(tx = tx, count = 5))

    var total: i64 = 0
    for v in rx {
        print("got ${v}")
        total += v
    }
    val joined = thread.join(worker)
    print("total ${total}, joined ok: ${result.is_ok(joined)}")
}
```

```text
got 1
got 4
got 9
got 16
got 25
total 55, joined ok: true
```

`sync.bounded<i64>(2)` returns a `(Sender, Receiver)` pair, taken apart by
destructuring. `send` waits while the queue holds two values. Because `spawn` takes
**one** argument, the sender travels inside a `datac`, `Job`. `for v in rx` ends by
itself: `main`'s only sender was moved into the job, so the channel closes when
the worker returns and drops it. `unbounded` never makes `send` wait; `rx.recv()` gives a
`Result` with `Err(Closed)`, `try_recv` and `recv_timeout` do not block (or block with
a limit). `tx.clone()` makes another sender for more producers.

## A thread pool

`std/pool` runs closures from one queue on a fixed number of workers:

```kelp
impl "std/pool"
impl "std/sync"
impl "std/atomic"

pd val total: AtomicI64 = AtomicI64.new(0)

fun add(n: i64) {
    total.fetch_add(value = n, order = atomic.Ordering.SeqCst)
}

fun main() {
    var p = pool.new(3)
    var i: i64 = 1
    while i <= 10 {
        val k = i
        p.spawn(fun() { add(k) })
        i += 1
    }
    p.join()
    print("sum ${total.load(order = atomic.Ordering.SeqCst)}, panics ${p.panicked()}")
}
```

```text
sum 55, panics 0
```

`p.spawn(closure)` queues a job, `p.join()` runs what is queued and waits for the
workers to exit, and `p.panicked()` counts jobs that panicked without killing their
worker. A `Pool` joins in its drop, so leaving its scope also waits for the jobs. The
total is read through an atomic, `AtomicI64`, in a `pd`, with `Ordering.SeqCst`, the one
ordering Kelp has.

## Exercises

1. Spawn two threads that each square a number, join both with `when`, and print the
   sum of the squares.
2. Using the pool, make four jobs each push `k * 10` onto a `pd val` `Mutex<List<i64>>`,
   then print how many entries there are and their sum. (A `fun` literal cannot read a
   `pd` directly, as the compiler tells you; call a named function that does.)

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/thread"
impl "std/result"

fun square(n: i64).return: i64 = n * n

fun main() {
    val a = thread.spawn(square, 7)
    val b = thread.spawn(square, 8)
    var sum: i64 = 0
    when thread.join(a) {
        Ok(v) -> sum += v
        Err(e) -> print(e.message)
    }
    when thread.join(b) {
        Ok(v) -> sum += v
        Err(e) -> print(e.message)
    }
    print("sum of squares ${sum}")
}
```

```text
sum of squares 113
```

2.

```kelp
impl "std/pool"
impl "std/sync"

pd val log: Mutex<List<i64>> = Mutex.new(List.empty())

fun record(k: i64) {
    log.lock { v -> v.push(k * 10) }
}

fun main() {
    var p = pool.new(2)
    var i: i64 = 1
    while i <= 4 {
        val k = i
        p.spawn(fun() { record(k) })
        i += 1
    }
    p.join()
    val n = log.lock { v -> v.len() }
    val total = log.lock { v ->
        var t: i64 = 0
        for x in v {
            t += x
        }
        t
    }
    print("${n} entries, sum ${total}")
}
```

```text
4 entries, sum 100
```

</details>

Next: [Networking](/tutorial/14-networking).
