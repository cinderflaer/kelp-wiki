---
title: "Pitfalls"
description: "The compile errors and runtime panics that come up most often, with the message each one prints and the fix for it."
isPublished: true
tags: "language"
---
The rules that explain most compile errors, with the message each one produces and
the fix. Source: [`syntax.md` §18 and §22](/design/syntax).

## Ownership

| Message | What happened | Fix |
| --- | --- | --- |
| `use of moved value 'a'` | an owned value was assigned, returned or passed with `move` | borrow instead (a plain parameter borrows), make a second owned copy, or reorder so the last use is last |
| `use of moved value 'bag.xs'` | a field that was moved out by value was read again | bind the field once and use the binding, or take the whole value as a `move T` parameter |
| `cannot move out of a borrow` | a `move` parameter was handed a value that belongs to the caller | take a `move T` parameter yourself, or borrow |
| `cannot move the field 'xs' out of 'b': the value is borrowed, so it is not this frame's to give away` | an owned field was read by value out of a borrowed struct | pass a borrow, call a method on it, or take the value as a `move T` parameter and read the field from that local |
| `cannot read the owned field 'xs' by value: the base is not a local this frame owns, so a partial move cannot take the field out; use it through a borrow (pass it to a parameter, call a method on it) or hold it in a 'Box' and 'take()' it` | reading an owned field out of a temporary or a borrowed structure | bind the owner to a local first, then read the field from that local |
| `cannot use 'bag' as a whole value: its field 'xs' was moved out` | using or borrowing the binding as a whole after one of its fields was moved out | use the fields that stayed, or assign a fresh value into the moved field on a `var` local |
| `use of moved value 'h.text'` | that `enum` payload was read by value already | a payload of an owned place is taken once, exactly as a field is: match the payloads that stayed, or match a borrow of the enum |
| `cannot use 'h' as a whole value: its payload 'text' was moved out` | using the enum as a whole after one of its payloads was moved out | match only the payloads that stayed, or match a borrow of the enum instead |
| `this call returns a borrow of its parameter 'self', so that argument has to be a variable or a field` | a borrow-returning call was used outside a supported direct text-view binding | bind the owned receiver first; `val view = String.from_str("x").as_str()` and `val name = mkName().name.as_str()` promote their temporary owner |
| `this is a borrow of a borrow` (with the operand named) | `&o` where `o` is already a borrow, which a parameter always is | pass the parameter itself: `o`, not `&o` |
| `cannot borrow a temporary value` | `&expr` needs a place, and a call's result is not one, nor is a field of one | bind the call to a `val` and borrow the field of that: `val h = mk()` then `&h.name` |
| `operator requires matching numeric operands, found 'mut i64' and 'i32'` (with the `write '*sink'` note) | a `mut T` parameter is an exclusive borrow, so it is read and written through `*` | write `*sink`, not `sink`, wherever the value is used |
| `cannot borrow 'names' as exclusive: already borrowed as shared` | the owner is mutated while a bound borrow into it is still used later in the block, or later in the same loop | move the mutation after the borrow's last use; a use inside a loop body keeps the borrow live for the whole loop |
| `cannot assign to 'list' while it is borrowed` | a cursor or a view into `list` is still used when `list` is reassigned | stop using the cursor first, or rebind the cursor to a different owner |
| `cannot borrow 'a': already borrowed exclusively` | two live exclusive borrows of one place: two `mut` cursors, or copying a `&mut` into a second binding | keep one exclusive borrow at a time; shared cursors into the same owner are fine |
| `cannot move 'list' while it is borrowed` | an owner is moved while a cursor into it is live | stop using the cursor first |
| `cannot return a borrow of 'local': ...` | a borrow rooted in a frame local is returned | return a borrow derived from the first reference parameter, or return an owned value instead |

Two borrow errors that used to be common no longer appear. A bound borrow ends
at its last use, so `val first = names.get(0); print(first.as_str());
names.push(x)` compiles without wrapping the read in an extra `{ }`; that
workaround is obsolete. And a reference binding remembers the owner its value
came from, so `var cur = &list; cur = cur.next.get()` is accepted and
`cannot assign to 'cur' while it is borrowed` no longer names the cursor. See
[Borrows end at their last use](/language/ownership#borrows-end-at-their-last-use)
and [Cursors and provenance](/language/ownership#cursors-and-provenance).

## Text

| Message | Fix |
| --- | --- |
| `cannot assign value of type 'String' to 'y' declared as 'str'` | a `str` binding takes a view: add `.as_str()` |
| `argument 'x' has type 'View', expected 'str'` | a slice has no NUL after it: `v.to_string()` |
| a returned borrow of a temporary is refused | a direct `val` binding may promote `String.from_str("x").as_str()` or `.view()`; return an owned `String` instead when the borrow would escape |
| `field 'text' stores a borrowed 'View'` | move the String/Bytes that owns the view into an earlier field of the same `datac`, or store an owned `String` |
| comparing two `str` values | a `str` is a borrowed pointer, so `==` would compare addresses: use `str.eq`, or compare two `View`s with `v == w` |
| `field 'text' stores a borrowed 'str'` | a string literal is static; otherwise move its String/Bytes owner into an earlier field of the same `datac` |

## Equality

| Message | What happened | Fix |
| --- | --- | --- |
| `cannot compare 'P' values with '=='` | a `datac`/`enum` gets `==`/`!=` only from a declared `eq`, and nothing is derived | declare `fun P.eq(other: &P) => bool`, which `a == b` lowers to (`a.eq(&b)`); or compare the fields directly, or match with `when` |
| `cannot compare 'P' values with '<'` | `<`/`<=`/`>`/`>=` are refused on a `datac`/`enum` with no `Ord` impl, whether or not it has `eq` | implement `ops.Ord` (see [Operator traits](/language/operator-traits)), or compare the fields you mean |
| `'P.eq' takes exactly one parameter, a shared borrow of 'P'` | the `eq` method has the wrong signature | write `fun P.eq(other: &P) => bool`: one parameter, a shared borrow of the type, returning `bool` |
| `cannot compare 'A' with 'B'` | the two operands are different types | make both sides the same type |

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
| a type error on `n * 1.0` | integers and floats do not mix. Convert the integer first with `n.to_f64()`. An integer literal adapts to a float type, but a variable does not |
| `i32.to_u64: value out of range` (runtime) | the plain conversion panics when the value does not fit; `n.try_to_u64()` returns `Option<T>` instead, so the caller can test |

## Collections

| Symptom | Fix |
| --- | --- |
| `List.empty()` / `Map.empty()` has no element type | nothing said what is inside and nothing decided it: write it on the binding (`var xs: List<i32> = List.empty()`), or `push`/`insert`/`set` a value, which decides the element |
| a `Map` value or an array element is a container | a `List` element and a `Box` element may be a `List` or a `Box`, but a `Map` value and an array element may not be a container at all; wrap the inner one in a one-field `datac` |
| `Map` key type refused | a key is keyable when the compiler can derive its hash and its equality: `String`, an integer, `bool`, `char`, or a `datac`/`enum`/tuple whose fields, variant payloads or positions are all keyable, and a `datac`/`enum` outside that set becomes a key by declaring `hash` and `eq`. The message names the field that is not, or the half of the pair that is missing |
| `cannot mutate 'xs' while iterating over it` | the body may read the list it walks but not change it; walk a different list, or change the source by index in a `while` |

## Tuples

| Message | What happened | Fix |
| --- | --- | --- |
| `this pattern has 3 position(s), and the tuple it destructures ('(i32, i32)') has 2` | the pattern writes a different number of positions than the tuple has elements | write one binding per element, and `_` for a position you do not need |
| `a destructuring binding takes no written type: ...` | `val (a, b): (i32, i32) = ...` wrote one type for several positions | bind the whole value first (`val p: (i32, i32) = ...`), then `val (a, b) = p` |
| `a destructuring binding takes one tuple value apart, and this initializer is a 'i32'` | the initializer is not a tuple | bind a single value with an ordinary `val name = ...` |
| `use of moved value 'p'` | the initializer was already taken apart by an earlier destructuring | bind the value once, and name every position you need in that one statement |
| `cannot read element 1 of the tuple out of a borrow by value: ...` | an owned position was read out of a borrow | read a `Copy` position, use the tuple through a borrow, or take it with `move` |
| `element 1 of the tuple is a borrowed type ('str')` | a tuple stores its elements by value, exactly as a `datac` field does | store an owned `String` |
| `element 2 of the tuple is 'unit'` | `unit` is the absent value and cannot be stored | produce a value, or leave the position out |
| `'Later' is declared after this type` | a tuple element is a by-value field, so it may only name a type declared earlier | declare the element type first, or hold it behind a `Box` or a `List` |
| `cannot pass a value of type '(i32, i32)' to 'print'` | a tuple is a record, and `print` takes a scalar, a `str` or a `String` | print each position |

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
| `'pub' applies to a top-level 'fun', 'extern fun', 'extern type', 'datac', 'enum' or 'const', found ...` | `pub` goes in front of one of those declarations and nowhere else |
| `pub` is refused on a `pd` or on a method | a passdown is module-scoped by design, and a method's reachability follows its declaring type: mark the type `pub` instead |
| `'lib.make' is exported but its signature names 'lib.Hidden', which module 'lib' does not export ...` | the declaration is reachable from another module, so every type its signature names has to be reachable too; add `pub` to the type, or make the declaration private. It covers a `pub fun`'s parameters and return, a method inside a `pub datac` or `pub enum`, a `pub extern fun`, a `pub extern type`'s parent, a `pub datac`'s fields and a `pub enum`'s variant payloads, and the type arguments of a container, an array, a borrow or a function type |
| a gated call is refused and names a domain | write the grant on the `impl` line: `caps(fs = ["/srv/data/**"])` |
| `... needs the 'fs' capability, which module 'x' was not granted` and `x` is not the module you wrote the call in | the module that holds nothing is the middle one; the message names the `impl` line that imported it without a `caps(...)` clause, and that line is the one to change |
| a path with `..` or a relative path is refused | `fs`/`process` patterns match absolute, normalized paths |
| `127.0.0.1` is not covered by `localhost` | `net` matches the host **string you wrote**, not a resolved address |
| an `impl` after a declaration is a parse error | imports go first, then `const`/`pd`, then types and functions |

## Contract limits that look like errors

| Symptom | Reality |
| --- | --- |
| `o.or_else(f)` / `result.unwrap` on an owned payload will not type-check | the helpers whose receiver stays a borrow are `Copy`-only; `option.unwrap`, `option.unwrap_or`, `option.expect`, `result.map` and `result.map_err` take their receiver with `move`, and `if let`/`when` over an owned place binds the payload by value |
| `?` refuses to propagate a different error type | `?` converts a failure only through an `impl convert.From<E1> for E2`; write the impl, or use `result.map_err` ([Generic traits](/language/generic-traits)) |
| two `fun pick(...)` overloads collide | a user module cannot overload; spell the type into the name |
| `Shape.Empty.label()` is refused | a receiver that builds a variant names a type; bind it first (`val s = Shape.Empty`, then `s.label()`) |

## Integer overflow is not checked

Integer `+`, `-` and `*` overflow **wraps silently**. The compiler gives no warning. If a wrap
matters, use [`mathx`](/libraries/mathx)'s checked or saturating forms.

## See also

- [Ownership and borrowing](/language/ownership), [Text](/language/text), [Collections](/language/collections), [Constants and passdowns](/language/passdowns)
- [Capabilities](/language/capabilities)
