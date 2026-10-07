---
title: "Tutorial 10: Closures and scoped blocks"
description: "Chapter 10 of the Kelp tutorial: fun literals and closures that own their captures, scoped parameters and trailing blocks that may borrow and write local variables, and the real errors for the cases the compiler refuses."
isPublished: true
tags: "tutorial, language, closures"
---
Kelp has two kinds of anonymous function. A **closure** owns what it captures and can
be stored and returned. A **scoped block** is a `{ ... }` written after a call; it may
borrow locals, even write them, because the callee can only call it during the call.
The reference is [Functions](/language/functions#closures).

## The program

```kelp
impl "std/list"

// returns a closure that owns its captured `step`
fun make_adder(step: i32).return: closure(i32).return: i32 {
    return fun(x: i32).return: i32 = x + step
}

fun apply_twice(f: closure(i32).return: i32, x: i32).return: i32 = f(f(x))

// a scoped parameter: only a literal or trailing block can be passed
fun each_to(n: i32, f: scoped fun(i32)) {
    var i = 1
    while i <= n {
        f(i)
        i += 1
    }
}

fun main() {
    val add5 = make_adder(5)
    print("add5(10) = ${add5(10)}")
    print("twice = ${apply_twice(add5, 1)}")

    val xs: List<i32> = List.of(3)
    val tripled = list.map(xs, fun(x: &i32).return: i32 = x * 3)
    print("tripled ${tripled.get(0)}")

    // a trailing block borrows what it captures, and may write it
    var total = 0
    var calls = 0
    each_to(4) { n ->
        total += n
        calls += 1
    }
    print("total ${total} over ${calls} calls")

    var seen: List<i32> = List.empty()
    each_to(3) { n -> seen.push(n * n) }
    print("squares ${seen.len()} first ${seen.get(0)} last ${seen.get(2)}")
}
```

```text
add5(10) = 15
twice = 11
tripled 9
total 10 over 4 calls
squares 3 first 1 last 9
```

Both backends agreed on every line.

## Closures

A `fun` literal is `fun(x: i32).return: i32 = x + step`. When it names a binding from
the enclosing scope, that is a **capture**, and the literal's type is written
`closure(i32).return: i32` (compare the plain function type `fun(i32).return: i32` from
chapter 2).

Captures are **move-only**: a `Copy` binding (the `i32` `step`) is copied into the
closure's environment, and an owned binding such as a `String` is moved in and gone
from the enclosing scope. The closure owns its environment and frees it where it dies.
That is why `make_adder` can return a closure whose `step` outlives the call.

A **borrow cannot be captured**, because the environment would outlive the frame the
borrow points into, and Kelp has no lifetime syntax to say otherwise:

```kelp
impl "std/str"

fun make(name: &str).return: closure().return: usize {
    return fun().return: usize = str.len(name)
}

fun main() {
    val f = make("kelp")
    print(f())
}
```

```text
$ kelpc check c10bad2.kp
error: a 'fun' literal cannot capture 'name': it is a borrow ('str'), and the environment it would be stored in outlives the frame the borrow points into — capture an owned value, or pass it as a parameter of the literal
  --> c10bad2.kp:4:12
```

Pass the value as a parameter of the literal, or capture an owned copy. Library
callbacks are typically `closure(&T).return: U`, as in `list.map(xs, fun(x: &i32).return: i32 = x * 3)`
above, where the `Copy` element is used directly.

## Scoped parameters and trailing blocks

A parameter written `f: scoped fun(i32)` accepts only a `fun` literal or a **trailing
block** at the call site, never a stored value. A block after the call is the call's
last argument, and it names its parameters by name only; their types come from the
callee: `each_to(4) { n -> ... }`. A block whose last line is an expression returns
it when the callee expects a value.

Because the callee cannot keep the block, the block may capture an enclosing binding
**by borrow**. And it may capture **exclusively**: a block captures a binding
exclusively exactly when its body needs to write it (`total += n`, `seen.push(...)`,
or passing it to a `mut` parameter). No annotation is needed. The program's first
block updated two local counters and the second pushed onto a list, and the results
were visible after the call.

The enclosing binding must be an owned `var` or a `mut` parameter, which the block
reborrows for the call only:

```kelp
fun each_to(n: i32, f: scoped fun(i32)) {
    f(n)
}

fun main() {
    val frozen = 0
    each_to(3) { n -> frozen = n }
    print(frozen)
}
```

```text
$ kelpc check c10bad1.kp
error: cannot write to captured 'frozen': it is not declared 'var' in the enclosing function; declare it 'var' so a scoped block can write it
  --> c10bad1.kp:7:23
```

And while a block holds an exclusive capture, nothing else in the same call may touch
that owner:

```kelp
datac State(var count: i32)

fun two(s: mut State, f: scoped fun(i32)) {
    f(1)
}

fun main() {
    var s = State(count = 0)
    two(s) { n -> s.count += n }
    print(s.count)
}
```

```text
$ kelpc check c10bad3.kp
error: cannot borrow 's': already borrowed exclusively
  --> c10bad3.kp:9:12
```

This is the same mechanism [`Mutex.lock`](/stdlib/sync) uses in chapter 13: a block
that can update a local accumulator while the lock is held.

## Exercises

1. Write `repeat(times: i32, f: scoped fun(i32))` that calls `f(i)` for `i` from 0 up
   to `times`, and use it to build the text `ababab` in a `String` declared outside
   the call.
2. Write `make_counter_step(step: i32)` returning a closure, make two of them, and
   print results of calling each, including one composed with the other.

<details>
<summary>Solutions</summary>

1.

```kelp
fun repeat(times: i32, f: scoped fun(i32)) {
    var i = 0
    while i < times {
        f(i)
        i += 1
    }
}

fun main() {
    var line = String.empty()
    repeat(3) { i ->
        line.push_str("ab")
    }
    print(line)
}
```

```text
ababab
```

2.

```kelp
fun make_counter_step(step: i32).return: closure(i32).return: i32 {
    return fun(x: i32).return: i32 = x + step
}

fun main() {
    val by2 = make_counter_step(2)
    val by10 = make_counter_step(10)
    print("${by2(1)} ${by10(1)} ${by2(by10(0))}")
}
```

```text
3 11 12
```

</details>

Next: [Projects and modules](/tutorial/11-projects).
