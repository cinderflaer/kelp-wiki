---
title: "`std/env`"
description: "Environment variables. Gated on env."
isPublished: true
tags: "stdlib"
---
Environment variables. **Gated on `env`.**

```kelp
impl "std/env" with caps(env = ["NO_COLOR"])   // one name
impl "std/env" with caps(env = ["APP_*"])      // a prefix
impl "std/env" with caps(env = ["*"])          // anything
```

| Function | Returns | Notes |
| --- | --- | --- |
| `env.has(name: &str)` | `bool` | presence, not value |
| `env.get(name: &str)` | `String` | panics when unset |
| `env.set(name: &str, value: &str)` | `Unit` | |
| `env.unset(name: &str)` | `Unit` | |

```kelp
impl "std/env"

fun main() {
    if env.has("HOME") {
        print(env.get("HOME"))
    }
    env.set("KELP_DEMO", "1")
    print(env.has("KELP_DEMO"))
    env.unset("KELP_DEMO")
    print(env.has("KELP_DEMO"))
}
```

## Notes

- There is **no listing**: a program cannot enumerate the environment. That is
  the capability model doing its job: a grant names the variables it may read, so
  "which variables exist?" is not a question the language lets you ask.
- `get` panics on an unset name; check `has` first unless a missing variable is a
  bug.
- The variable's *presence* is what `has` reports, which is exactly what the
  [no-color.org](https://no-color.org) convention needs:
  [`term`](/libraries/term) tests `env.has("NO_COLOR")` and ignores the
  value.

## See also

- [`term`](/libraries/term): the one library that reads `NO_COLOR`
- [Capability patterns](/reference/capability-patterns)
