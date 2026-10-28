---
title: "`std/time`"
description: "Clocks and sleeping. Gated on time."
isPublished: true
tags: "stdlib, time"
---
Clocks and sleeping. **Gated on `time`.**

```kelp
impl "std/time" caps(time = [])
```

`time` has no pattern to restrict, so an empty list is the whole grant: naming
any function in the module is the authority.

| Function | Returns | Notes |
| --- | --- | --- |
| `time.nowUnix()` | `i64` | seconds since the epoch (UTC) |
| `time.nowMonoNs()` | `i64` | nanoseconds on the **monotonic** clock: for durations, never for dates |
| `time.sleepMs(ms: u64)` | `Unit` | |

```kelp project
impl "deps/datetime/lib"
impl "std/time"

fun main() {
    val start = time.nowMonoNs()
    time.sleepMs(2)
    val elapsed = time.nowMonoNs() - start
    print(elapsed >= 0)

    val now = time.nowUnix()
    print(now > 0)

    val civil = datetime.from_unix(now)
    print(datetime.format_iso8601(&civil))
}
```

## Notes

- `sleep_ms` is in this module because there is nowhere else for it yet, but it
  takes no authority: sleeping does not touch anything shared. Any module that
  holds `time` can sleep.
- `now_unix` is integer seconds: no sub-second precision, no timezone (unix time
  is UTC by definition).
- Use `now_mono_ns` for measuring: `now_unix` can jump when the wall clock is
  adjusted, the monotonic clock cannot.
- There is no formatting here. Turning seconds into a date and back is
  [`datetime`](/libraries/datetime), which needs no capability at all:
  it is pure arithmetic on a number you supply.
- [`log`](/libraries/log) and [`benchkit`](/libraries/benchkit) are the
  two libraries that consume this module, and both therefore need `time`
  delegated to *them*.

## See also

- [`datetime`](/libraries/datetime)
- [`log`](/libraries/log)
- [`benchkit`](/libraries/benchkit)
