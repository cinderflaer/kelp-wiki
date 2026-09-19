---
title: "config_load"
description: "Reads settings from a manifest-shaped text and pulls typed values out of it, which is what a tool does with coral.toml before it does anything else."
isPublished: true
tags: "example, data-formats"
---
Reads settings from a manifest-shaped text and pulls typed values out of it, which
is what a tool does with `coral.toml` before it does anything else.

| | |
| --- | --- |
| Source | [`src/config_load.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/config_load.kp) |
| Needs | `config` |
| Shows | the TOML subset the manifest format uses, typed accessors, defaults, and why `1.5` is text |

## The dependency

```toml
[dependencies]
config = "Juniper/fpl/config"
```

The text is in the program so the example runs with no file. In a tool the same
call reads a path:

```kelp
val text = fs.read_text(path.as_str())
val parsed = config.parse(text.as_str())
```

## The program

```kelp
impl "deps/config/lib" as config
impl "std/str"

// Every owned local lives here rather than in `main`: one declared inside an
// `if let` arm does not build yet (see Known issues), and these are `String`s.
fun show(cfg: &config.Config) {
    val name = config.get_str(cfg, "", "name")
    print(str.concat("config     name = ", name))

    print("config     count = ${config.get_int(cfg, "", "count")}")
    print("config     has(name) = ${config.has(cfg, "", "name")}")

    // 1.5 is not an integer, so it is stored as the text it was written as.
    val ratio = config.get_str(cfg, "", "ratio")
    print(str.concat("config     ratio is text: ", ratio))

    val host = config.get_str(cfg, "server", "host")
    print(str.concat("config     server.host = ", host))

    val features = config.get_array(cfg, "server", "features")
    print("config     features = ${features.len()} entries")

    // Accessors with defaults do not panic on a missing or wrong-typed key.
    val fallback = config.get_str_or(cfg, "", "missing", "unset")
    print(str.concat("config     missing = ", fallback.as_str()))
    print("config     missing int = ${config.get_int_or(cfg, "", "missing", -1)}")
    print("config     a text value read as int falls back = ${config.get_int_or(cfg, "", "ratio", -1)}")

    // The entries are flat, so the section is part of the key.
    print("config     entries = ${cfg.entries.len()}")
}

fun main() {
    val text = "# a project\nname = \"demo\"\ncount = 7\nratio = 1.5\n\n[server]\nhost = \"127.0.0.1\"\nfeatures = [\"a\", \"b\"]  # trailing comment\n"

    val parsed = config.parse(text)
    if let Ok(cfg) = parsed {
        show(cfg)
    }
}
```

## Run it

```sh
kelpc run config_load.kp
```

## Output

```
config     name = demo
config     count = 7
config     has(name) = true
config     ratio is text: 1.5
config     server.host = 127.0.0.1
config     features = 2 entries
config     missing = unset
config     missing int = -1
config     a text value read as int falls back = -1
config     entries = 5
```

## What to take from it

- **Only two value types are recognised: quoted strings and integers.** A float,
  a boolean or a bare word is stored as the text it was written as, so `ratio` is
  the string `1.5`, not a number. A tool that wants a float parses it itself with
  `str.parse_f64`.
- **Arrays are arrays of quoted strings,** comma-separated, with whitespace around
  a comma ignored. `get_array` panics if the value is not one.
- **The section is part of the key at the root,** which is the empty string: the
  accessors take `(section, key)` and the entries are flat, so `""` and `"server"`
  are the two names in play here.
- **`_or` accessors do not panic.** `get_str_or` and `get_int_or` return the
  fallback when the key is missing *or* the type is wrong, which is the difference
  between them and `get_str`/`get_int`.
- **A comment is stripped outside a quoted string only,** so a `#` inside quotes
  survives.
- **`cfg.entries` is the flat list of everything parsed,** which is how a tool
  reports what it read without knowing the keys in advance.
- **The helper function is the `if let` workaround again.** Owned locals belong
  outside the arm, and this is the third example in the chapter that has to say so
  (see [Known issues](/meta/known-issues) BUG-1).

## See also

- [`config`](/libraries/config) for the reader in full, including the lower-level entry points
- [Projects and coral.toml](/getting-started/projects) for the manifest this format comes from
- [Known issues](/meta/known-issues)
