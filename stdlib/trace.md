---
title: "`std/trace`"
description: "Opt-in trace events and duration spans with monotonic timestamps, written to stderr. Gated on time."
isPublished: true
tags: "stdlib, diagnostics, profiling"
---

`std/trace` writes compact trace records to stderr. It is for explicit
diagnostic and profiling hooks, not automatic instrumentation.

```kelp norun
impl "std/source"
impl "std/trace" caps(time = [])

fun main() {
    trace.event(source.file(), source.line(), "connected")
    val request = trace.begin(source.file(), source.line(), "request")
    // work
    trace.end(source.file(), source.line(), request)
}
```

It needs the `time` capability because every record uses the monotonic clock.
`time` has no resource names, so `caps(time = [])` grants the domain itself.
There is no compiler flag or environment switch that enables tracing for a
program that does not call this module.

| Function | Result | Meaning |
| --- | --- | --- |
| `trace.event(file, line, name)` | `Unit` | Emits an instantaneous event. |
| `trace.begin(file, line, name)` | `trace.Span` | Emits a `begin` record and saves its timestamp. |
| `trace.end(file, line, span)` | `Unit` | Emits an `end` record with elapsed nanoseconds. |
| `trace.emit(kind, file, line, name, elapsed_ns)` | `Unit` | The one writer the three above use. `elapsed_ns` is `-1` when the record has no duration. Call it directly only to write a custom kind. |
| `trace.escape(text)` | `String` | Escapes a backslash, a tab and a newline, so the text fits in one field. |

Pass `source.file()` and `source.line()` at each call. A library cannot inspect
its caller's location, so this keeps the record attached to the Kelp code that
actually requested it rather than to `std/trace` itself.

Each call writes one escaped, tab-separated line to standard error (through
`std/io`), so the trace goes to the terminal or the log without touching
standard output:

```text
trace<TAB>event|begin|end<TAB>monotonic_ns<TAB>file:line<TAB>name[<TAB>elapsed_ns]
```

`end` includes the duration from `begin`; events and begins do not. Timestamps
are monotonic and meaningful for ordering and durations within one process,
not for dates or comparisons between processes. Backslashes, tabs and newlines in the file
or name are escaped (as `\\`, `\t` and `\n`), so one trace call remains one record.

## See also

- [`std/time`](/stdlib/time) for the monotonic clock the records use
- [`std/source`](/stdlib/source) for the call-site values the calls take
- [`std/io`](/stdlib/io) for `eprint`, which writes each record
