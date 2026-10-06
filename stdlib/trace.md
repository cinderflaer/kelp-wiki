---
title: "std/trace"
description: "Opt-in trace events and duration spans with monotonic timestamps."
tags: "stdlib, diagnostics, profiling"
---

`std/trace` writes compact trace records to stderr. It is for explicit
diagnostic and profiling hooks, not automatic instrumentation.

```kelp
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
| `trace.event(file, line, name)` | `unit` | Emits an instantaneous event. |
| `trace.begin(file, line, name)` | `trace.Span` | Emits a `begin` record and saves its timestamp. |
| `trace.end(file, line, span)` | `unit` | Emits an `end` record with elapsed nanoseconds. |

Pass `source.file()` and `source.line()` at each call. A library cannot inspect
its caller's location, so this keeps the record attached to the Kelp code that
actually requested it rather than to `std/trace` itself.

Each call writes one escaped, tab-separated line:

```text
trace<TAB>event|begin|end<TAB>monotonic_ns<TAB>file:line<TAB>name[<TAB>elapsed_ns]
```

`end` includes the duration from `begin`; events and begins do not. Timestamps
are monotonic and meaningful for ordering and durations within one process,
not for dates or comparisons between processes. Tabs and newlines in the file
or name are escaped, so one trace call remains one record.
