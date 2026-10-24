---
title: "Closures and iterators"
description: "Function literals that capture a value, scoped blocks that may update a local variable, and writing your own Iterator that for can walk, with the real output of each program."
isPublished: true
tags: "tutorial, language, closures, iterators"
---
**You will learn:** how to write a small function inline, how a function can keep
a value it was made with, and how `for` walks anything that implements `Iterator`.

## The program

```kelp
impl "std/iter"
impl "std/option"

datac Countdown(var n: i32)

impl iter.Iterator for Countdown {
    type Item = i32
    fun mut Self.next() => option.Option<i32> {
        if self.n == 0 {
            return option.Option.None
        }
        val v = self.n
        self.n -= 1
        return option.Option.Some(value = v)
    }
}

fun make_scaler(step: i32) => closure fun(i32) => i32 {
    return fun(x: i32) => i32 = x * step
}

fun sum_with(xs: List<i32>, f: scoped fun(i32) => i32) => i32 {
    var total: i32 = 0
    var i: int = 0
    while i < xs.len() {
        total += f(xs.get(i))
        i += 1
    }
    return total
}

fun main() {
    for c in Countdown(n = 3) {
        print!("${c} ")
    }
    print("liftoff")

    val triple = make_scaler(3)
    print(triple(7))

    var xs: List<i32> = List.empty()
    xs.push(4)
    xs.push(5)
    xs.push(6)
    print(sum_with(xs) { n -> n * 10 })

    var seen = 0
    print(sum_with(xs) { n ->
        seen += 1
        n
    })
    print("seen ${seen}")

    print(iter.sum_i64(iter.range(1, 5)))
}
```

```text
3 2 1 liftoff
21
150
15
seen 3
10
```

## Function literals

`fun(x: i32) => i32 = x * step` is a function written in place. It can be
passed around like any function value, which is why `make_scaler` can return one.

A literal that uses a value from the function around it keeps that value. This is
a closure. `triple` remembers `step = 3` after `make_scaler` has returned, and
`triple(7)` gives 21. The closure type is written `closure fun(i32) => i32`.

## Scoped blocks

`sum_with(xs) { n -> n * 10 }` passes a block to `sum_with`. The block is the
function `f`: the `{ n -> ... }` names its parameter, and the value of the last
line is what it returns. `f` is declared `scoped`, which means the block is used
only during the call. That lets the block change variables around it, as `seen`
does: the block adds one to `seen` on every call, and `seen` is 3 afterwards.

Use an ordinary closure when a function value must outlive the call that made it,
as `triple` does. Use a scoped block when the function is called and finished
inside one call, as the `sum_with` calls are.

## Iterators

`for c in Countdown(n = 3)` works because `Countdown` implements `Iterator`. An
iterator provides a `next()` method that returns `Some` for each value and `None`
when it has finished. `for` calls `next()` until it gets `None`, so the loop
stops on its own.

`iter.range(1, 5)` is a built-in iterator from `std/iter` that produces 1, 2, 3
and 4, and stops before 5. `iter.sum_i64` adds up an iterator's values.

## Try it

1. Change `Countdown` so it stops at 1 rather than 0. What does the loop print?
2. Write `fun make_offset(d: i32) => closure fun(i32) => i32` that adds `d`
   to its argument. Print `make_offset(10)(5)`, then try it again with the closure
   stored in a `val` first. Which form compiles?

Next: [Modules and capabilities](/tutorial/11-projects).
