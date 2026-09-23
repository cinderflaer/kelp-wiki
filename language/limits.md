---
title: "Limits in v1"
description: "Source section - syntax.md \u00a717. These are deliberate, and each one has a workaround in this documentation."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §17](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).
These are deliberate, and each one has a workaround in this documentation.

## Control flow

- **No `break` and no `continue`.** Iteration is a `for` over a `List`, or a
  `while` plus an index when the loop is not a front-to-back walk.
- No `loop` expression, no labelled loops.

## Errors

- **`?` propagates only an identical failure type.** There is no error
  conversion, no `From`, no boxing. `result.map_err` is the bridge.
- A function returning `Unit` has nowhere to propagate to.

## Data and generics

- **No extra type parameters on a method.** A `datac`, an `enum` and a `fun` may
  each declare type parameters, but a receiver on a generic type must write the
  type's own parameters, in order: `fun Pair<A, B>.first()`. A method cannot add
  parameters of its own. See [Generics and type parameters](/language/generics).
- **A method call through an `enum` value is refused**, and combinators over `Option` and
  `Result` are free functions. An `enum` may still *declare* a receiver method
  (the `Map` key pair below is one), and the compiler calls it, but `e.method()`
  on a binding of enum type is rejected; call a free function instead.
- **A `Map` key must be keyable.** The compiler derives the key's hash and
  equality from the fields, so the derived set is `String`, an integer, `bool`,
  `char`, or a `datac`/`enum` whose every field (or every variant payload) is
  itself keyable. A `datac` or `enum` outside that set becomes a key by declaring
  both `fun T.hash().R: u64` and `fun T.eq(other: &T).R: bool`, which the map
  calls instead of a derived pair; the key is still cloned into the entry, so the
  type has to be deep-copyable. A float is refused (`nan`), and a `Bytes`,
  container, view, borrow or `datac`/`enum` with a field outside the set is
  refused with a message naming that field or the half of the pair that is
  missing.
- **No user overloading**, and no user `extern` bodies: `extern fun` is reserved
  for compiler-shipped stdlib modules. (`abs`, `min`, `max`, `clamp` are the only
  overloads in the language, and they are stdlib-only.)

## Ownership

- **A partial move takes one projection of an owned local.** `val xs = bag.xs`
  moves that field out of an owned `val`/`var` local or a `move T` parameter, and
  the binding keeps the fields that stayed. An owned `enum` payload read by value
  out of an owned place is the same partial move, which is what a `when`/`if let`
  over an owned place does with the payload it binds. A projection read out of a
  borrowed structure or out of a nested place is still refused.
- **The helpers whose receiver stays a borrow are `Copy`-only.** `option.unwrap`
  on an `Option<String>` and `result.map` over a `Result<T, MyErr>` take their
  receiver with `move` now, so both work. `option.or_else`, `result.unwrap`,
  `result.unwrap_or`, `result.unwrap_err`, `result.expect`, `result.expect_err`,
  `result.and_then`, `result.or_else` and `list.filter` over a `List<String>`
  read through a borrow and rebuild what they hand back, so the payload (or the
  accepted element) must be `Copy`.
- **No references (and no `View`) in fields, `List` elements, `Map` values,
  array elements or `Box` contents.** Text you must store is a `String`; a view
  is taken at the point of use.
- A `View` never becomes a `str`: a slice has no NUL after it, so `str.len`/
  `str.eq` on one would read past the slice. Take `v.to_string()`.

## Containers

- **A `List` element and a `Box` element may be a `List` or a `Box`;** a `Map`
  value and an array element may not be a container at all, and every container
  refuses a borrow, a `str`, a `View`, an atomic, a function value and `Unit` as
  an element. A map that holds a list, or a named row, wraps the inner one in a
  one-field `datac` (as `csv.Row`, `listx.Chunk`, `table.Row` do).
- **`[T; N]` is fixed at its written length.** There is no `[T; 0]`, no `a[i]`
  subscript (write `.get`/`.set`, as on a `List`) and no growth. The repeat form
  `[x; N]` copies `x` into every slot, so its element has to own nothing, which
  is the one array shape a `datac` element cannot take: write the elements out,
  or start from a literal and `set` each one. An array cannot be a `List` or
  `Map` element, and an array element cannot be a `List`, `Map` or `Box`.
- No iteration protocol: `for` is a desugared index walk over a `List` or an
  array, and a `Map` has no iterator: iterate `keys()` and look up.

## Compile-time evaluation

- **A `const` is the same language, not a second one.** Its initializer may use
  the operators, `if`, an integer conversion, other `const`s, and a call to a
  plain `fun` whose own body stays inside that set. There is no `comptime`
  block, no compile-time `List`/`Map`, and no `size_of`/`align_of`; a builtin, an
  `extern fun` and a method call are all out of reach, so `str.len("x")` cannot
  be a constant.
- Evaluation is bounded: one million steps and sixty-four nested calls, and
  exceeding either is a diagnostic. A constant that calls a function is running
  inside the compiler, so the function has to terminate on the values the
  constant gives it.

## Concurrency

- **No threads, no async, no coroutines.** Concurrency is a later milestone; the
  standard library reaches the outside world by processes and by `poll`-style
  readiness (`wait_readable`) instead. A program that needs two things at once
  spawns a process. [Concurrency in v1](/language/concurrency) has the model as
  it stands.
- **An atomic cell and a standalone fence exist, and neither carries a thread by
  itself.** `Atomic<T>` in [`std/atomic`](/stdlib/atomic) is one location every
  access to which is a single atomic operation, and `thread.fence(order)` in
  [`std/thread`](/stdlib/thread) joins the total order while naming no location.
  The single ordering v1 has is `SeqCst`, and the fence changes nothing a
  single-threaded program can observe. There is no `thread.spawn` and no
  `thread.join` yet, so nothing shares the cell across threads today; a shared
  counter is a `pd val` atomic, which is the declaration that will let a second
  thread hold the borrow.

## Text

- `str.to_upper`/`to_lower` are **ASCII-only**.
- A string is UTF-8 by convention and bytes by API: most functions count bytes and
  the codepoint helpers are the separate `char_*` set.
- No regular expressions anywhere. [`glob`](/libraries/glob) has `*`/`?`,
  and that is the whole pattern language.

## Not present at all

No `unsafe`, no exceptions, no garbage collector, no macros, no traits, no
interfaces, no operator overloading, no `dyn` dispatch, no lifetime syntax, no
closures that capture a borrow, no named nested functions, and no undefined
behaviour escape hatch.

## See also

- [Concurrency in v1](/language/concurrency)
- [Pitfalls](/language/pitfalls)
- [Ownership and borrowing](/language/ownership)
- [Collections](/language/collections)
