---
title: "`glob`: `*`/`?` pattern matching"
description: "A public glob matcher over  and ? -  matches any run of characters (including none), ? matches exactly one, everything else matches itself literally."
isPublished: true
tags: "library, filesystem"
---
A public glob matcher over `*` and `?`: `*` matches any run of characters
(including none), `?` matches exactly one, everything else matches itself
literally.

No capability. (The compiler's own capability matcher lives in `std/rt` and
implements the same shape; it is the compiler's runtime module rather than a
library to reach for, and this is the importable version.)

```toml
[dependencies]
glob = "Lilly/fpl/glob"
```

```kelp
impl "deps/glob/lib"
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `glob_match(pattern: &str, text: &str)` | `bool` | byte-wise, not Unicode-aware: `?` is one byte |
| `glob_filter(pattern: &str, xs: &List<String>)` | `List<String>` | the elements `glob_match` accepts, in order, each cloned |

## Semantics

- `*` matches the empty string: `glob_match("a*", "a")` is true.
- A pattern with no wildcards is an equality test.
- `glob_match("", "")` is true; `glob_match("*", "")` is true.
- There is no `**` (path-spanning), no character class `[abc]`, no brace
  expansion, no escape character. `/` is an ordinary character, so `*.kp` also
  matches `dir/main.kp`.

## Cost

The classic O(len(pattern) × len(text)) DP table, flattened to one
`List<bool>` and indexed by `row * cols + col`.

## Example

```kelp
impl "deps/glob/lib"

fun main() {
    print(glob.glob_match("*.kp", "main.kp"))
    print(glob.glob_match("a*c", "abbbc"))
    print(glob.glob_match("a?c", "abc"))
    print(glob.glob_match("a?c", "ac"))
    print(glob.glob_match("*", ""))
    print(glob.glob_match("", ""))
    var xs: List<String> = List.empty()
    xs.push("a.kp")
    xs.push("b.txt")
    xs.push("c.kp")
    val kept = glob.glob_filter("*.kp", xs)
    print(kept.len())
    print(kept.get(0).as_str())
}
```

Output:

```
true
true
true
false
true
true
2
a.kp
```

## Notes

- `?` counts bytes, so it does not match one multi-byte UTF-8 character.
- `glob_filter` clones each kept element, because a `List` only lends its
  elements by reference.
- There is no directory walk here; combine it with `std/fs.walk` or
  `fsx` to filter a tree.
