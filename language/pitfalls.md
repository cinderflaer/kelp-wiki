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
| `use of moved value 'bag.xs'` | a field that was moved out by value was read again | bind the field once and use the binding, or take the whole value as a `move T` parameter |
| `cannot move out of a borrow` | a `move` parameter was handed a value that belongs to the caller | take a `move T` parameter yourself, or borrow |
| `cannot move the field 'xs' out of 'b': the value is borrowed, so it is not this frame's to give away` | an owned field was read by value out of a borrowed struct | pass a borrow, call a method on it, or take the value as a `move T` parameter and read the field from that local |
| `cannot read the owned field 'xs' by value: the base is not a local this frame owns, so a partial move cannot take the field out; use it through a borrow (pass it to a parameter, call a method on it) or hold it in a 'Box' and 'take()' it` | reading an owned field out of a temporary or a field chain | bind the owner to a local first, then read the field from that local |
| `cannot use 'bag' as a whole value: its field 'xs' was moved out` | using or borrowing the binding as a whole after one of its fields was moved out | use the fields that stayed, or assign a fresh value into the moved field on a `var` local |
| `use of moved value 'h.text'` | that `enum` payload was read by value already | a payload of an owned place is taken once, exactly as a field is: match the payloads that stayed, or match a borrow of the enum |
| `cannot use 'h' as a whole value: its payload 'text' was moved out` | using the enum as a whole after one of its payloads was moved out | match only the payloads that stayed, or match a borrow of the enum instead |
| `this call returns a borrow of its parameter 'self', so that argument has to be a variable or a field` | a method that returns a borrow of its receiver was called on a temporary | bind the receiver first: `val u = set.union(a, b)` then `u.len()`; a field of a returned `datac` (`mkName().name.as_str()`) is the same case one projection deeper |
| `this is a borrow of a borrow` (with the operand named) | `&o` where `o` is already a borrow, which a parameter always is | pass the parameter itself: `o`, not `&o` |
| `cannot borrow a temporary value` | `&expr` needs a place, and a call's result is not one, nor is a field of one | bind the call to a `val` and borrow the field of that: `val h = mk()` then `&h.name` |
| `operator requires matching numeric operands, found 'mut i64' and 'i32'` (with the `write '*sink'` note) | a `mut T` parameter is an exclusive borrow, so it is read and written through `*` | write `*sink`, not `sink`, wherever the value is used |

## Text

| Message | Fix |
| --- | --- |
| `argument 'b' has type 'String', expected 'str'` | the parameter takes a view: add `.as_str()` |
| `argument 'x' has type 'View', expected 'str'` | a slice has no NUL after it: `v.to_string()` |
| `.as_str()` on a temporary is refused | bind the `String` to a `val` first (same for `.view()`); a chained call is the same temporary one step out (`fmt.int(n).as_str()`) |
| a template is refused as a value | `a string template can only be printed`: build the text with `str.concat`, `fmt.*` or a `String`, or print it where it is written |
| `field 'text' is a borrowed type ('View')` | a view cannot be stored: store a `String` |
| `cannot compare 'View' values with '=='` | use `v.eq(other)`, which compares bytes and lengths |
| `field 'text' is a borrowed type (str)` | same as the `View` case: a field must be owned |

## Characters and integers

| Message | Fix |
| --- | --- |
| `argument 'c' has type 'char', expected 'u8'` | a character literal with nothing asking for a type is a `char`, and a `char` is not an integer; write the byte as a byte literal (`b'"'`) or write the type (`val c: u8 = '"'`) |
| `a byte literal is a 'u8', not a 'i64'` | a byte literal is a `u8` by construction and does not take the type its context asks for; use a character literal when the type should come from where it sits |
| `a byte literal is one ASCII character or a '\xNN' escape` | a non-ASCII character is a code point, so it belongs in a character literal; `b'\xe9'` is the byte 233 |
| `a hex escape is written '\xNN', with two hex digits` | the escape is exactly two hex digits in every literal form; in a string literal it stops at the ASCII range, so `"\xff"` is not text |
| `a 'str' is NUL-terminated, so '\x00' cannot be in a string literal` | a `str` ends at a NUL, so the escape cannot spell one; build arbitrary bytes with `Bytes` |
| `a 'str' is NUL-terminated, so a raw NUL byte cannot be in a string literal` | the same rule for the byte written literally rather than escaped: the `str` ends there, so the literal cannot carry one; build arbitrary bytes with `Bytes` (`Bytes.empty` then `push`) |
| `the character '中' (U+4E2D) does not fit in 'u8'` | a character literal takes the type its context asks for; use a wider type, or the byte you meant |
| `operator requires matching integer operands, found 'u8' and 'bool'` | `& \| ^ << >> ~` are integer-only and both operands must be the *same* type |
| a `n * 1.0` type error | there is no implicit numeric conversion: `n.to_f64()` |
| `i32.to_u64: value out of range` (runtime) | the plain conversion panics when the value does not fit; `n.try_to_u64()` returns `Option<T>` instead, so the caller can test |

## Collections

| Symptom | Fix |
| --- | --- |
| `List.empty()` / `Map.new()` has no element type | nothing said what is inside and nothing decided it: write it on the binding (`var xs: List<i32> = List.empty()`), or `push`/`insert`/`set` a value, which decides the element |
| a `Map` value or an array element is a container | a `List` element and a `Box` element may be a `List` or a `Box`, but a `Map` value and an array element may not be a container at all; wrap the inner one in a one-field `datac` |
| `Map` key type refused | a key is keyable when the compiler can derive its hash and its equality: `String`, an integer, `bool`, `char`, or a `datac`/`enum` whose fields are all keyable, and a `datac`/`enum` outside that set becomes a key by declaring `hash` and `eq`. The message names the field that is not, or the half of the pair that is missing |
| `for` cannot `push` to what it walks | the loop borrows its iterable; iterate over a copy or index the source |

## Arrays and constants

| Message | Fix |
| --- | --- |
| `an array of 3 element(s) is expected here, and this literal has 2` | the length is part of the type, so `[T; N]` and the literal have to agree, and `[x; N]` has to produce `N` |
| `'k' is not a constant here` | an array's length is evaluated at compile time: write a literal, a `const`, or an expression over them. A `val` computed at runtime is not a constant, and a `const` may only name constants declared before it |
| `the repeat form '[x; N]' needs an element that owns nothing` | `[x; N]` copies `x` into every slot, so `x` cannot own memory; write the elements out, or use a scalar or a scalar-only `datac` |
| `'&i32' cannot be a container element` | a container owns its elements, so a borrow cannot be one |
| `an array length has to be at least 1` | there is no `[T; 0]`; a zero-length C array is not standard C |
| `Array.get: index out of bounds` (runtime) | the index was checked against the array's own length; the call site is the bug |
| `'print' cannot be called in a constant expression` | a `const` is folded inside the compiler, so it cannot call a builtin, an `extern fun` or a method, only a plain `fun` that stays inside what a constant can evaluate |
| `this constant expression did not finish within 1000000 steps` | a `const` may call a `fun`, and that function has to terminate on the values the constant gives it |

## Closures

| Symptom | Fix |
| --- | --- |
| a borrowed binding cannot be captured | pass it as a parameter of the literal instead |
| `*x` on a closure parameter fails | a `Copy` parameter is used directly: `acc + x`, not `acc + *x` |

## Modules and capabilities

| Message | Fix |
| --- | --- |
| `cannot find module` / a name resolves nowhere | `impl` the file, and note that paths are relative to the project's `src/` |
| `'lib.hidden' is private: 'hidden' is declared in module 'lib' without 'pub' ...` | the item exists but another module cannot reach it; add `pub` to its declaration, or call it from inside its own module. A name that does not exist at all gets `module 'lib' has no item 'hidden'` instead, and a "did you mean" hint never offers a private item |
| `'pub' applies to a top-level 'fun', 'extern fun', 'datac', 'enum' or 'const', found ...` | `pub` goes in front of one of those declarations and nowhere else |
| `pub` is refused on a `pd` or on a method | a passdown is module-scoped by design, and a method's reachability follows its declaring type: mark the type `pub` instead |
| `'lib.make' is exported but its signature names 'lib.Hidden', which module 'lib' does not export ...` | the declaration is reachable from another module, so every type its signature names has to be reachable too; add `pub` to the type, or make the declaration private. It covers a `pub fun`'s parameters and return, a method inside a `pub datac` or `pub enum`, a `pub extern fun`, a `pub datac`'s fields and a `pub enum`'s variant payloads, and the type arguments of a container, an array, a borrow or a function type |
| a gated call is refused and names a domain | write the grant on the `impl` line: `caps(fs = ["/srv/data/**"])` |
| `... needs the 'fs' capability, which module 'x' was not granted` and `x` is not the module you wrote the call in | the module that holds nothing is the middle one; the message names the `impl` line that imported it without a `caps(...)` clause, and that line is the one to change |
| a path with `..` or a relative path is refused | `fs`/`process` patterns match absolute, normalized paths |
| `127.0.0.1` is not covered by `localhost` | `net` matches the host **string you wrote**, not a resolved address |
| an `impl` after a declaration is a parse error | imports go first, then `const`/`pd`, then types and functions |

## Contract limits that look like errors

| Symptom | Reality |
| --- | --- |
| `option.or_else` / `result.unwrap` on an owned payload will not type-check | the helpers whose receiver stays a borrow are `Copy`-only; `option.unwrap`, `option.unwrap_or`, `option.expect`, `result.map` and `result.map_err` take their receiver with `move`, and `if let`/`when` over an owned place binds the payload by value |
| `?` refuses to propagate a different error type | v1 has no error conversion; `result.map_err` is the bridge |
| two `fun pick(...)` overloads collide | a user module cannot overload; spell the type into the name |
| an `enum` cannot have a method | v1 has no enum methods; write a free function |

## The one behaviour that is not a warning

Integer `+`, `-` and `*` overflow is **unchecked**: it wraps silently. If a wrap
matters, use [`mathx`](/libraries/mathx)'s checked or saturating forms.

## See also

- [Ownership and borrowing](/language/ownership), [Text](/language/text), [Collections](/language/collections), [Constants and passdowns](/language/passdowns)
- [Capabilities](/language/capabilities)
