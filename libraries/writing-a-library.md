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

datac Item(val name: String, val count: i64)

fun parse(text: &str).R: result.Result<List<Item>, ParseErr> { ... }
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

- **A user module cannot overload a name**, which is why `listx` spells the type
  into the function (`sum_i32`, `min_f64`) and why `set` ships two types
  (`Set<T>` and `StrSet`) where the standard library would overload one.
- **`List` and `Map` cannot nest directly**, so a nested container is wrapped in a
  one-field `datac`: `csv.Row`, `listx.Chunk` and `table.Row` are exactly that.
- **A closure parameter that borrows a module-declared type codegens**, so a
  library may take a callback over its own type: `json` ships
  `each_value`/`filter_array`.
- **`Option`/`Result` payloads cannot be moved out of a `Copy`-less enum**, which
  is why a library's "unpack" helpers take an `out` parameter and return `bool`
  (the shape `std/io`'s `read_line_into` uses) rather than returning
  `Option<String>`.

## Adding one to `fpl`

1. Add the folder with its `.kp` source (entry `lib.kp`).
2. Add a row to the repository's root `README.md` table and to `index.toml`.
3. Add a page to this chapter.
4. Push. That *is* publishing: there is no version to bump.

## See also

- [Libraries (fpl)](/libraries)
- [Catalogue](/libraries/catalogue)
- [Projects and coral.toml](/getting-started/projects)
