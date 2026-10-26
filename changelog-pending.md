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

- `kelpc boot <project dir>` builds a freestanding example and boots it under QEMU, checking the serial lines named by the `[run]` table in its `coral.toml` (`qemu`, `expect`, and the optional `ramfb` and `smp`). It replaces the `run.sh` scripts that each repeated the same QEMU command: 21 of the 25 examples lost theirs (issue #303). Four keep a `run.sh` because their checks are ordered or generated.

- Several plain module paths may share one `impl` line: `impl "std/str", "std/fmt", "std/option"` is the same as three lines, one module each, in the order written (issue #299). A `caps(...)` grant keeps its own line, and a grant written after a list is refused with that fix named. This is spelling only: the existing lines are unchanged.

- The pure std modules need no `impl` line (issue #300). `str`, `fmt`, `math`, `option`, `result`, `convert` and `iter` are in scope in every project module by their own names, and a module joins the program only when the file names it. A bare `Option<T>` and `Result<T, E>` are the std types, in annotations, generic arguments and the paths `Option.Some(...)` and `Result.Err(...)`. The `impl` line still works and keeps its meaning: a file whose own `impl` names a module `str` has that module as `str`, and the std `str` is then reached from another file. `derive(text)` no longer needs `impl "std/fmt"`. Capability modules keep their `impl` line.

- A file of top-level statements with no `fun main` runs them as its `main`, in source order, and declarations may come before, between or after them. A file with statements cannot also declare `main`, the statements may only be in the entry file, and `?` is refused in one, as it is in `fun main()` (issue #288).
- At the top level, `fun` may be left out of a function with no modifier: `main() { ... }`, `half(n: int) => int = n / 2`, `Counter.bump()` and `mut Counter.bump()` are the same as their `fun` forms, and one file may mix them. A `pub` function keeps `fun`, and a `pub` line without it is refused with `pub fun` named as the fix (issue #287).
- A `fun Type.name()` whose body writes `self` is exclusive with no `mut` written: the receiver mode is inferred from the body, so `fun mut` is not needed. A shared borrow cannot call such a method, and the refusal names the rule. Inside a datac block the mode is still written (`mut name()`), and a block method that writes `self` without it is refused with that fix named (issue #286).
- The type of a `const` is optional: `const LIMIT = 10` takes the type of its value, so an integer is `int`, a float `f64`, and a typed const keeps its type. A use never changes it, so a `const` used as a `usize` address or length keeps its annotation (`const BASE: usize = 0x1000`). An array, a tuple or a `section(...)` array still needs the type.
- A digit separator, `_` between two digits, may be written in an integer or float literal: `1_000_000`, `0x1000_0000`, `0b1010_1010`, `1_000.000_5`. It changes no value. A `_` first, last or doubled in a literal (`0x_ff`, `1_`, `1__000`) is refused by name, at the `_`.- The `val` on a `datac` or enum-payload field is optional: `datac Point(x: i32, y: i32)` is the same as `datac Point(val x: i32, val y: i32)`. A bare field is immutable, and `var` is still written, so a misused `var` keeps its message (issue #284).

- The `val` on a `datac` or enum-payload field is optional: `datac Point(x: i32, y: i32)` is the same as `datac Point(val x: i32, val y: i32)`. A bare field is immutable, and `var` is still written, so a misused `var` keeps its message (issue #284).

- A method may be written inside the braces of its `datac`, with no `fun` and no type name: `mut bump() { count += 1 }` in `datac Counter(val id: int, var count: int) { ... }` means the same as `fun mut Counter.bump()` written after the type. The two forms mix, and `fun` and `pub` are refused inside the block (issue #285).
- `derive(text)` writes the `Display` form of a `datac` or `enum` above it (issue #292): `impl fmt.Display` with `to_text`, so `"${x}"` and `print(x)` work with no hand-written impl. A `datac` reads `Point(3, ab)`, a `datac` with no fields `Blank()`, and an enum reads `Circle(2)` or its unit variant name `Empty`. Fields are written in declaration order and a `String` is written without quotes. The file must import `std/fmt`, and a field with no text form (a `List`, `Map`, `Box`, tuple or array, or a local type with no `to_text`) is refused by name. `derive(eq, hash, text)` may combine the three.

- An `extern fun` may name the C symbol it forwards to: `extern fun read(path: &str) => Bytes = "read_raw"` declares `read` as a function whose body calls `read_raw` with its parameters in order. The C symbol is the name the module's `symbols` list allows, and the std forwarding wrappers use the form now (issue #294).

- A parameter of a top-level `fun` may take a default value (issue #296): `fun scale(n: int, factor: int = 3)` makes `scale(2)` mean `scale(2, 3)`. The default is one literal, checked at each call, and a parameter with one comes after every parameter without one. An expression, another parameter, or a default on a method, generic function, `extern fun` or fun literal is refused.

- `main` may return `result.Result<unit, E>` (issue #298). On `Err(e)` the text of `e` goes to stderr with a newline and the program exits with status 1; on `Ok` it exits with status 0. `?` works in such a `main`. The success type must be `unit`, and `kelp_main_result` is reserved while `main` returns Result. A file needs no `std/io` or `std/process` import for this.

## Documentation

- The example modules open with a `//!` module header instead of a `//` comment block (issue #306). `kelpc doc` renders the header as the opening of each module's page, and `kelpc lint` no longer counts it as a comment run. Each header keeps its first paragraph and any paragraph that names a design path; the rest of the old block was repeated detail. The style page states the form in its new module header section.

- The Coral, Polyp, fpl and Lighthouse pages match their `main` branches: Coral has no version pins and records `coral.lock`, Polyp exports no `QUIT_ID` and its API lists the v4 and v5 nodes, fpl has 32 libraries, and Lighthouse has a Kelp port of the server in progress.

- A `&` in front of a parameter of an owned type is redundant (issue #283): `s: &String`, `p: &Point` (a `datac`), `xs: &List<T>`, `m: &Map<K, V>`, `b: &Bytes`, `b: &Box<T>` and `s: &str` take the same arguments as the bare type. `kelpc lint` warns on it, and the examples and language pages write the bare type. `&dyn`, a scalar or another `Copy` type, a fixed-size array, a generic `T` and `fun X.eq(other: &X)` keep their `&`.

- A function whose whole body is one `unsafe { ... }` block may be written `unsafe fun`, with the block left out (issue #289). The language chapter states the rule: every caller must already be in unsafe context. The compiler is unchanged, and three example functions in the kernel tests are written this way.

## Added

- A `coral.toml` section `[caps."<module id>"]` grants an imported module its capabilities once, so the `impl` lines that import it need no `caps(...)` clause (issue #301). The section is a ceiling: a clause on that module may grant only what the section covers, and the entry module keeps its `[caps]` section. No existing grant changes meaning.
- A multi-line string literal: `"""` opens a block, a line holding only `"""` closes it, and the closing line's indentation is removed from the lines between. The value always ends with a newline and uses the string escapes, so a block equals the same text written with `\n` (issue 260). An unterminated block is refused at its opening.

## Changed

- A string literal is written bare where a `String` is expected: `String.from_str("x")` in a `String` slot (a `val` or `var` with a written type, a `datac` field, an argument, a `List` element, a `Map` key or value, a `return`) becomes `"x"`. The conversion was already there (`str` to `String` where a `String` is expected); the wrapper was boilerplate. `String.from_str` stays for a non-literal argument, for a method call on its result (`String.from_str("x").as_str()`), and for an untyped `val` or `var` (issue #312).

- The example folders share one copy of each file they use (issue #305). `kelpc/tests/fixtures/examples/shared/` holds the NS16550 driver, the Sv39 walker and the Polyp framebuffer platform, and each example's `src/` links to its copy instead of carrying its own. The compiler reads a link as the file it names, so no module id, diagnostic or output changes, and the manifests are unchanged.

- A compiled-and-run test fixture keeps its expected stdout in a `// stdout-begin` trailer at the end of the file, not in the Rust test that runs it (issue #304). The test names and the number of passing tests do not change. The `impl` lines are not expanded yet (issue #357).

- One name for an empty map (issue #302): `Map.empty()` is the constructor, as `List.empty()` and `String.empty()` already are. `Map.new()` still compiles and prints an `outdated:` finding that names `Map.empty()`; it is removed in the next development cycle. The examples, the wiki pages and the test fixtures are written with `Map.empty()`. No meaning changes.

- One spelling of a function type (issue #293): `fun(T) => U` is the function pointer and `closure fun(T) => U` is the owned closure, with the `closure` marker in front of `fun`. The old `closure(T) => U` spelling is refused, and the message names the new one. Every example, library and page is written with the new spelling. Breaking: a `closure(...)` type in a program must become `closure fun(...)`. No meaning changes.

- A name that a `when` arm or an `if let` binds and never reads is an unused binding: `kelpc lint` warns on it and names the fix, `_` (issue #297). `Err(e) -> 0` becomes `Err(_) -> 0`, and a name that starts with `_` is never reported. Renaming to `_` does not change any program. The examples, the wiki examples and the test fixtures that bound a value they never read are written with `_`.

- The kernel examples write their field-wise `Pair` with `derive(eq, hash)` instead of a hand-written `eq` (issue #291). `derive` itself is unchanged, and no program changes.
- A group of exports may be written in one block: `pub { const LIMIT: i32 = 10 ... fun scale(...) ... }` exports each item in it, as if `pub` were written in front of it (issue #290). The block holds declarations only, each item keeps its own doc comment, and a `pub` written again inside the block is refused. No existing program changes.
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

- The borrowing `Option` and `Result` helpers have one definition each, written as methods (issue #295). `map`, `and_then`, `or_else` and `each` are methods only: `o.map(f)`, `r.and_then(f)`. Breaking: the free spellings `option.map`, `option.and_then`, `option.or_else`, `option.each`, `result.and_then`, `result.or_else` and `result.each` are removed, and a call to one is refused; write the method. `option.is_some`, `option.is_none`, `result.is_ok` and `result.is_err` keep their free spelling. `result.map` and `result.map_err` are unchanged.
- `spawn`, `run`, `run_inherit` and `try_run` take a trailing `dir: &str = ""` (issue #296), and `fmt.float`'s `decimals` defaults to 2. The `_in` forms (`spawn_in`, `run_in`, `run_inherit_in`, `try_run_in`) keep their signatures for one cycle and forward to the new functions; no program changes.
- The wiki examples no longer write `impl "std/str"`, `"std/fmt"`, `"std/math"`, `"std/option"`, `"std/result"`, `"std/convert"` or `"std/iter"` in project code, because those modules need no line (issue #300). Lines for modules that still need one are kept. Where the compiler still asks for `impl "std/option"` or `impl "std/result"` (a call that hands back one of those types from another module, such as `thread.join` or `Atomic.compare_exchange`), the example keeps its line.

- `pool.join_or_report(handle)` joins one thread handle and reports its error (issue #310). It returns the value as `Some`; an `Err` prints the worker's panic text on stdout and returns `None`. Write the type argument, `pool.join_or_report<T>(h)`, because `T` is not inferred from the handle yet. It lives in `std/pool` because a module cannot call its own `thread` builtins. `examples/download_pool.kp` uses it and its output does not change. `thread.join` is unchanged.
- `unwrap_or` is a method on `Option` and `Result` for a `Copy` payload: `o.unwrap_or(0)` and `r.unwrap_or(0)` (issue #311). The `Result` form drops the `Err` payload without reading it, so use it only where the error carries nothing the caller needs; where the error matters, use `when`, `?` or `map_err`. The free forms `option.unwrap_or(o = ..., fallback = ...)`, which takes an owned payload, and `result.unwrap_or(r = ..., fallback = ...)` are unchanged.
