---
title: "Pitfalls"
description: "The rules that explain most compile errors, with the message each one produces and the fix. Source - syntax.md \u00a718 and \u00a722."
isPublished: true
tags: "language"
---
The rules that explain most compile errors, with the message each one produces and
the fix. Source: [`syntax.md` §18 and §22](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Ownership

| Message | What happened | Fix |
| --- | --- | --- |
| `use of moved value 'a'` | an owned value was assigned, returned or passed with `move` | borrow instead (a plain parameter borrows), make a second owned copy, or reorder so the last use is last |
| `cannot move out of a borrow` | a `move` parameter was handed a value that belongs to the caller | take a `move T` parameter yourself, or borrow |
| `cannot read the owned field 'name' by value: v1 has no partial moves` | reading an owned field out of a borrowed struct | pass a borrow, call a method on it, or hold it in a `Box` and `take()` |
| `this call returns a borrow of its parameter 'self', so that argument has to be a variable or a field` | a method that returns a borrow of its receiver was called on a temporary | bind the receiver first: `val u = set.union(a, b)` then `u.len()` |

## Text

| Message | Fix |
| --- | --- |
| `argument 'b' has type 'String', expected 'str'` | the parameter takes a view: add `.as_str()` |
| `argument 'x' has type 'View', expected 'str'` | a slice has no NUL after it: `v.to_string()` |
| `.as_str()` on a temporary is refused | bind the `String` to a `val` first (same for `.view()`) |
| `field 'text' is a borrowed type ('View')` | a view cannot be stored: store a `String` |
| `cannot compare 'View' values with '=='` | use `v.eq(other)`, which compares bytes and lengths |
| `field 'text' is a borrowed type (str)` | same as the `View` case: a field must be owned |

## Characters and integers

| Message | Fix |
| --- | --- |
| `argument 'c' has type 'char', expected 'u8'` | a character literal with nothing asking for a type is a `char`; write `val c: u8 = '"'` |
| `the character '中' (U+4E2D) does not fit in 'u8'` | a character literal takes the type its context asks for; use a wider type, or the byte you meant |
| `operator requires matching integer operands, found 'u8' and 'bool'` | `& \| ^ << >> ~` are integer-only and both operands must be the *same* type |
| a `n * 1.0` type error | there is no implicit numeric conversion: `n.to_f64()` |
| `i32.to_u64: value out of range` (runtime) | narrowing conversions panic when the value does not fit |

## Collections

| Symptom | Fix |
| --- | --- |
| `List.empty()` / `Map.new()` has no element type | write it on the binding: `var xs: List<i32> = List.empty()` |
| a nested container is refused | wrap the inner one in a one-field `datac` or a `Box` |
| `Map` key type refused | keys are `String`, an integer or `bool`, and only those |
| `for` cannot `push` to what it walks | the loop borrows its iterable; iterate over a copy or index the source |

## Closures

| Symptom | Fix |
| --- | --- |
| a borrowed binding cannot be captured | pass it as a parameter of the literal instead |
| `*x` on a closure parameter fails | a `Copy` parameter is used directly: `acc + x`, not `acc + *x` |
| a closure parameter over a module-declared type fails to compile | a compiler bug, not a language rule: see [Known issues](/meta/known-issues) |

## Modules and capabilities

| Message | Fix |
| --- | --- |
| `cannot find module` / a name resolves nowhere | `impl` the file, and note that paths are relative to the project's `src/` |
| a gated call is refused and names a domain | write the grant on the `impl` line: `with caps(fs = ["/srv/data/**"])` |
| a path with `..` or a relative path is refused | `fs`/`process` patterns match absolute, normalized paths |
| `127.0.0.1` is not covered by `localhost` | `net` matches the host **string you wrote**, not a resolved address |
| an `impl` after a declaration is a parse error | imports go first, then `const`/`pd`, then types and functions |

## Contract limits that look like errors

| Symptom | Reality |
| --- | --- |
| `option.unwrap` on an `Option<String>` will not type-check | the combinators are `Copy`-only; use `if let`/`when`, or `Box.take` |
| `?` refuses to propagate a different error type | v1 has no error conversion; `result.map_err` is the bridge |
| two `fun pick(...)` overloads collide | a user module cannot overload; spell the type into the name |
| an `enum` cannot have a method | v1 has no enum methods; write a free function |

## The one behaviour that is not a warning

Integer `+`, `-` and `*` overflow is **unchecked**: it wraps silently. If a wrap
matters, use [`mathx`](/libraries/mathx)'s checked or saturating forms.

## See also

- [Known issues](/meta/known-issues): the defects that affect valid programs
- [Ownership and borrowing](/language/ownership), [Text](/language/text), [Collections](/language/collections)
- [Capabilities](/language/capabilities)
