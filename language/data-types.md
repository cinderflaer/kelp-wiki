---
title: "`datac` and `enum`"
description: "Source section - syntax.md \u00a79."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §9](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Kelp has two ways to declare a type: a **record** (`datac`), where every field
exists in every value, and a **tagged union** (`enum`), where exactly one variant
is live.

## `datac`

```kelp
datac Point(val x: i32, val y: i32)
datac Counter(val id: i32, var count: i32)
datac Node(val value: i32, val next: Box<Node>)
```

- Fields are declared `val` (immutable) or `var` (mutable), one per
  comma-separated entry.
- **A `datac` holds owned data only.** A `str` field, a reference field or a
  `Unit` field is illegal, because the `datac` owns its fields and must be able
  to free them. Store a `String`.
- A field of another `datac` type is stored **inline**, so that type must be
  declared earlier in the same file. A self-referencing or forward-referencing
  field must be behind a `Box` or a `List`:

  ```kelp
  datac List2(val head: i32, val tail: Box<List2>)   // recursive, finite size
  datac Tree(val kids: List<Tree>)                   // recursive, finite size
  datac Bad(val next: Bad)                           // error: infinite size
  ```

- Construction is a call with the `datac` name, and field access is `.`:

  ```kelp
  val p = Point(x = 3, y = 4)
  print(p.x)

  var c = Counter(id = 1, count = 0)
  c.count = 5              // ok: field is var and c is a var binding
  ```

- Reading an owned field **by value** takes it out of an owned local:
  `val s = node.text` moves the field out and the local keeps the rest (see
  [Partial moves](/language/ownership)). Out of a borrow it is refused, because
  that would produce two owners of the same buffer: borrow it instead, or hold
  it in a `Box` and `take()` it out.
- `datac` values are dropped at the end of the owning scope, fields recursively.
- **A tuple is a record too.** `(i32, String)` is a record with positional
  fields: it needs no declaration, it is a legal `datac` field and a legal
  `enum` payload, and it obeys every rule above. Its positions are read by
  destructuring, because there is no `.0` ([Types](/language/types)).

## `enum`

```kelp
enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}
```

- Variants are newline-separated. Each is a name, optionally followed by
  `val`/`var` payload fields in parentheses.
- A payload field obeys every `datac` field rule: owned data only, stored inline,
  so a payload type must be declared earlier unless it is behind a `Box`/`List`.
- An `enum` value is owned and **not `Copy`**, like a `datac`. Assigning or
  passing one moves it; dropping it drops the live variant's payloads.
- Construction names the variant, qualified by the enum:
  `Shape.Circle(r = 1.0)`, `Shape.Empty`. Arguments may be named or positional.
- An `enum` may declare receiver methods, and a call on a value of the type
  resolves one. A receiver that builds a variant names a type rather than a value,
  so it is refused: bind the variant first.

## Matching

`when` with a scrutinee is the only pattern match, and it must be exhaustive:

```kelp
fun area(s: &Shape).R: f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}

fun label(s: &Shape).R: &str = when s {
    Circle(_) -> "circle"
    Rect(_, _) -> "rect"
    Empty -> "empty"
}
```

- The number of bindings must equal the number of payload fields; `_` ignores
  one.
- The scrutinee is matched where it is when it is a **place** (a binding, a
  field path, or a dereference): nothing moves out of it as a whole, and only the
  matched payload is copied, borrowed, or (an owned payload of an owned place)
  moved out. A **temporary** is bound to a hidden local first, so the arm has a
  place to read the payload out of, and a non-`Copy` payload borrow has something
  to point at for the length of the arm. A chain over a temporary stages its
  **root**, so `when mk().t { ... }` binds `mk()` and frees the whole value once.
- A payload binds as a **copy** when it is `Copy`, **by value** when it is owned
  and the scrutinee is an owned place (a `val`/`var` binding or a `move T`
  parameter), and as a **shared borrow** otherwise: `r` above is an `f64`, while a
  `Word(val text: String)` payload binds as an owned `String` out of an owned
  `Word` and as `&String` out of a `&Word`. The value taken by value is gone from
  the enum afterwards.
- There is no `else` requirement when every variant has an arm; an `else ->` arm
  covers the variants not named above it.

`if let` is the single-arm form, and it accepts the same scrutinees `when`
does, temporary ones included, by binding them to a hidden local first. See
[Control flow](/language/control-flow).

## Generics

Both declarations accept type parameters, and each use site instantiates them:

```kelp
datac Pair<A, B>(val first: A, val second: B)

enum Option<T> {
    Some(val value: T)
    None
}

val p: Pair<i32, String> = Pair(first = 1, second = "one")
val n: Option<i32> = Option.Some(value = 7)
```

- Write the arguments wherever a type is written: `Pair<i32, String>`,
  `List<Option<i32>>`, `Box<Pair<i32, i32>>`.
- Two instantiations of one template are two different types.
- A type argument may not be `str` or a reference.
- Type arguments are **inferred at a construction**; write them explicitly only
  when inference has nothing to go on: `Option.Some<i64>(value = 7)`.
- A payload-less variant cannot take an instantiation, because there is no call to
  attach it to: write the expected type instead:
  `val none: Option<i32> = Option.None`.

## Methods

A `datac` may carry methods ([Methods and receivers](/language/methods)), and so
may a concrete `enum`: `fun Shape.label()`, called on a value of the type
(`val s = Shape.Empty`, then `s.label()`), while `Shape.Empty.label()` is refused
because a receiver that builds the variant names a type rather than a value. A
generic `enum`'s template carries none, so combinators over `Option`/`Result` are
free functions in `std/option` and `std/result`.

## See also

- [Collections](/language/collections)
- [Generics and type parameters](/language/generics)
- [Ownership and borrowing](/language/ownership)
- [Errors and panics](/language/errors)
