---
title: "Writing a library"
description: "A Kelp library has no manifest, no version, no build step and no artifact. What a consumer needs from it is a folder in a git repo."
isPublished: true
tags: "library"
---
A Kelp library has no manifest, no version, no build step and no artifact. What a
consumer needs from it is **a folder in a git repo**.

## The shape

```
mylib/
    lib.kp            # the entry file — the consumer names it, so the name is a convention
    ...               # any other .kp files lib.kp imports
```

```kelp
impl "std/str"
impl "std/result"

pub datac Item(val name: String, val count: i64)

pub fun parse(text: &str).R: result.Result<List<Item>, ParseErr> { ... }
```

And in a consumer:

```toml
[dependencies]
mylib = "Juniper/mylib"            # the whole repo
other = "Juniper/fpl/other"        # one folder inside a repo
local = "file:///srv/git/fpl#third" # a full URL, folder after '#'
```

```kelp
impl "deps/mylib/lib"
```

The consumer's `impl` path is always `deps/<manifest-name>/<entry-file>`, because
a folder dependency lands **flat**: the *contents* of the folder you named go to
`src/deps/<name>/`. The clone behind it uses `--filter=blob:none --sparse`, so a
sibling folder in the same repo never comes down, which is exactly why rule 3
below is a rule.

## The five rules

1. **One folder is one library.** Its files are what a consumer gets. Nothing
   outside the folder is available, so the folder has to be self-contained.
2. **The entry file has no fixed name.** `lib.kp` is the convention; the consumer
   writes the path, so whatever they name is the entry.
3. **A folder cannot `impl` a sibling.** Not a style rule: the sibling was never
   fetched. Two libraries that genuinely share code become one folder, or the
   *consumer* declares both and wires them together.
4. **A library declares its own capabilities.** A library's own
   `impl "std/fs" caps(...)` is the grant it needs; the consumer's manifest
   grants it nothing. A JSON library holds no authority; a library that reads
   files asks for it where the read is written, and the consumer decides the
   pattern at its own `impl` line.
5. **An `index.toml` or a README table is metadata for humans.** Coral does not
   read either: the manifest's folder path is the name.

## Constraints the language puts on a library

- **A consumer reaches the entry file's items only when they are `pub`.**
  Another module reaches a `fun`, `extern fun`, `datac`, `enum` or `const` that
  carries `pub`, and nothing else (A-13), so the surface a consumer calls is the
  surface the library marks. A method follows its declaring type: `pub` on the
  type exports the methods a value of it carries, and `pub` on a method is
  refused. A `pd` never takes `pub`, because a passdown is module-scoped.
- **A user module cannot overload a name**, which is why `listx` spells the type
  into the function (`sum_i32`, `min_f64`) and why `set` ships two types
  (`Set<T>` and `StrSet`) where the standard library would overload one.
- **The container element sets are narrow.** A `List` element and a `Box`
  element may be a `List` or a `Box`, but a `Map` value and an array element may
  not be a container, and no container takes a borrow, a view or an atomic. A
  library that puts a list inside a map, or wants a named row, wraps it in a
  one-field `datac`: `csv.Row`, `listx.Chunk` and `table.Row` are exactly that.
- **A closure parameter that borrows a module-declared type codegens**, so a
  library may take a callback over its own type: `json` ships
  `each_value`/`filter_array`.
- **An owned payload comes out of an owned place, not out of a borrow.** A
  parameter of an owned type is a borrow, so a library's "unpack" helper either
  takes the value with `move` and hands the payload out (`option.unwrap`), or
  returns the payload inside an `Option`/`Result` (`result.map`) and lets the
  caller match an owned local. A helper that only has a borrow fills an `out`
  parameter and returns `bool` (the shape `std/io`'s `read_line_into` uses)
  instead of returning `Option<String>`.

## Adding one to `fpl`

1. Add the folder with its `.kp` source (entry `lib.kp`).
2. Add a row to the repository's root `README.md` table and to `index.toml`.
3. Add a page to this chapter.
4. Push. That *is* publishing: there is no version to bump.

## Releases, and when a library goes on a branch

The `main` of `fpl` is what a consumer gets, and it has to build against the
**released** compiler: `coral sync` fetches a dependency from the remote's tip,
and `coral.toml` cannot name a branch (`coral/src/deps.rs` parses a dependency
into a URL and a folder, and nothing else). There is no way for a consumer to opt
out of `main`, so a `main` that needs an unreleased compiler breaks every one of
them.

That is why a release pulls its libraries with it, on a branch:

- When a new language version is being worked on, a library the change touches is
  updated for it **at once**, on `fpl`'s `unreleased` branch, in the same session
  as the language change. `kelp-wiki` already works this way, and so do `coral`
  and `lighthouse` when a change reaches them.
- `main` keeps building against the released compiler until the release lands.
- At the release, each `unreleased` branch merges into `main` and both are pushed.
  One merge per repository.
- A change that needs **no** unreleased compiler is not release-coupled: a new
  library, a new function, a documentation fix. Those go straight to `main`,
  because they are what a consumer can use today.

## See also

- [Libraries (fpl)](/libraries)
- [Catalogue](/libraries/catalogue)
- [Projects and coral.toml](/getting-started/projects)
