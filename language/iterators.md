---
title: "Iterators, `for` and `break`"
description: "`for x in it` walks any type that implements std/iter's Iterator, `for` over a List or array keeps its index walk, and `break`/`continue` are ordinary loop control. std/iter ships Range and three drain helpers; the adapters are not there yet."
isPublished: true
tags: "language"
---
Source sections:
[`plan/iterators.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/iterators.md)
and [`plan/iterators-status.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/iterators-status.md).

`for` has two meanings, chosen by the type of what it walks:

```kelp
for x in xs { body }     // xs is a List<T> or a [T; N]
for x in it { body }     // it implements std/iter's Iterator
```

A `List<T>` or an array keeps the index walk it always had. Any other type must
implement `Iterator` from [`std/iter`](/stdlib/iter), and the loop calls `next()`
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

It prints, identically on both backends:

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
- A `break` or `continue` frees every owned local declared inside the loop it
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
- Every owned local of every loop an exit leaves is freed, as for a plain `break`.
  The compiler writes a labelled exit as a hidden flag and ordinary `break`s, so
  nothing else about loops changed.

## `std/iter`

[`std/iter`](/stdlib/iter) is pure Kelp and ships the trait, `Range` with
`range` and `range_step`, `count`, `sum_i64` and `collect_list`, the owned list
iterator (`into_iter`, `cloned`) and the adapters `map`, `filter`, `take`, `skip`,
`enumerate`, `zip` and `chain`. They chain, because an adapter is itself an
iterator:

```kelp
impl "std/iter"

var evens = iter.filter(iter.into_iter(xs), fun(x: &i64).return: bool = x % 2 == 0)
for v in iter.map(evens, fun(x: &i64).return: i64 = x * 10) {
    print(v)
}
```

## What is not there yet

- **A borrowing `List.iter()`** that yields `&T`: a borrow into a list cannot outlive the
  iterator that hands it out without a way to say how long it lives. `iter.into_iter`
  moves the list in and yields owned items, and `iter.cloned(&xs)` walks a copy.
- Not a gap, but worth knowing: a generic impl works too,
  `impl<I: iter.Iterator> iter.Iterator for Twice<I> { type Item = I::Item ... }`
  ([Traits](/language/traits)); `std/iter`'s adapters use the simpler by-shape
  rule, under which a generic `datac` whose template declares `fun mut
  Name<P, ...>.next().return: option.Option<Item>` is an `Iterator`.

## See also

- [Control flow](/language/control-flow)
- [Associated types](/language/associated-types)
- [`std/iter`](/stdlib/iter)
- [Limits in v1](/language/limits)
