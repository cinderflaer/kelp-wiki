---
title: "`config`: TOML/INI-ish reader"
description: "A small flat config reader - key = \"value\" pairs, [section] tables, arrays of strings, bare tokens, # comments. It is deliberately the subset coral.toml itself uses - one key = value per line,..."
isPublished: true
tags: "library, data-formats"
---
A small flat config reader: `key = "value"` pairs, `[section]` tables, arrays
of strings, bare tokens, `#` comments. It is deliberately the subset
`coral.toml` itself uses: one `key = value` per line, blank lines free.

No capability.

```toml
[dependencies]
config = "Lilly/fpl/config"
```

```kelp
impl "deps/config/lib"
```

## Values

```kelp
enum Value {
    Str(val value: String)
    Int(val value: i64)
    Arr(val items: List<String>)
}

datac Entry(val section: String, val key: String, val value: Value)
datac Config(val entries: List<Entry>)
```

The root section is the empty string `""`. There is no nesting: a `[section]`
header only changes the section the following keys land in.

How a right-hand side is parsed:

| Written | Becomes |
| --- | --- |
| `"text"` | `Value.Str`, with `\n` and `\t` translated; the string must be exactly one quoted string with nothing after it |
| `[..]` | `Value.Arr` of quoted strings, comma-separated, whitespace around commas ignored |
| an integer that `str.parse_i64` accepts (`7`, `-3`) | `Value.Int` |
| anything else (`1.5`, `true`, `bare`) | `Value.Str` of the trimmed raw text |

`#` starts a comment **outside** a quoted string, so `key = "# not a comment"`
keeps its `#`.

## Parsing

| Function | Returns |
| --- | --- |
| `parse(text: &str)` | `result.Result<Config, ParseErr>` |

```kelp
enum ParseErr {
    MalformedLine     // no '=' in a non-blank, non-section line
    UnterminatedString
    UnterminatedArray
    EmptyKey          // '=' with nothing before it
    BadSection        // a '[' line without a closing ']'
}
```

`parse` splits on `\n`, so a trailing newline produces one final blank line and
that is free. The first failing line stops the parse.

## Accessors

| Function | Returns |
| --- | --- |
| `find_entry(cfg, section, key)` | `option.Option<usize>`: the entry position |
| `has(cfg, section, key)` | `bool` |
| `get(cfg, section, key)` | `&Value`; panics `config.get: key not found` |
| `get_str` / `get_int` / `get_array` | the typed value; panics when the key is absent or the type is wrong |
| `get_str_or(cfg, section, key, fallback: &str)` | `String` |
| `get_int_or(cfg, section, key, fallback: i64)` | `i64` |
| `is_str(v)` / `is_int(v)` / `is_array(v)` | `bool` |
| `as_str(v)` / `as_int(v)` / `as_array(v)` | the typed payload; panics with `config.as_str: value is not a string` and friends |

The `_or` forms return the fallback when the key is absent **or** the value has
the wrong type, so `get_int_or` on `ratio = 1.5` gives the fallback, not an
error.

## Lower-level entry points

The scanner is usable on its own if you are parsing something larger than one
file:

| Function | Returns | Notes |
| --- | --- | --- |
| `strip_comment(line: &str)` | `String` | the line with a `#` comment removed, quotes honoured |
| `parse_line(raw: &str, section: mut String, entries: mut List<Entry>)` | `option.Option<ParseErr>` | one line; a `[section]` header updates `section` in place. `None` means success |
| `parse_kv(section: &str, key: &str, raw_value: &str, entries: mut List<Entry>)` | `option.Option<ParseErr>` | one already-trimmed value |
| `parse_quoted_into(s: &str, out: mut String)` | `bool` | fills `out`; `false` on a malformed string, `out` may hold a partial decode |
| `parse_array_into(inner: &str, out: mut List<String>)` | `bool` | the text between `[` and `]` |
| `translate_escape(e: u8)` | `u8` | `n` -> newline, `t` -> tab, anything else itself |
| `is_ws_byte(c: u8)` | `bool` | space or tab |
| `copy_err(e: &ParseErr)` | `ParseErr` | rebuilds a payload-less variant; the receiver is a borrow, so nothing can be moved out of it |

## Example

```kelp
impl "deps/config/lib"

fun main() {
    val text = "# a comment\nname = \"demo\"\ncount = 7\nratio = 1.5\n\n[server]\nhost = \"127.0.0.1\"\nfeatures = [\"a\", \"b\"]  # trailing\n"
    val parsed = config.parse(text)
    if let Ok(cfg) = parsed {
        print(config.get_str(cfg, "", "name"))
        print(config.get_int(cfg, "", "count"))
        print(config.get_str(cfg, "", "ratio"))
        print(config.get_str(cfg, "server", "host"))
        val feats = config.get_array(cfg, "server", "features")
        print(feats.len())
        print(config.get_str_or(cfg, "", "missing", "fallback"))
        print(config.get_int_or(cfg, "server", "missing", 9))
        print(config.has(cfg, "server", "host"))
        val v = config.get(cfg, "", "count")
        print(config.is_int(v))
    }
}
```

Output:

```
demo
7
1.5
127.0.0.1
2
fallback
9
true
true
```

## Limits

- One level deep: `[a.b]` is not a nested table, it is a section literally named
  `a.b`, and `key.sub = 1` is a key named `key.sub`.
- No booleans, floats, dates or multiline strings. `1.5` and `true` are strings.
- No duplicate detection: two entries with the same section and key both live in
  `entries` and `find_entry` returns the first.
- The quoted-string and array readers fill an `out` parameter and return `bool`
  rather than wrapping the result in an `Option`, because the caller owns the
  buffer and a partial decode stays visible in it. That shape is internal; the
  public accessors above are unaffected.
