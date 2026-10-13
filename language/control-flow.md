---
title: "Control flow"
description: "How Kelp branches and loops: if, elif, if let, while, for, when with patterns and tuple patterns, and return, including the rules that refuse some loops."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §6](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

Kelp has `if`/`else` (with `if let`), `for`, `while`, `when` and `return`. Inside
a loop, `break` leaves it and `continue` starts its next pass. `loop { ... }` is
an endless loop, and `break value` leaves a `loop` with a value. A loop can carry
a label, so `break 'outer` and `continue 'outer` act on that loop. There is no
`goto` and no exceptions. See also [Iterators, `for` and `break`](/language/iterators).

## `if` / `else`

```kelp
if n > 0 {
    print("positive")
} elif n < 0 {
    print("negative")
} else {
    print("zero")
}
```

An `if` used as a value must have an `else`, and both arms must produce the same
type:

```kelp
val label: String = if n > 0 { "pos" } else { "not pos" }
```

### `elif` and `else if`

The link between one condition and the next has two spellings, and they mean the
same thing:

```kelp
if n > 2 {
    print("big")
} elif n > 1 {
    print("medium")
} elif n > 0 {
    print("small")
} else {
    print("none")
}
```

- **`elif` is the preferred spelling.** `else if` is the same link, stays legal
  and compiles identically, and `kelpc fmt` never rewrites one into the other;
  `kelpc lint` warns about `else if` and says which spelling to write.
- A chain may mix the two, and `elif` takes the same grammar as `if`: a
  condition and a block, or a pattern and a block (`elif let`).

## `if let`

`if let` is the same conditional with a **pattern** instead of a boolean
condition: the branch runs when the variant matches, and it binds the payload for
that branch.

```kelp
if let Ok(v) = parsed {
    print(v + 1)
}

if let Word(text) = token {
    print(str.len(text.as_str()))
}

if let Rect(w, h) = shape {
    print(w * h)
} elif let Circle(r) = shape {
    print(3.14159 * r * r)
} else {
    print(0.0)
}
```

- It is exactly the pattern form of `when` with one arm and an `else`, so the arm
  rules are the same: the variant must exist, the binding count must match the
  payload, and `_` ignores one.
- The scrutinee may be **any expression**, temporary or place. A *place* is
  matched directly, and only the projection an arm reads out by value is gone
  from it; a *temporary* is bound to a hidden local first, which is how `if let
  Ok(v) = json.parse(text)` is legal at all, and that hidden local is an owned
  place like any other. A field chain over a temporary stages its **root**:
  `if let Word(w) = mk().t` binds `mk()` and matches its `t`, so the whole `mk()`
  result is dropped when the block ends rather than the field being read out of a
  value that has no storage of its own.
- A payload binds as a **copy** when it is `Copy`, **by value** when it is owned
  and the scrutinee is an owned place (a `val`/`var` binding or a `move T`
  parameter), and as a **shared borrow** otherwise. So `if let Ok(x) = parsed`
  where `parsed` is an owned `Result<Civil, _>` gives you a `Civil` and takes it
  out of `parsed`, while a `parsed: &Result<Civil, _>` gives you a `&Civil`: pass
  `x`, not `&x`.

## `while`

```kelp
var i: usize = 0
while i < xs.len() {
    print(xs.get(i))
    i += 1
}
```

`while` is the general loop: a condition, re-evaluated before each pass. The body
may be empty (`while !file.is_open() { }`), which is how a spin-wait is written.

## `for`

`for` walks a `List<T>` or a `[T; N]` front to back, and any type that implements
`std/iter`'s `Iterator` with a `next()` loop
([Iterators, `for` and `break`](/language/iterators)). The rest of this section
is the list and array walk:

```kelp
for x in xs {
    print!("$x ")
}
```

- The iterable must be a `List<T>`, a `[T; N]`
  ([Collections](/language/collections)) or a type that implements `Iterator`;
  anything else is refused with a message that names the trait. A `List` or array
  is walked as an index-and-`while` loop, where the index advances before the
  body runs so that `continue` reaches the next element. A type with an
  `Iterator` impl is walked by calling `next()` until `None`.
- **A destructuring binding takes an element apart**: `for (k, v) in pairs` walks a
  `List<(K, V)>` and binds both positions, `_` ignores one, and a nested pattern
  takes a nested tuple. It reads as `for e in pairs { val (k, v) = e ... }`,
  so the element is moved into the pattern exactly as a destructuring `val`
  moves it. The pattern needs an element that is a tuple.
- The element binding gives exactly what `List.get` gives: a copy of a `Copy`
  element, a shared borrow of an owned one. `for n in numbers` reads `n: i32`;
  `for name in names` reads `name: &String`, so a `str` call wants
  `name.as_str()`. An array's `get` gives the same thing, and its `len` is the
  type's own length.
- The body may **read** the place it walks (`xs.get(i)`, `xs.len()`, `&xs`), and
  may walk or change a **different** list, but it may not mutate the one it
  walks. A `mut` receiver method on it (`push`, `pop`, `remove`, `insert`,
  `set`, `clear`, `sort`, `reverse`), an assignment to it, a move of it, taking
  `&mut xs`, and passing it to a `mut` parameter are all one compile error,
  reported on the `for` line:

  ```
  error: cannot mutate 'xs' while iterating over it
  ```

  A `fun` literal written in the body cannot capture it either: a capture moves
  or copies, and the move is refused the same way. The rule names the place, so
  `for x in self.items { self.other.push(x) }` is legal while
  `for x in self.items { self.items.push(x) }` reports
  `cannot mutate 'self.items' while iterating over it`.
- When the loop has to change what it walks, walk it by index with `while`
  instead: that is the supported pattern, and no such rule applies to it.
- Anything else (a call, a literal, or a field of one) is bound to a temporary
  the loop owns and frees, and is evaluated **once**. A field chain over a
  temporary stages its *root*: `for x in mk().items` binds `mk()` once and walks
  its `items`, so the call does not run again for the condition and for every
  element.
- The loop variable is a `val`; copy it into a `var` to mutate it.

## `when`

`when` is a chain of conditions that reads as a value:

```kelp
fun classify(n: i32) => &str = when {
    n > 0 -> "pos"
    n < 0 -> "neg"
    else -> "zero"
}
```

Each arm is `condition -> value`. Arms are evaluated in order, `else` is required
when a value is produced, and `when` desugars to nested `if`/`else if`/`else`.
`->` appears nowhere else in the language.

With a **scrutinee**, `when` becomes pattern matching over an `enum`:

```kelp
fun area(s: &Shape) => f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}
```

- The scrutinee is matched where it is when it is a **place** (a name, a
  `.field` chain, `*expr`): nothing moves out of it as a whole, and only the
  matched payload is copied, borrowed, or (an owned payload of an owned place)
  moved out. A **temporary** (a call's result, a literal) is bound to a hidden
  local first, because a payload borrow has to outlive the arm it is bound in;
  the local is dropped once the match ends, and it is an owned place like any
  other. A chain over a temporary stages its **root**: `when mk().t { ... }`
  binds `mk()` and matches its `t`, so the whole temporary is dropped exactly once,
  never the field alone.
- Matching must be exhaustive: either every variant has an arm, or an `else ->`
  arm is present.
- There are no guards in v1. Outside a tuple pattern, an arm head is a variant
  name with one binding per payload field, and `_` ignores a payload. Literal and
  nested patterns are only available inside a **tuple pattern**, below.
- A payload binds as a copy when `Copy`, **by value** when it is owned and the
  scrutinee is an owned place, and as a shared borrow otherwise.

### A tuple pattern

Several values can be matched together by writing them as a tuple and each arm as
a tuple pattern:

```kelp
impl "std/option"

fun combine(a: &option.Option<i32>, b: &option.Option<i32>) => i32 = when (a, b) {
    (Some(x), Some(y)) -> x + y
    (Some(x), None) -> x
    (None, y) -> 0
}
```

- A position is a variant pattern (`Some(x)`, `None`; a capitalized name), a
  **literal** (`0`, `-1`, `'a'`, `true`), a **nested tuple pattern**
  (`((a, b), c)`), a lowercase name that matches anything and binds it, or `_`.
  All arms have the same number of positions, at least two. `else` may stand for
  the rest.
- A scrutinee written as a tuple literal is **not built**: its elements are the
  positions, so a parameter or a field is matched where it lives and a borrowed
  element (`&option.Option<i32>`) is fine. Any other tuple value is bound once and its
  positions are matched.
- Arms are tried in order, the first position that an arm names a variant for is
  matched first, and each level is an ordinary single-position `when`, so the
  usual rules hold at every level: a variant with no arm (and no arm that matches
  anything there) is the "not exhaustive" error naming the variant.
- A position tested against literals is compared with `==`, so a number has no
  list of values to be exhaustive over: some arm must match anything in that
  position (a name, `_`, or `else`), or the pattern is refused. A string literal
  is not a position pattern, and a guard is not supported. The value read by a
  matching name moves out of an owned position exactly as a payload does.

```kelp
fun classify(a: i32, b: i32) => i32 = when (a, b) {
    (0, 0) -> 100
    (0, y) -> y
    (x, 0) -> x * 10
    (x, y) -> x + y
}
```

## `return`

```kelp
fun sum_to(n: i32) => i32 {
    var acc = 0
    var i = 1
    while i <= n {
        acc += i
        i += 1
    }
    return acc
}
```

`return` with no value is allowed in a function with no `=> T`. An
expression-bodied function does not use `return` at all.

A block whose **last statement is `panic(...)`** diverges, so it satisfies any
declared return type, including a borrowed one. That rule is what makes a
"this cannot happen" accessor expressible:

```kelp
impl "std/option"

fun unwrap<T>(o: &option.Option<T>) => T {
    if let Some(v) = o {
        return v
    }
    panic("Option.unwrap: value is None")
}
```

It applies to a function body's tail and nowhere else: a `panic` cannot be the
arm of an `if`/`when` used as a value.

## See also

- [Iterators, `for` and `break`](/language/iterators)
- [Functions](/language/functions)
- [Return types and `return`](/language/returns)
- [Errors and panics](/language/errors)
- [Ownership and borrowing](/language/ownership)
