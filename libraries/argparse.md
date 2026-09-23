---
title: "`argparse`: flags, options, positionals and `--help` text"
description: "Parses a plain List<String> (typically process.args(), but the list is a parameter, so the library stays ungated and works standalone too), plus one typed value: a byte count with a k/m/g/t suffix."
isPublished: true
tags: "library, cli"
---
Parses a plain `List<String>` (typically `process.args()`, but the list is a
parameter, so the library stays ungated and works standalone too).

No capability.

```toml
[dependencies]
argparse = "Juniper/fpl/argparse"
```

```kelp
impl "deps/argparse/lib"
```

## The one convention

- `--name` is a **boolean flag** (present or not). A flag never takes a value.
- `--name=value` and `--name value` are both accepted for a declared
  **option**. An option always takes a value.
- There are **no short flags** (`-v`) and no subcommands. A subcommand is just
  the first positional; re-parse the rest with a second `Parser` if you want one
  per subcommand. Anything not starting with `--` is a positional.

The convention is chosen for being the least ambiguous to scan without
backtracking.

## Types

```kelp
datac FlagSpec(val name: String, val help: String)
datac OptionSpec(val name: String, val default: String, val help: String)
datac Parser(val prog: String, var flags: List<FlagSpec>, var options: List<OptionSpec>)

datac SetOption(val name: String, val value: String)
datac ParsedArgs(val set_flags: List<String>, val option_values: List<SetOption>, val positionals: List<String>)

enum ParseErr {
    UnknownFlag(val name: String)
    MissingValue(val name: String)
}
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `new(prog: &str)` | `Parser` | bind with `var`: `add_*` mutates it |
| `add_flag(p: mut Parser, name: &str, help: &str)` | `Unit` | |
| `add_option(p: mut Parser, name: &str, default: &str, help: &str)` | `Unit` | `default` is what `get_option` returns when unset |
| `parse(p: &Parser, args: &List<String>)` | `result.Result<ParsedArgs, ParseErr>` | unknown `--name`, or a `--name` option with no following token, is an error |
| `has_flag(pa: &ParsedArgs, name: &str)` | `bool` | |
| `get_option(p: &Parser, pa: &ParsedArgs, name: &str)` | `String` | explicitly set value, else the declared default. **Panics** `argparse.get_option: 'name' was never declared with add_option`. That is a caller bug, not user input |
| `positionals(pa: &ParsedArgs)` | `&List<String>` | every token that was not `--…` |
| `help_text(p: &Parser)` | `String` | rendered usage, flags and options |
| `err_name(e: &ParseErr)` | `&str` | the offending name |
| `err_message(e: &ParseErr)` | `String` | `unknown flag or option: --x` / `--x needs a value` |

`get_option` returns an owned `String`, not a `&str`: the value may come from
`pa` or from `p`'s default, and a borrow-returning function can only return
something derived from its *first* reference parameter (syntax.md §10.2).

Inspection helpers: `is_known_flag(p: &Parser, name: &str) -> bool` and
`is_known_option(p: &Parser, name: &str) -> bool`, for checking a name before
`parse` or for building your own scanner. `parse_long_token` is the internal
one-token step; it builds each `ParseErr` value directly from the token text, so
nothing is rebuilt from a borrow.

## `--name value` and `--name=value`

For a declared option, `--name value` consumes the next token even when that
token starts with `--`. A `--name` token that matches no flag and no option is
`UnknownFlag`; use `--name=value` when the value itself begins with `--`.

## `help_text` shape

```
usage: <prog> [flags] [options] [args]

flags:
  --<name>\t<help>

options:
  --<name>=<value> (default: <default>)\t<help>
```

Sections with no entries are omitted. A trailing newline is included.

## Example

```kelp
impl "deps/argparse/lib"

fun main() {
    var p = argparse.new("demo")
    argparse.add_flag(p, "verbose", "print more")
    argparse.add_option(p, "output", "out.txt", "where to write")
    print(argparse.help_text(&p))

    var args: List<String> = List.empty()
    args.push("--verbose")
    args.push("--output=result.txt")
    args.push("input.kp")
    args.push("second.kp")
    val parsed = argparse.parse(&p, args)
    if let Ok(pa) = parsed {
        print(argparse.has_flag(pa, "verbose"))
        print(argparse.get_option(&p, pa, "output"))
        print(argparse.positionals(pa).len())
        print(argparse.positionals(pa).get(0).as_str())
    }

    var defaults: List<String> = List.empty()
    defaults.push("only-this.kp")
    val parsed2 = argparse.parse(&p, defaults)
    if let Ok(pa) = parsed2 {
        print(argparse.has_flag(pa, "verbose"))
        print(argparse.get_option(&p, pa, "output"))
    }

    var bad: List<String> = List.empty()
    bad.push("--nope")
    val failed = argparse.parse(&p, bad)
    if let Err(e) = failed {
        print(argparse.err_name(e))
        print(argparse.err_message(e))
    }

    var missing: List<String> = List.empty()
    missing.push("--output")
    val failed2 = argparse.parse(&p, missing)
    if let Err(e) = failed2 {
        print(argparse.err_name(e))
        print(argparse.err_message(e))
    }
}
```

Output:

```
usage: demo [flags] [options] [args]

flags:
  --verbose	print more

options:
  --output=<value> (default: out.txt)	where to write

true
result.txt
2
input.kp
false
out.txt
nope
unknown flag or option: --nope
output
--output needs a value
```

## Typed values

`get_option` hands back a `String`, which is the convention this library states.
A byte count is the one conversion almost every command line needs, so it lives
here rather than in every consumer.

| Function | Returns | Notes |
| --- | --- | --- |
| `parse_bytes(text: &str)` | `result.Result<u64, str.ParseErr>` | a byte count with an optional binary suffix: `512`, `4k`, `4kb`, `1m`, `2g`, `1t`. Case is ignored, a trailing `b` means bytes. `Err(Empty)` when there are no digits at all, `Err(Invalid)` otherwise |
| `get_bytes(p, pa, name, default: u64)` | `result.Result<u64, str.ParseErr>` | `parse_bytes` on a declared option; `default` stands in only when the resolved text is empty, which is the option not given with an empty declared default, or given as `--name=`. Any other text, the declared default included, is parsed, so `4k` gives 4096 and `out.txt` is an `Err` |

A value that *was* given and does not parse is still an `Err`, so a caller can
tell "unset" from "bad":

```kelp
val limit = argparse.get_bytes(p = &p, pa = pa, name = "min-size", default = 0)
if let Err(_) = limit {
    print("--min-size wants a byte count like 4k")
    process.exit(2)
}
if let Ok(n) = limit {
    print(n)
}
```

`str.ParseErr` carries no detail (it is `Empty` or `Invalid`), so the message is
the caller's: the two cases are worth one line each, and a library cannot know
what the flag was called.

## Notes

- Everything else is a `String`: a flag or option outside `get_bytes` has no
  typed parsing here, so a numeric option is `str.parse_i64` on the
  `get_option` result.
- A flag given twice stays once in `set_flags` per occurrence (`has_flag` is a
  scan); an option given twice keeps both `SetOption` entries and `get_option`
  returns the first.
- `--` (bare) is treated as an option token with an empty name and errors as
  `UnknownFlag`. There is no end-of-options separator.
- `help_text` is text only: the library never prints, and never exits. A caller
  decides what `--help` does.
