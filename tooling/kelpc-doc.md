---
title: "`kelpc doc`"
description: "The documentation generator: /// and //! comments, the options (-o, --format md|html, --private, --check, --std), what a page shows, deterministic output, its limits, and the lint warning for a doc comment attached to nothing."
isPublished: true
tags: "tooling, cli"
---
`kelpc doc` turns the comments above your declarations into a set of pages, one
per module plus an index. It reads the comments the lexer already keeps as
trivia, so it never changes how a program compiles, and it does not need the
program to compile: it scans tokens, not the checked program. Everything on this
page was run against the prebuilt compiler of the `main` branch on the machine
that wrote it; the plan behind it is
[`tooling/kelpc-doc.md`](/tooling/kelpc-doc).

```text
usage: kelpc doc <file.kp|project dir>... [-o <dir>] [--format md|html] [--private] [--check]
       kelpc doc --std [-o <dir>] [--format md|html] [--private] [--check]
```

## Writing doc comments

| Comment | Documents |
| --- | --- |
| a run of `///` lines directly above the item | a `fun`, `datac`, `enum`, `trait`, `pd`, `const`, `static` or `extern type`; an enum variant; a `datac` field; a trait method |
| a `//!` block before the first declaration | the module. Only `impl "..."` lines may come before it |
| `////` | nothing: it is an ordinary comment |

The text is plain Markdown-ish prose. Lines starting with `- ` stay a list, and a
backticked name that matches exactly one type or trait among the documented
modules becomes a link to it.

A comment on a `datac` documents that type only. Fields inherit no text: give a
field its own `///` block when it needs a description, and it is otherwise shown
without one.

A module to document, `ledger.kp`:

```kelp
//! A tiny ledger: sums of money kept in whole cents.
//!
//! `Entry` is one line, and `total` adds a list of them.
impl "std/list"

/// One line in a ledger.
///
/// - `cents` is signed: a refund is negative
pub datac Entry(
    /// What the line was for.
    val label: String,
    /// The amount in cents.
    val cents: i64
)

/// How a ledger reads an amount.
pub enum Sign {
    /// Money in.
    Credit
    /// Money out.
    Debit
}

/// Adds up the `cents` of every `Entry` in `entries`.
pub fun total(entries: &List<Entry>) => i64 {
    var sum: i64 = 0
    for e in entries {
        sum = sum + e.cents
    }
    return sum
}

/// Says whether an `Entry` is money in or money out.
fun Entry.sign() => Sign {
    if self.cents < 0 {
        return Sign.Debit
    }
    return Sign.Credit
}

fun helper() {
}

fun main() {
    var es: List<Entry> = List.empty()
    es.push(Entry(label = "pay", cents = 500))
    print(total(&es))
}
```

(`Entry.sign` has no `pub` because a method cannot be marked `pub`: it follows
its type. `helper` and `main` are private and have no doc.)

## Running it

The generator puts a dash between each name and its summary. The examples on this
page write a colon there instead, so that no output here carries a dash.

```text
$ kelpc doc ledger.kp -o out-md; echo "rc=$?"
rc=0
$ ls out-md
index.md  ledger.md
$ cat out-md/index.md
# Modules

- [`ledger`](ledger.md): A tiny ledger: sums of money kept in whole cents.
```

A successful run prints nothing. `out-md/ledger.md`, exactly as written:

````text
# Module `ledger`

A tiny ledger: sums of money kept in whole cents.

[`Entry`](#entry) is one line, and `total` adds a list of them.

## Imports

- `impl "std/list"`

## Types

### `Entry`

```kelp
pub datac Entry(val label: String, val cents: i64)
```

One line in a ledger.

- `cents` is signed: a refund is negative

**Fields**

- `val label: String`: What the line was for.
- `val cents: i64`: The amount in cents.

#### `Entry.sign`

```kelp
fun Entry.sign() => Sign
```

Says whether an [`Entry`](#entry) is money in or money out.

### `Sign`

```kelp
pub enum Sign
```

How a ledger reads an amount.

**Variants**

- `Credit`: Money in.
- `Debit`: Money out.

## Functions

### `total`

```kelp
pub fun total(entries: &List<Entry>) => i64
```

Adds up the `cents` of every [`Entry`](#entry) in `entries`.
````

`helper` and `main` are not there: only `pub` items are listed. The `Entry` and
`Sign` mentions in the prose became links, and `Entry.sign` appears under its
type because a method of a public type is listed with the type.

## Options

| Option | Effect |
| --- | --- |
| `<file.kp>` | document one file; its module id is its file stem |
| `<project dir>` | document a project's `src/`; a module's id is its path relative to `src/` |
| `-o <dir>` | the output directory, `doc` by default, created if missing |
| `--format md\|html` | Markdown (the default) or HTML; any other value is refused (`error: '--format' takes 'md' or 'html', found 'pdf'`) |
| `--private` | list private items too, not only `pub` ones |
| `--check` | write nothing; exit 1 when a listed item lacks a doc |
| `--std` | document the shipped standard library instead of your files |

Several paths may be given at once; each file or project contributes its modules
to the same index, and a missing path stops the run with
`error: cannot read 'nope.kp': No such file or directory (os error 2)` and exit 1.

A project directory's modules are named by path, and the file name replaces the
slash with a dot:

```text
$ kelpc doc kelpc/tests/docs/project -o o4
$ ls o4
index.md  main.md  util.text.md
```

`--std` names its pages the same way (`std.str.md`, `std.fs.md`, and so on for
every shipped module). The shipped modules have no `pub`, so `--std` lists
everything except `extern fun`s.

### `--private`

The same `ledger.kp` with `--private` differs from the default in exactly the two
functions the default left out:

```text
$ kelpc doc ledger.kp --private -o out-priv
$ diff out-md/ledger.md out-priv/ledger.md
50a51,62
> ### `helper`
>
> ```kelp
> fun helper()
> ```
>
> ### `main`
>
> ```kelp
> fun main()
> ```
>
```

### `--format html`

HTML output is one self-contained file per module (a small inline stylesheet that
follows the reader's light or dark preference, no scripts) and an `index.html`.
Anchors are ids on the headings, so `#entry` works in either format.

```text
$ kelpc doc ledger.kp --format html -o out-html
$ ls out-html
index.html  ledger.html
```

The body of `ledger.html` carries the same content as the Markdown, for example:

```html
<h3 id="entry"><code>Entry</code></h3>
<pre><code>pub datac Entry(val label: String, val cents: i64)</code></pre>
<p>One line in a ledger.</p>
```

### `--check`

`--check` is for CI. It writes no page, prints one line per undocumented item as
`file:line: <what> has no doc comment`, and exits 1 if there was any. It checks
every item a page would list, and also each field, variant and trait method; it
does not require docs on associated types or on methods inside an `impl` block.

```text
$ cat bad.kp
/// Documented.
pub fun good() {
}

pub fun bad() {
}
$ kelpc doc bad.kp --check; echo "rc=$?"
bad.kp:5: public fun `bad` has no doc comment
rc=1
$ kelpc doc ledger.kp --check; echo "rc=$?"
rc=0
```

## What a page shows

Each module page, in order, has:

- the `//!` text as the introduction;
- **Imports**: the module's `impl` lines, with their `caps(...)` clauses;
- sections for **Types** (`datac` and `enum`, with their fields or variants),
  **Traits**, **Functions**, **Constants** and **Statics**, each item with its
  signature, the doc text, and for a type the receiver methods and the
  `impl Trait for Type` blocks found for it;
- the signature is what `kelpc fmt` prints, collapsed onto one line, so a
  multi-line `datac` header reads as one;
- `unsafe` is shown on an `unsafe fun` (`*unsafe*`);
- a `*requires capability `fs`*` note on a function that sits in a gated standard
  module (`std/fs` holds the `fs` domain) or whose body names a gated import
  directly.

Those last two, from the compiler's own test module `kelpc/tests/docs/shapes.kp`:

````text
### `load`

```kelp
pub fun load(path: &str) => String
```

*requires capability `fs`*

Reads a file named by `path`.

### `make`

```kelp
pub unsafe fun make(r: f64) => Circle
```

*unsafe*

Makes a circle from a radius.
````

## Deterministic output

The same input gives the same bytes: items are sorted, there is no timestamp, no
absolute path and no environment in a page. Running the command twice and
comparing the two directories:

```text
$ kelpc doc ledger.kp -o out-md
$ kelpc doc ledger.kp -o out-md2
$ diff -r out-md out-md2 && echo identical
identical
```

So generated docs can be committed and a diff of them means something changed.

## Limits

- **A `datac` field written on the same line as its `datac(` cannot carry its own
  doc.** Put one field per line, as `Entry` does above. The page still lists the
  field, just without text, and the comment is reported by `kelpc lint` as
  attached to nothing:

  ```text
  $ cat same.kp
  /// A pair.
  pub datac P(/// the x
   val x: i32, val y: i32)
  $ kelpc doc same.kp -o o3 && sed -n 13,16p o3/same.md
  **Fields**

  - `val x: i32`
  - `val y: i32`
  $ kelpc lint same.kp
  warning: this '///' documents nothing: a doc comment must sit directly above a fun, datac, enum, trait, pd, const, static, extern type, enum variant, field or trait method
    --> same.kp:2:13
  ```

- **Capability notes are direct references only.** A function gets
  `requires capability` when it sits in a gated module or its own body names a
  gated import; a function that merely calls one that does is not marked.
- Signatures come from the formatter when the formatted file has the same shape
  as the source; the tool reads tokens, so it does not resolve types, aliases or
  calls, and documents code that does not type check (it listed
  `pub fun Entry.sign` from a draft of `ledger.kp` that `kelpc run` itself
  refuses).

## The lint warning

A doc comment that sits above nothing a page can attach it to (a `val` inside a
function body, or a stray block) is a `kelpc lint` **warning**, never an error, so
older code that used `///` or `//!` as an ordinary comment still compiles. From
the compiler's `kelpc/tests/docs/orphan.kp`:

```text
$ kelpc lint kelpc/tests/docs/orphan.kp; echo "rc=$?"
warning: this '///' documents nothing: a doc comment must sit directly above a fun, datac, enum, trait, pd, const, static, extern type, enum variant, field or trait method
  --> kelpc/tests/docs/orphan.kp:1:1
warning: this '///' documents nothing: a doc comment must sit directly above a fun, datac, enum, trait, pd, const, static, extern type, enum variant, field or trait method
  --> kelpc/tests/docs/orphan.kp:4:5
rc=0
```

Both findings are reported and the exit status stays 0, like every `lint` warning
(see [`lint`](/tooling/kelpc-cli#lint)). To keep the text as a plain comment, write
`//` (or `////`).

## The standard library

Twelve standard modules (`str list option result fs io net http sync time math
env`) carry a `//!` header and a doc on every function, and `kelpc doc --std`
renders all of the shipped modules (32 pages and an index when this page was
written).

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Tooling](/tooling)
- [Style](/language/style)
