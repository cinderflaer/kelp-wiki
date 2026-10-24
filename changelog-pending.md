---
title: "Pending changes"
description: "Changes that are in kelp but not in a released version yet. The release procedure reads this page; it replaces plan/CHANGELOG.pending.md."
isPublished: true
tags: "changelog, release"
---
> **Moved 2026-10-16.** This page replaces `plan/CHANGELOG.pending.md` in the kelp repository, which is removed. The release procedure now reads this page, not the kelp repository. Add a line here for every user-visible change, and wipe the lines back to this header when a version is released.

# Pending changes

Scratch file for changes that are not released yet. It lives on this page now: an edit here is the edit, and the wiki sync carries it.

Add a line here when a user-visible change lands in `kelp`. **Do not touch
`wiki/changelog.md` until a version is released**: the changelog page carries
releases only.

When a version drops, write that release's entry in `wiki/changelog.md` from
this file plus the tag's commits and the Gitea release body, then wipe this file
back to this header. No need to ask first.

Keep each line short and factual: what changed, and why it matters to someone
writing Kelp. Group under the headings below; delete the headings that stay
empty on release.

## added

- The type of a `const` is optional: `const LIMIT = 10` takes the type of its value, so an integer is `int`, a float `f64`, and a typed const keeps its type. A use never changes it, so a `const` used as a `usize` address or length keeps its annotation (`const BASE: usize = 0x1000`). An array, a tuple or a `section(...)` array still needs the type.
- A digit separator, `_` between two digits, may be written in an integer or float literal: `1_000_000`, `0x1000_0000`, `0b1010_1010`, `1_000.000_5`. It changes no value. A `_` first, last or doubled in a literal (`0x_ff`, `1_`, `1__000`) is refused by name, at the `_`.- The `val` on a `datac` or enum-payload field is optional: `datac Point(x: i32, y: i32)` is the same as `datac Point(val x: i32, val y: i32)`. A bare field is immutable, and `var` is still written, so a misused `var` keeps its message (issue #284).

- The `val` on a `datac` or enum-payload field is optional: `datac Point(x: i32, y: i32)` is the same as `datac Point(val x: i32, val y: i32)`. A bare field is immutable, and `var` is still written, so a misused `var` keeps its message (issue #284).

## Documentation

- The Coral, Polyp, fpl and Lighthouse pages match their `main` branches: Coral has no version pins and records `coral.lock`, Polyp exports no `QUIT_ID` and its API lists the v4 and v5 nodes, fpl has 32 libraries, and Lighthouse has a Kelp port of the server in progress.

- A `&` in front of a parameter of an owned type is redundant (issue #283): `s: &String`, `p: &Point` (a `datac`), `xs: &List<T>`, `m: &Map<K, V>`, `b: &Bytes`, `b: &Box<T>` and `s: &str` take the same arguments as the bare type. `kelpc lint` warns on it, and the examples and language pages write the bare type. `&dyn`, a scalar or another `Copy` type, a fixed-size array, a generic `T` and `fun X.eq(other: &X)` keep their `&`.

## Added

- A multi-line string literal: `"""` opens a block, a line holding only `"""` closes it, and the closing line's indentation is removed from the lines between. The value always ends with a newline and uses the string escapes, so a block equals the same text written with `\n` (issue 260). An unterminated block is refused at its opening.

## Changed

- Numeric conversions take the everyday names (issue #279): `to_byte()` and `try_to_byte()` convert to `u8` on an integer. `to_u8()` and `try_to_u8()` still compile and print an `outdated:` finding naming the fix; they are removed in the next development cycle. `to_int()` and `to_float()` are unchanged, and the fixed-width names (`to_i64()`, `to_f64()`, `to_usize()` and the rest) keep their names.
- Index and length functions take `int`, not `usize` (issue #278): `len`, `get`, `set`, `insert`, `remove`, `slice`, `str.byte`, `str.substring`, the `Bytes` read and write offsets, the byte counts of `mem.alloc`, `rand.bytes` and the `io` and `net` reads and writes, and the counts of `with_capacity` and `reserve`. Breaking: a `usize` passed to one of them is refused, and the message names both types, so convert with `to_int()`. A negative index panics with the same bounds message as today; a negative count to `with_capacity` or `reserve` panics with `negative count`. Addresses and arena or frame sizes (`Ptr.addr`, `Ptr.offset`, `Frame`, `Arena`, the allocator hooks) stay `usize`.
- Field shorthand: in a `datac` or enum variant construction, a bare name `host` means `host = host` when a local has that name, and it mixes with named arguments (`Job(host, port, paths = paths)`). A bare name with no matching local or field is refused with the name in the message. Calls to functions are unchanged.
- Bare variant construction (issue #281): `Circle(r = 1.0)` and `Empty` build the variant of an `enum` declared in the same module when no other enum of the same module declares a variant of that name. Two enums that share the name need the qualifier, and the refusal names it. `Shape.Circle(...)` still compiles, and `when` patterns already took the bare name. `None`, `Some`, `Ok` and `Err` keep their prelude meaning.

- The example pages match their programs: `count-lines-words-bytes` passes an absolute path, the `sandbox-directory-grant` panic line is current, and the `count-lines-in-kelp-tree` listing is the current `examples/src`.
- The bench runner (`bench/gc/run.sh`) and the Tidepool step 0, step 1 and block test comments describe the hosted build and the checked blocks. No behaviour changed.
- An unannotated integer literal is `int`, the 64-bit signed integer, instead of `i32` (decision 72, issue #275). `int` is a type name for `i64`, so `val n: int = 5` is valid. A value past 2^31 is an ordinary value with no annotation, and an unannotated literal past `i64::MAX` is refused by name. Annotated `i32` code is unchanged; code that relied on the `i32` default needs `: i32`.
- `int`, `uint` and `float` are distinct types of the target's native width (`i64`, `u64` and `f64` on a 64-bit target), not names for the fixed widths (issue #275, owner direction 2026-10-23). An unannotated float literal stays `f64`; `float` is written where it is wanted. `int` does not mix with `i32` or `i64` without a conversion: the refusal names every type involved. A diagnostic for an `int` value prints `int`. Code that passed an unannotated integer binding to an `i64` parameter converts it with `.to_i64()`.
- A hosted build accepts an owned `Box<dyn Trait>` as a `List` element, a `Map` value, a `Box` payload or a `datac` field when every type the program coerces into that trait is memory. A trait with an implementor that has a destructor stays refused, and the refusal names the trait object.
- An expression body with no `=> T` takes the type of its body as its return type (issue 280): `fun double(x: i32) = x * 2` builds. A recursive body, a `when` with several arms, an `asm` body, a generic or trait method, and a body whose type is a borrow still need the type written, and a public function's inferred type cannot name a private type.
