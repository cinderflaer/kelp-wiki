---
title: "`log`: leveled records to stderr"
description: "Leveled log lines with a unix timestamp and a stable prefix."
isPublished: true
tags: "library"
---
Leveled log lines with a unix timestamp and a stable prefix.

**Gated on `time`** (for the timestamp): a consumer must delegate it explicitly.

```toml
[dependencies]
log = "Lilly/fpl/log"
```

```kelp
impl "deps/log/lib" caps(time = [])
```

`time` has no pattern to restrict, so an empty list is the whole grant.

## Levels

Levels are plain `i32` constants rather than an `enum`: an `enum` is always owned
and never `Copy`, so a `Logger.min_level` field of that type could only be read
through a borrow and every comparison would need its own borrow-taking helper.
Four `const`s compare with `<` directly and store as a plain field.

| Constant | Value | Name printed |
| --- | --- | --- |
| `log.LEVEL_DEBUG` | 0 | `DEBUG` |
| `log.LEVEL_INFO` | 1 | `INFO` |
| `log.LEVEL_WARN` | 2 | `WARN` |
| `log.LEVEL_ERROR` | 3 | `ERROR` |

## Type

```kelp
datac Logger(val name: String, val min_level: i32)
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `new_logger(name: &str, min_level: i32)` | `Logger` | `min_level` is one of the `LEVEL_*` constants |
| `debug(l: &Logger, msg: &str)` | `Unit` | |
| `info(l: &Logger, msg: &str)` | `Unit` | |
| `warn(l: &Logger, msg: &str)` | `Unit` | |
| `error(l: &Logger, msg: &str)` | `Unit` | |
| `log_at(l: &Logger, level: i32, msg: &str)` | `Unit` | the one function that formats and writes; a record below `min_level` is dropped before anything is formatted |
| `level_name(level: i32)` | `&str` | `"DEBUG"`, `"INFO"`, `"WARN"`, or `"ERROR"` for anything unrecognised |

`max_level` is not a thing: `level < min_level` drops the record, so a higher
`min_level` means fewer records. There is no `logger.set_level`: `min_level` is
a `val` field, so a new level means a new `Logger`.

## Line format

```
[<unix-seconds>] <LEVEL> <name>: <msg>
```

Written to **stderr** via `io.eprint`, so it is not interleaved with a program's
stdout pipe. Integer seconds, no milliseconds, no timezone (unix time is UTC).

## Example

```kelp
impl "deps/log/lib" caps(time = [])

fun main() {
    val l = log.new_logger("app", log.LEVEL_INFO)
    log.debug(&l, "not printed")
    log.info(&l, "started")
    log.warn(&l, "careful")
    log.error(&l, "broke")
    print(log.level_name(log.LEVEL_ERROR))
    print(log.level_name(log.LEVEL_DEBUG))
}
```

stdout:

```
ERROR
DEBUG
```

stderr:

```
[1789836728] INFO app: started
[1789836728] WARN app: careful
[1789836728] ERROR app: broke
```

The exact timestamp varies with the run.

## Notes

- Not thread-safe and not line-buffered by this library: each record is one
  `eprint` call, so a record is written whole as long as nothing else writes to
  the same fd.
- No structured fields, no JSON output, no log rotation, no `log_at` shortcut for
  a `String` message (a `str` parameter accepts `String.as_str()`).
- The timestamp is read once per record, so a filtered record costs no `time`
  call.
