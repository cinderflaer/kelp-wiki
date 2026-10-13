---
title: "Iterators, `for` and `break`"
description: "for x in it walks any type that implements std/iter's Iterator. A List or array keeps its index walk. Covers break, continue, labels, loop values and the std/iter helpers and adapters."
isPublished: true
tags: "language"
---
Source: [`language/iterators.md`](/language/iterators) and [`language/iterators.md`](/language/iterators).

`for` has two meanings, chosen by the type of what it walks:

```kelp
for x in xs { body }     // xs is a List<T> or a [T; N]
for x in it { body }     // it implements std/iter's Iterator
```

A `List<T>` or an array keeps the index walk it always had. Any other type must
implement `Iterator` from [`std/iter`](#stditer), and the loop calls `next()`
once per pass until it returns `None`. `break` and `continue` are ordinary loop
control in both forms and in a written `while`.

## The `Iterator` trait

```kelp
pub trait Iterator {
    type Item
    fun mut Self.next().return: option.Option<Self::Item>
}
```

`Item` is an [associated type](/language/associated-types), and `next` takes
`mut Self` because an iterator advances through itself. It hands back an
**owned** item, so `x` in `for x in it` is an owned binding the body may move.
The trait is the only thing `for` looks for: a type that merely has a method
called `next` is not iterable.

This program writes one iterator by hand, walks it with `break` and `continue`,
and uses the three helpers `std/iter` ships:

```kelp
impl "std/iter"
impl "std/option"

datac Fib(var a: i64, var b: i64)

impl iter.Iterator for Fib {
    type Item = i64
    fun mut Self.next().return: option.Option<i64> {
        val v = self.a
        self.a = self.b
        self.b = v + self.b
        return option.Option.Some(value = v)
    }
}

fun main() {
    for i in iter.range(0, 5) {
        print!("$i ")
    }
    print("")
    for i in iter.range_step(10, 0, -3) {
        print!("$i ")
    }
    print("")
    // an endless iterator needs break
    for f in Fib(a = 0, b = 1) {
        if f > 50 {
            break
        }
        if f % 2 == 1 {
            continue
        }
        print!("$f ")
    }
    print("")
    val xs = [1, 2, 3, 4, 5, 6]
    var total = 0
    for x in xs {
        if x == 2 {
            continue
        }
        if x == 5 {
            break
        }
        total += x
    }
    print(total)
    print(iter.count(iter.range(0, 10)))
    print(iter.sum_i64(iter.range(1, 5)))
    val l = iter.collect_list(iter.range(3, 6))
    print(l.len())
    print(l.get(2))
}
```

It prints:

```
0 1 2 3 4 
10 7 4 1 
0 2 8 34 
8
10
10
3
5
```

Reading it line by line:

- `iter.range(0, 5)` and `iter.range_step(10, 0, -3)` are `std/iter`'s own
  iterators. A range is half-open, and a negative step walks down.
- `Fib` never returns `None`, so the loop needs `break`. `continue` skips the
  odd values, which is why only `0 2 8 34` print.
- The `List` walk (`for x in xs` over `[1, 2, 3, 4, 5, 6]`) skips 2 with
  `continue` and stops at 5, so the total is `1 + 3 + 4`.
- `count`, `sum_i64` and `collect_list` drain an iterator.

## What `for` does with each type

- **A `List<T>` or `[T; N]`.** Unchanged in behaviour and speed: an index bound
  at zero, `x` is what `List.get` gives (a copy for a `Copy` element, a shared
  borrow for an owned one), and the body may not mutate the place being walked
  ([Control flow](/language/control-flow#for)). The index advances before the
  body runs, which only `continue` can observe.
- **Anything that implements `Iterator`.** The loop holds the iterator and calls
  `next()`. A place (`for x in it` where `it` is a `var`) is **borrowed
  exclusively for the loop**, so using it inside the body is the ordinary
  borrow error, and a temporary (`for x in iter.range(0, 3)`) is owned by the
  loop and cannot be named at all:

  ```
  error: cannot borrow 'f': already borrowed exclusively
  ```

  An iterator that is a function parameter has to be bound to a `var` first,
  because a parameter is an immutable binding.
- **Anything else** is refused, and the message names the trait:

  ```
  error: 'for' walks a 'List<T>' or a type that implements 'Iterator', and 'i32' is neither: implement 'std.iter.Iterator' for it ('type Item' and 'fun mut Self.next().return: option.Option<Self::Item>'), or walk a 'List' by index
  ```

  A `Map` is walked with a pattern instead: see below.

- **`for (key, value) in map`** walks a `Map<K, V>` (26.10.3). The pattern is two
  names, or `_` for one you do not need, and the map must be a named place. It is
  the same as `for key in map.keys() { val value = map.get(key) ... }`, so the keys
  are a snapshot in insertion order: the body may change the map, and a key it
  removes makes the later lookup panic like any `get` of an absent key. `key` is a
  copy for a `Copy` key and a shared borrow otherwise, and `value` is what `get`
  gives (a copy, or a borrow).

The iterable is evaluated once, so `for x in make()` calls `make` a single time.

## `break` and `continue`

`break` leaves the innermost loop and `continue` goes on to the next pass. They
are statements, not keywords: a bare `break` or `continue` in statement position
is the statement, and a name used in an expression is still a name.

```kelp
fun main() {
    var i = 0
    while i < 100 {
        i += 1
        if i % 2 == 0 {
            continue
        }
        if i > 7 {
            break
        }
        defer print("done $i")
        var j = 0
        while j < 10 {
            j += 1
            if j == 2 {
                break
            }
        }
        print(j)
    }
    print(i)
}
```

```
2
done 1
2
done 3
2
done 5
2
done 7
9
```

- `continue` in a `while` re-tests the condition, so the increment has to be part
  of the loop's own logic. Here `i += 1` comes first.
- `break` in the inner loop leaves only the inner loop.
- A `defer` in the body runs on the way out of a `break` or `continue` as it does
  on any exit from its block, which is why `done 1`, `done 3`, `done 5` and
  `done 7` print once per odd pass. The passes that `continue` before reaching
  the `defer` print nothing.
- A `break` or `continue` drops every owned local declared inside the loop it
  leaves, and only those.
- Outside every loop they are refused, naming the statement:

  ```
  error: 'break' is a loop control statement, and no loop encloses it: write it inside a 'while' or a 'for'
  ```

- A deferred action cannot contain one:

  ```
  error: a deferred action cannot contain 'break' or 'continue': the action runs while the block is being left, so it cannot leave the loop again
  ```

- **`loop` can be a value** (26.10.3): `break value` leaves the loop and is what the
  `loop` evaluates to.

  ```kelp
  var n = 0
  val doubled = loop {
      n += 1
      if n == 4 {
          break n * 2
      }
  }                          // 8
  ```

  Every `break` out of such a loop carries a value and at least one does (the
  compiler refuses a plain `break`, and a value loop with none); the values have
  one type, decided by the first, and an integer literal there takes the default
  `i32` as it would anywhere without a written type, so bind a `val v: i64 = 5`
  first when the loop should produce a different width. A label works:
  `val x = 'outer: loop { ... break 'outer value ... }`. The value starts with a
  name, a literal (a leading `-` included), a template or a `[`; wrap anything else
  in a `val` first. Only a `loop` can produce a value: `while` and `for` cannot
  `break` with one. `return` and `?` inside the loop still leave the function.

### `loop` and labels

`loop { ... }` is an endless loop, the same as `while true { ... }`; the body ends
with `break` or `return`. A label is written before a loop, as `'name:`, and
`break 'name` or `continue 'name` acts on that loop from inside a loop nested in it:

```kelp
'rows: for y in [1, 2, 3] {
    for x in [1, 2, 3] {
        if x == y {
            continue 'rows      // the next y
        }
        if y == 3 {
            break 'rows         // leave both loops
        }
    }
}
```

- A label is a `'` and a name (`'outer`); the closing `'` of a character literal
  is what tells the two apart. It may label a `while`, a `for` or a `loop`.
- A label that names no enclosing loop is an error. A label does not cross a
  function, a `fun` literal or a block passed to a call.
- `loop` is read as the keyword only at the start of a statement and only when a
  `{` follows, so a function called `loop` is still a name everywhere else.
- Every owned local of every loop an exit leaves is dropped, as for a plain `break`.
  The compiler writes a labelled exit as a hidden flag and ordinary `break`s, so
  nothing else about loops changed.

## std/iter

The `Iterator` trait that `for x in it` walks, the half-open `Range`, and three
helpers that drain an iterator. Ungated.

```kelp
impl "std/iter"
```

The module is pure Kelp, builds in a freestanding image where `std/option` does
(only `collect_list` waits for an allocator), and is why a `for` over a range
costs no libc: `Range.next` is an ordinary method and the loop is an ordinary
`while` by the time either backend sees it. 
### Surface

```kelp
pub trait Iterator {
    type Item
    fun mut Self.next().return: option.Option<Self::Item>
}

pub datac Range(var lo: i64, val hi: i64, val step: i64)
pub fun range(a: i64, b: i64).return: Range
pub fun range_step(a: i64, b: i64, step: i64).return: Range

pub fun count<I: Iterator>(it: move I).return: usize
pub fun sum_i64<I: Iterator>(it: move I).return: i64
pub fun collect_list<I: Iterator>(it: move I).return: List<I::Item>
```

| Item | Notes |
| --- | --- |
| `Iterator` | `next` hands back one **owned** item; `None` ends the loop. A type opts in with `impl iter.Iterator for T` and binds `type Item` |
| `Range` | `[lo, hi)` stepping by `step`; a negative step walks down and stops at `hi` from above. It owns nothing, so it needs no allocator |
| `range(a, b)` | step 1; an empty range yields nothing |
| `range_step(a, b, step)` | explicit step. A step of `0` is not rejected: it is treated as a descending step, so `range_step(0, 5, 0)` is empty and `range_step(5, 0, 0)` never advances |
| `count(it)` | how many items remain, by draining |
| `sum_i64(it)` | the sum; the item type must be `i64`, and any other item type is a type error at the addition |
| `collect_list(it)` | drains into a `List<I::Item>`, in order |

Each helper takes the iterator by `move`.

### Example

```kelp
impl "std/iter"

fun main() {
    for i in iter.range(0, 5) {
        print!("$i ")
    }
    print("")
    for i in iter.range_step(10, 0, -3) {
        print!("$i ")
    }
    print("")
    print(iter.count(iter.range(0, 10)))
    print(iter.sum_i64(iter.range(1, 5)))
    val l = iter.collect_list(iter.range(3, 6))
    print(l.get(2))
}
```

Output:

```
0 1 2 3 4 
10 7 4 1 
10
10
5
```

### The list iterator and the adapters

```kelp
iter.into_iter(xs: move List<T>) -> ListIter<T>      // owned items, front to back
iter.cloned(xs: &List<T>) -> ListIter<T>             // a copy of a borrowed list
iter.map(it, f)        -> MapIter<..>     // f: closure(&Item) -> U
iter.filter(it, pred)  -> FilterIter<..>  // pred: closure(&Item) -> bool
iter.take(it, n)       -> TakeIter<..>    // at most the first n
iter.skip(it, n)       -> SkipIter<..>    // the items after the first n
iter.enumerate(it)     -> EnumerateIter<..>   // (usize, Item), from 0
iter.zip(a, b)         -> ZipIter<..>     // (A::Item, B::Item), stops at the shorter
iter.chain(a, b)       -> ChainIter<..>   // all of a, then all of b (same item type)
```

Each takes its iterator by `move` and is itself an `Iterator`, so they nest
(`iter.take(iter.filter(iter.into_iter(xs), keep), 3)`). A `for` over an adapter
needs it in a `var` (or a temporary), as for any iterator that advances. The
adapters are generic `datac`s with a `next` method; a generic type with such a
`next` is an iterator by shape, which is why none of them needs a generic trait
impl (see [What is not there yet](#what-is-not-there-yet)).

### The consumers

```kelp
iter.any(it, pred) -> bool                 // some item satisfies pred
iter.all(it, pred) -> bool                 // every item does
iter.find(it, pred) -> Option<Item>        // the first that does
iter.last(it) -> Option<Item>
iter.fold(it, init, f) -> A                // f(&acc, &item) is the next accumulator
```

Each takes its iterator by `move` and stops as soon as the answer is known
(`any`, `all`, `find`). With `count`, `sum_i64` and `collect_list` these are the
whole set of consumers.

## What is not there yet

- **A borrowing `List.iter()`** that yields `&T`: a borrow into a list cannot outlive the
  iterator that hands it out without a way to say how long it lives. `iter.into_iter`
  moves the list in and yields owned items, and `iter.cloned(&xs)` walks a copy.

## See also

- [Control flow](/language/control-flow)
- [Associated types](/language/associated-types)
- [Limits in v1](/language/limits)
