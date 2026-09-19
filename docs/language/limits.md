# Limits in v1

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

- **No generic functions.** `datac` and `enum` take type parameters; `fun` does
  not. A function that must work for several types is written per type, which is
  why `listx` has `sum_i32`/`sum_i64`/`sum_f64` and `testkit` has
  `check_eq_i64`/`check_eq_str`.
- **A receiver on a generic type must write the type's own parameters**, in order:
  `fun Pair<A, B>.first()`. There is no way to declare a method with parameters of
  its own.
- **An `enum` carries no methods**, generic or not: combinators over `Option` and
  `Result` are free functions.
- **A `Map` key must be `String`, an integer or `bool`.** The compiler generates
  the key's hash and equality, so the set is closed: a float is refused (`nan`),
  and a `datac`, container or borrow is refused because v1 has no equality for
  them.
- **No user overloading**, and no user `extern` bodies: `extern fun` is reserved
  for compiler-shipped stdlib modules. (`abs`, `min`, `max`, `clamp` are the only
  overloads in the language, and they are stdlib-only.)

## Ownership

- **No partial moves.** An owned field cannot be read out of a borrowed
  structure, and an owned `enum` payload cannot be read out of an owned one
  either: use a `Box` and `take()` it, or pass a borrow.
- That is what makes some stdlib helpers `Copy`-only: `option.unwrap` on an
  `Option<String>`, `result.map` over a `Result<T, MyErr>` and `list.filter` over
  a `List<String>` each need a move out that does not exist yet.
- **No references (and no `View`) in fields, `List` elements, `Map` values or
  `Box` contents.** Text you must store is a `String`; a view is taken at the
  point of use.
- A `View` never becomes a `str`: a slice has no NUL after it, so `str.len`/
  `str.eq` on one would read past the slice. Take `v.to_string()`.

## Containers

- **`List` and `Map` cannot nest directly** and cannot hold a borrow, a `str`,
  `Unit` or another container. Wrap the inner one in a one-field `datac` (as
  `csv.Row`, `listx.Chunk`, `table.Row` do) or a `Box`.
- No iteration protocol: `for` is a desugared index walk over a `List`, and a
  `Map` has no iterator: iterate `keys()` and look up.

## Concurrency

- **No threads, no async, no coroutines.** Concurrency is a later milestone; the
  standard library reaches the outside world by processes and by `poll`-style
  readiness (`wait_readable`) instead. A program that needs two things at once
  spawns a process.

## Text

- `str.to_upper`/`to_lower` are **ASCII-only**.
- A string is UTF-8 by convention and bytes by API: most functions count bytes and
  the codepoint helpers are the separate `char_*` set.
- No regular expressions anywhere. [`glob`](../libraries/glob.md) has `*`/`?`,
  and that is the whole pattern language.

## Not present at all

No `unsafe`, no exceptions, no garbage collector, no macros, no traits, no
interfaces, no operator overloading, no `dyn` dispatch, no lifetime syntax, no
closures that capture a borrow, no named nested functions, and no undefined
behaviour escape hatch.

## See also

- [Pitfalls](pitfalls.md)
- [Ownership and borrowing](ownership.md)
- [Collections](collections.md)
