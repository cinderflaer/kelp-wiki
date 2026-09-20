---
title: "Control flow"
description: "Source section - syntax.md \u00a76."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §6](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Kelp has `if`/`else` (with `if let`), `for`, `while`, `when` and `return`. There
is no `break`, no `continue`, no `loop`, no `goto` and no exceptions: a
condition that must end a loop early goes in the `while` header.

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
  matched directly with nothing moved; a *temporary* is bound to a hidden local
  first, which is how `if let Ok(v) = json.parse(text)` is legal at all.
- The one expression that is not a scrutinee is a **field of a temporary**.
  `if let Word(w) = mk().t` names the owned field it would have to read out of a
  value that has no storage of its own, and `when` refuses a temporary outright
  (`when mk()` itself is "the scrutinee of a pattern 'when' must be a place").
  Bind the call first: `val h = mk()`, then match `h.t`.
- A payload binds as a **copy** when it is `Copy` and as a **shared borrow**
  otherwise. So in `if let Ok(x) = parsed` where `parsed: Result<Civil, _>`, `x`
  is already a `&Civil`: pass `x`, not `&x`.

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

`for` walks a `List<T>` front to back:

```kelp
for x in xs {
    print!("$x ")
}
```

- The iterable must be a `List<T>`. `for` is **desugared by the parser** into the
  index-and-`while` walk, so no later pass knows it exists and there is no
  iterator protocol to implement.
- The element binding gives exactly what `List.get` gives: a copy of a `Copy`
  element, a shared borrow of an owned one. `for n in numbers` reads `n: i32`;
  `for name in names` reads `name: &String`, so a `str` call wants
  `name.as_str()`.
- The iterable is *borrowed* when it is a place, so the body cannot `push` to
  what it walks.
- Anything else (a call, a literal) is bound to a temporary the loop owns and
  frees, and is evaluated **once**.
- The loop variable is a `val`; copy it into a `var` to mutate it.

## `when`

`when` is a chain of conditions that reads as a value:

```kelp
fun classify(n: i32).R: &str = when {
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
fun area(s: &Shape).R: f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}
```

- The scrutinee must be a **place** (a name, a `.field` chain, `*expr`), never a
  temporary: a payload borrow has to outlive the arm it is bound in. Use `if let`
  when you have an expression.
- Matching must be exhaustive: either every variant has an arm, or an `else ->`
  arm is present.
- There are no guards, no literal patterns and no nested patterns in v1. An arm
  head is a variant name with one binding per payload field, and `_` ignores a
  payload.
- A payload binds as a copy when `Copy` and as a shared borrow otherwise, so
  matching never partially moves the scrutinee.

## `return`

```kelp
fun sum_to(n: i32).R: i32 {
    var acc = 0
    var i = 1
    while i <= n {
        acc += i
        i += 1
    }
    return acc
}
```

`return` with no value is allowed in a function with no `.R: T`. An
expression-bodied function does not use `return` at all.

A block whose **last statement is `panic(...)`** diverges, so it satisfies any
declared return type, including a borrowed one. That rule is what makes a
"this cannot happen" accessor expressible:

```kelp
fun unwrap<T>(o: &Option<T>).R: T {
    if let Some(v) = o {
        return v
    }
    panic("Option.unwrap: value is None")
}
```

It applies to a function body's tail and nowhere else: a `panic` cannot be the
arm of an `if`/`when` used as a value.

## See also

- [Functions](/language/functions)
- [Return types and `return`](/language/returns)
- [Errors and panics](/language/errors)
- [Ownership and borrowing](/language/ownership)
