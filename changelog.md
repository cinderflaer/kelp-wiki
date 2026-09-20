---
title: "Changelog"
description: "Every release of Kelp, newest first: what the language gained and what the compiler that implements it gained with it. Entries are short; plan/done.md keeps the full milestone record."
isPublished: true
tags: "language, compiler"
---
Every release of Kelp, newest first. The version is the `kelpc` version
(`kelpc version`), the tag is in the
[kelp repository](https://homelabone.xenoo.dev/gittea/Juniper/kelp), and the
release notes and binary asset are on the
[releases page](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases).

A release entry covers **the language and the compiler together**, because in
this project they ship as one artifact: a new construct is a lexer, a parser, a
checker and a backend change at once. Tooling releases have their own pages:
[Coral changelog](/tooling/coral-changelog) and
[Lighthouse changelog](/tooling/lighthouse-changelog).

**Numbering, 2026-09-20.** The tags `v0.2.0` to `v0.2.3` were renamed to
`v0.1.2` to `v0.1.5`, and the Gitea releases with them: the first scheme counted
milestones rather than shipped versions, so six releases carried two minor
numbers. Each renamed tag keeps its commit and its release asset, so the files
are the original builds, not rebuilt ones. The build-time version string inside
them therefore still carries the old number: running
`kelpc-0.1.5-linux-x86_64 version` prints `kelpc 0.2.3`. A source checkout of
`main` reports `0.1.6`, and every release cut from here on reports its own
number.

These entries are deliberately short. The authority for what a milestone
actually contained is
[`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md);
this page is the index to it.

| Version | Date | Headline |
| --- | --- | --- |
| [0.1.5](#015-2026-09-20) | 2026-09-20 | the compiler emits its own x86-64 assembly; `kelpc fmt`; block comments |
| [0.1.4](#014-2026-09-19) | 2026-09-19 | five checker bugs found by a real 807-line program |
| [0.1.3](#013-2026-09-19) | 2026-09-19 | a literal takes its sibling operand's type on either side |
| [0.1.2](#012-2026-09-19) | 2026-09-19 | `View`, `char` literals, bitwise operators, `str` to `String` coercion |
| [0.1.1](#011-2026-09-19) | 2026-09-19 | the `for` loop, `spawn_in`/`run_in`, fallible `try_run`, `fs.symlink` |
| [0.1.0](#010-no-release) | 2026-09-19 | first tag: the core language, modules, containers, capabilities, stdlib |

## 0.1.5 (2026-09-20)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.5)
· 84 commits · 112 unit tests, 291 end-to-end green on the C backend, 242 of
them on the assembly backend.

**The compiler emits its own x86-64 assembly.** `kelpc build --backend=asm`
writes assembly itself and finishes it with `as` and `ld`; no C compiler in
that chain. The C backend stays as the differential oracle, so every fixture is
built by both and their stdout compared byte for byte. Constructs the new
backend cannot lower yet are refused **by name** rather than miscompiled: the
`fs`/`io`/`net`/`path`/`process` extern bodies, closures and function values,
and a capability-gated call.

What the assembly backend covers: `enum` tagged unions with `when`, `if let`
and a generated per-`enum` drop; **float fields in aggregates with the real
SysV per-eightbyte classifier** (SSE only when every field overlapping the
eightbyte is a float), pinned by a test that reads the emitted assembly; float
locals in the xmm pool with direct memory and immediate operands; a scalar
`mut` borrow and the store through it; owned heap fields, `Box<T>`, `List<T>`,
`Map<K, V>`, `String` and `View`; extern calls through the PLT; passdowns as
generated storage, with owned ones freed from a generated `kelp_drop_pds` that
`main` registers with `atexit`. The division-and-add kernel went from 4.16x the
`-O0` column to 0.54x of `cc -O2`.

**`kelpc fmt`**, with `--check` and `-w`: a token-level, comment-preserving
formatter, plus the lexer trivia it needs, and a 27-pair corpus.

**Block comments** (`/* ... */`).

**The runtime's Kelp half.** The capability matcher and path normalizer are now
written in Kelp, with the reviewed C versions kept as the reference the
differential tests compare against.

**Memory safety.** A valgrind gate over both backends is now part of the test
suite, and found: a one-eightbyte aggregate field or element loaded as a whole
`QWORD` (an invalid read past a heap block, invisible to a stdout comparison);
a temporary read through a field access that was not dropped; a `?` reached
with a pending operand that fell into the stack, fixed by rebuilding `rsp` from
`rbp` in the epilogue; and the forked child's `argv` leak in
`process.spawn_raw`.

**Also fixed.** `?` leaking a frame's drops; passdown forwarding; float literal
emission; chained `if let` re-moving its own scrutinee; `%` below 64 bits; a
zero-capacity `String`; a literal wider than its type; a `pd var` borrow is
shared unless the function writes it; a wrong-width aggregate load in the
assembly backend; the drop plan keyed by a block's identity instead of its
source span, so an owned local in a desugared `if let` or `for` block is no
longer dropped out of scope; a closure typedef that named a module type's
typedef before that type existed; and the C backend's warning noise, a doubled
parenthesis on every comparison and a tautological conversion bound.

**Stdlib.** `str.less` and `str.is_digit`: the byte ordering and decimal digit
predicate the libraries in the catalogue had each written by hand.

**Build.** `kelpc build` with no `-o` writes into `build/` instead of the
working directory. The crate moved to the 2024 edition.

**Known, not fixed here.** An owned local bound in a loop body is not dropped
on a path that does not move it, so a program that rebinds one leaks. It
predates this release and reproduces on the C backend at `-O0`.

## 0.1.4 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.4)
· 2 commits · 80 unit tests, 230 end-to-end green.

Five checker bugs, all found by compiling a real program: an 807-line JSON
library written with no access to the compiler source, built against 0.1.2 and
0.1.3. Every error it hit was the checker refusing ordinary code.

- **A view through a pattern binding keeps its provenance.** `if let Str(s) = v
  { return s.as_str() }` returns a view of `v`; the borrow root used to be the
  binding's *name*, so the same borrow was accepted as `v.x.as_str()` and
  refused as `s.as_str()`. Only borrow-typed bindings now carry their root, so
  tracing through an owned `x` still cannot pass a view of a local as a view of
  a parameter.
- **`panic` tails diverge for the borrow checker too**, not only for the type
  checker. One predicate, both passes.
- **`str` and `&str` are one type in arm unification**, so a `when` whose arms
  return `.as_str()` and a literal joins to the borrow.
- **A borrow inside an initializer ends with the statement**:
  `str.parse_i64(cand.as_str())` borrows `cand` for one call and keeps nothing
  of it. A binding that *is* the borrow still pins its owner.
- **A `Copy` value is never moved**, so a receiver method that names a field
  and then calls another method on `self` no longer reports "cannot move
  'self' while it is borrowed" about a pointer.

`borrow_provenance_and_arms.kp` pins all five.

**Known, not fixed here**: two code-generation bugs, both with a ~10-line
reproduction. An owned local in an `if let` block whose body holds a nested
`if let` with a `return` gets its drop call emitted but not its declaration;
and a `pd var` written in a function called transitively from another non-`main`
function passes a value where the callee's hidden parameter is a pointer.

## 0.1.3 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.3)
· 3 commits · 80 unit tests, 229 end-to-end green.

**A bare literal takes its sibling operand's type on either side.** The same
807-line JSON library failed its UTF-8 encoder with `operator requires matching
numeric operands, found 'i32' and 'u32'` on
`out.push((192 + cp / 64).to_u8())`. `syntax.md` §2.4 already promised that a
literal takes the integer type its context requires, but the checker read
operands left to right only, so a literal on the *left* was typed `i32` before
the right operand was looked at. One `check_binary_operands` now types both
sides; arithmetic, the bitwise operators and the comparisons all get it. A
`const` is deliberately **not** a literal for this rule: it has a declared type,
so `BASE + wide` stays a real mismatch.

`literal_operand_typing.kp` covers every width in both directions;
`literal_const_is_not_a_literal.kp` pins the rejection.

## 0.1.2 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.2)
· 10 commits · 80 unit tests, 227 end-to-end green.

The five gaps a real program found, plus the reference section that was
missing. Recorded as **MK8-S2-M1**.

- **`to_f64`/`to_f32` on every integer type**, so widening is one call instead
  of formatting the integer and parsing it back. Operands still must match
  exactly: `n * 1.0` remains a type error.
- **Character literals**: `'x'`, `'\n'`, `'\u{4e2d}'`. One Unicode scalar
  value, taking the integer type its context asks for (so `c == '"'` works when
  `c` is a `u8`) and `char` when nothing constrains it. A code point that does
  not fit is a compile error, not a truncation.
- **Bitwise operators**: `& | ^ << >> ~`. `&` is bitwise-and infix and the
  borrow prefix in prefix position; `<<` and `>>` are two adjacent characters,
  so `List<List<i32>>` still closes. Precedence is C's except that the bitwise
  operators bind tighter than the comparisons, so `flags & MASK == 0` means
  what it looks like.
- **`str` or `View` becomes an owned `String`** where one is expected: a call
  argument, a `datac` field, a `List` element, a `Map` key or value, a written
  type, a return, an `if` branch, a `when` arm. The other direction stays
  explicit, because `String` to `str` is a borrow with a lifetime.
- **`View`**: a length-carrying borrowed text view. `s.view()`, then
  `len`/`is_empty`/`get`/`slice`/`eq`/`to_string`. A slice costs a pointer and
  a subtraction instead of an allocation. It follows `str`'s rules exactly and
  is never a `datac` field, an `enum` payload, a `List` element or a `Map` key:
  a slice has no NUL after it, and v1 has no lifetime syntax to tie a stored
  borrow to its source.
- **CLI**: `kelpc version`.
- **Docs**: `syntax.md` §22, "Writing a program: the rules that explain most
  errors", with the eight rules behind most diagnostics plus a complete scanner.

## 0.1.1 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.1)
· 11 commits · 80 unit tests, 214 end-to-end green (every heap fixture also
rebuilt with `-fsanitize=address` and run).

The first release with a Gitea release attached; `v0.1.0` was left where it was.
This is the state of `main` after **MK5-S2-M2** and **MK8-S1-M3**.

- **The `for` loop** (MK8-S1-M3). `for x in xs { ... }` walks a `List<T>` front
  to back, desugared by the parser into an index and a `while`, so no later pass
  knows it exists. The element binding is what `List.get` gives: a copy of a
  `Copy` element, a shared borrow of an owned one. A place iterable is borrowed,
  not moved; anything else is bound to a temporary the loop owns and frees, so it
  is evaluated once. The loop variable is a `val`; there is no `break` and no
  `continue`. `for` walks a `List` and nothing else.
- **MK5-S2-M2, the three stdlib gaps a Coral port hit.**
  `process.spawn_in(dir, program, args)` and `process.run_in(...)` `chdir` in the
  *child* between `fork` and `exec`, so no capability pattern's meaning moves; a
  child that cannot enter `dir` exits 126. `process.try_run`/`try_run_in` return
  `Result<RunResult, ProcErr>` where `ProcErr` is `NotFound`, `NotExecutable` or
  `DirNotFound`, all decided by a `stat`/`access` pre-check **before** the fork, so
  an `Err` always means the child never started. `process.executable(path)` is
  that pre-check as public surface. `fs.symlink(target, link)` checks both paths
  against the module's `fs` grant.

**Limits worth knowing.** A capability *denial* cannot be a value yet: the check
is compiled in per calling module and panics before any Kelp code runs, so
`ProcErr` has no `Denied` variant. `std/http` speaks `http` only. No threads.
`kelpc` has no `--version` flag; the release name is the version.

## 0.1.0 (no release)

Tag `v0.1.0`, pointing at the **pre-rebase** history: it is not an ancestor of
any later release, and its tree is the same as `main` at *MK8-S1-M2 phase E*
apart from a deleted `rebrand.md`. No Gitea release was attached to it.

Everything up to that point, in the older milestone numbering the repository used
at the time (the `M0` to `M9`, `C1`, `S1` to `S8` scheme; the current scheme's
mapping is in `plan/roadmap.md`):

- **Core language** (`M0` to `M4.5`): scaffold and lexer/parser for the full
  surface syntax; types and the C backend; `datac` with real per-field
  mutability and `while`; spans through a typed IR; the syntax rewrite to
  `fun`/`val`/`var`/`datac`/`when`; move checking; borrowing (`&`, `mut T`
  parameters, `*`, aliasing checks); receiver methods.
- **Modules and compile-time** (`M5.1` to `M5.3`): `impl` imports with
  module-qualified names, `coral.toml`, `pd` passdowns, string templates, and
  `%*alias*%` text substitution.
- **Heap and containers** (`M6.1` to `M6.3`, `M8`, `C1`): owned `Bytes` and
  `String`, `drop`, `extern fun`, `std/mem`, `std/str`, `std/path`, `const`,
  stdlib-only overloading, `&str` return elision, `Box<T>` and recursive
  `datac`s, the builtin monomorphized `List<T>`, and `str.split`/`join` and
  `fs.list` on top of it.
- **Capabilities** (`M7`): `caps(...)` grants with a real `fs`/`time`/`rand`
  behind them, then `fs.append`/`fs.sync`.
- **The standard library program** (`S1` to `S5`): growable `String`/`Bytes`,
  `panic`/`assert`, integer conversions, text building and number formatting,
  the `List` ordering surface, `io` and `process`, `net` (sockets, `poll`, name
  resolution), the `http` client, `Map<K, V>`, and `fs`/`env` breadth.
- **Errors as values** (`MK5-S6-M1`): `enum` tagged unions with pattern `when`,
  generic type declarations and generic functions/methods with explicit type
  arguments, `Map<K, V>` with a real key type, `if let`, the `?` operator,
  `std/option` and `std/result`, and the migration of the stdlib off the
  error-`datac` convention.
- **Function values and closures** (`MK8-S1-M2` phases A to E): `move T`,
  function values, anonymous `fun` literals, the stdlib callbacks that take
  them, and captures, where a literal that captures is a closure.
- The language was renamed from **X** to **Kelp** in this stretch.

## Maintaining this page

This page carries **released versions only**. Nothing goes here until a version
is tagged.

Changes in the meantime accumulate in `kelp/CHANGELOG.pending.md`, which is
gitignored and never committed: add a line there when a user-visible change
lands, grouped under language, compiler, stdlib, fixes and limits.

When a version drops, write its entry here from that file plus the tag's commits
and the Gitea release body, then wipe the pending file back to its header. Cut it
the way `0.1.5` above is cut: the version and date, a link to the Gitea release,
the numbers (unit tests, end-to-end tests per backend), then what changed,
grouped so a reader can skip what they do not care about.

Keep it short. Link to `plan/done.md` for the full story rather than copying it.

Write the page without em dashes. Use a colon or a comma for an aside, a
semicolon or a full stop between clauses, and a plain hyphen in a range.

## See also

- [Roadmap](/meta/roadmap): what is planned, and what is in progress
- [Compiler](/compiler): the pipeline each entry changed
- [Coral changelog](/tooling/coral-changelog) and
  [Lighthouse changelog](/tooling/lighthouse-changelog): the other two repositories
