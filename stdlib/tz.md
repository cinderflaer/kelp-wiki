---
title: "`std/tz`"
description: "Time zones over the host's TZif database: the offset in force at an instant, the wall clock it names, the instants a wall clock names (`One`/`Ambiguous`/`Gap`) and a `strftime` subset. Gated on fs and env(TZDIR); hosted only."
isPublished: true
tags: "stdlib, time"
---
Time zones over the system TZif database. `tz.load(name)` reads one zone file
(RFC 8536), the compiled form of the tz database, and answers instants with it.
**Gated on `fs` and `env`**: the module reads a file and asks the environment
for the database directory.

```kelp
impl "std/tz" caps(fs = ["/**"], env = ["TZDIR"])
impl "std/tz" caps(fs = ["/nix/store/**/share/zoneinfo/**"], env = ["TZDIR"])
```

The design is
[`stdlib/tz.md`](/stdlib/tz).
It needs no clock of its own: every call takes the instant or the wall clock the
caller already has, the way [`datetime`](/libraries/datetime) does.

## Types

```kelp
datac Offset(val seconds: i32, val abbrev: String, val is_dst: bool)

datac LocalTime(val year: i32, val month: i32, val day: i32,
                val hour: i32, val minute: i32, val second: i32,
                val weekday: i32, val yday: i32, val offset: Offset)

enum Resolved {
    One(val unix: i64)
    Ambiguous(val first: i64, val second: i64)
    Gap
}

enum TzErr {
    NotFound
    Denied
    Corrupt(val message: String)
}
```

`weekday` is 0 for Sunday through 6 for Saturday, and `yday` is 1 through 366.
Both follow `localtime`'s own numbering, not an ISO one.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `load(name)` | `Result<Zone, TzErr>` | `$TZDIR`, then `/usr/share/zoneinfo` |
| `load_in(dir, name)` | `Result<Zone, TzErr>` | one named directory, no environment lookup |
| `parse(data)` | `Result<Zone, TzErr>` | TZif bytes already in hand, no file read |
| `utc()` | `Zone` | the fixed zero offset under the name `UTC` |
| `fixed(offset_seconds)` | `Zone` | a fixed offset with no name; `%Z` prints `UTC` for zero and `+HH:MM` otherwise |
| `Zone.offset_at(unix_seconds)` | `Offset` | the offset in force at the instant |
| `Zone.local_parts(unix_seconds)` | `LocalTime` | the wall clock the instant names |
| `Zone.to_unix(y, m, d, h, mi, s)` | `Resolved` | the instant or instants a wall clock names |
| `Zone.format(unix_seconds, fmt)` | `String` | `%Y %m %d %H %M %S %z %Z %a %b %j %%` |

`format` copies any other `%x` through unchanged, `%` included. `%z` is
`+HHMM`/`-HHMM` and `%Z` is the abbreviation the database carries rather than a
locale's idea of it.

## Looking up a zone

`tz.load` reads the name under `$TZDIR` when that variable is set, non-empty,
absolute and free of `..`, and under `/usr/share/zoneinfo` otherwise. Both
candidates are tried: `NotFound` moves the search to the next directory, while
`Denied` and `Corrupt` end it, because a refused read is not a different grant
question and a corrupt file is corrupt wherever it was found. `tz.load_in`
reads one directory the caller names and never consults the environment;
`tz.parse` skips the filesystem entirely, so a caller holding TZif bytes (an
archive member, a fixture) does not have to write them out first.

A name with a leading `/`, a `..` segment or a NUL byte is `Denied` before any
path is built, so no name escapes the database directory. A read the OS refuses
with `EACCES` or `EPERM` is `Denied`; a missing file (or a directory where a
file was wanted) is `NotFound`; a file that is not a well-formed TZif file is
`Corrupt(message)`.

`std/tz` adds no authority of its own: the `fs` grant decides which paths are
reachable and the `env` grant must name `TZDIR` itself, because the environment
check is a name check. A grant too narrow for a path is the compiler's own
call-site **panic** rather than a returned `Denied` (open item 73,
[`meta/roadmap.md`](/meta/roadmap)).
`zoneinfo` on NixOS is a symlink into the store twice over (`/etc/zoneinfo` to
`/etc/static/zoneinfo`, which is itself a link to
`/nix/store/<hash>-tzdata-<version>/share/zoneinfo`). The capability check
resolves the whole chain before matching, so a grant has to name that store
tree, or the whole filesystem: `/etc/static/zoneinfo/**` is refused at the call.

## `One`, `Ambiguous` and `Gap`

`Zone.to_unix` takes a wall clock reading and hands back what it names.

- `One(unix)`: exactly one instant carries that reading.
- `Ambiguous(first, second)`: a reading the clock passes twice, which is what a
  clock set back does, with both instants and the earlier one first.
- `Gap`: a reading the clock never passes, which is what a clock set forward
  does.

The answer is computed, not tabled: every distinct offset in the zone is tried
and a candidate is kept only when the instant it produces really does carry that
offset. That is why `Gap` needs no special case, because across a spring-forward
neither offset reproduces itself, and across a fall-back both do.

## Limits

- **No leap seconds.** A POSIX instant is a count of seconds with no 23:59:60 in
  it; the TZif leap-second table is skipped rather than consulted, and the
  `right/` database is not read. The difference between UTC and TAI is left to
  whoever needs it.
- **Hosted only.** `std/tz` reads a file and an environment variable, neither of
  which a bare-metal image has a form of, so it is `Hosted` in
  `freestanding::std_admission` and a freestanding project that imports it is
  refused by name. See [Freestanding mode](/language/freestanding).
- **No database of its own.** It carries no embedded copy and no version check:
  the files are whatever the host has installed, so a zone whose rules changed
  after that installation is described by the old file.
- **No locale.** Month, weekday and abbreviation text are the database's own
  ASCII abbreviations or the English three-letter tables built into the
  formatter. There is no translated month name and no `LC_TIME` anywhere.
- **Years 1 to 9999.** Every instant function panics outside that range, and
  `to_unix` panics on a date or a time of day that is not real (month 13, day 31
  in April, a leap day in a non-leap year, hour 24). A caller's own arithmetic
  error is not the zone's answer.
- **A footer it does not understand is treated as absent**, so an exotic rule
  in a newer footer, or an offset or a rule's time past two weeks (the parser's
  ceiling), falls back to the last transition's type instead of failing the
  load.

## Example

```kelp
// The `std/tz` example: the offset in force at an instant, the wall clock an
// instant names, the instant a wall clock names, and the formatter.
impl "std/tz" caps(fs = ["/**"], env = ["TZDIR"])

fun digits(n: i64) => String = n.toText()

fun label(r: &tz.Resolved) => String {
    var out = String.empty()
    if let One(u) = r {
        out.push_str("one ")
        val d = digits(u)
        out.push_str(d.as_str())
    } elif let Ambiguous(a, b) = r {
        out.push_str("ambiguous ")
        val da = digits(a)
        val db = digits(b)
        out.push_str(da.as_str())
        out.push(' ')
        out.push_str(db.as_str())
    } else {
        out.push_str("gap")
    }
    return out
}

fun main() {
    val loaded = tz.load("America/New_York")
    if let Ok(z) = loaded {
        // The 2024 spring-forward instant, one second either side of it.
        val before = z.offset_at(1710053999)
        val after = z.offset_at(1710054000)
        print("${before.seconds} ${before.abbrev} dst=${before.is_dst}")
        print("${after.seconds} ${after.abbrev} dst=${after.is_dst}")

        val lt = z.local_parts(1710054000)
        print("${lt.year}-${lt.month}-${lt.day} ${lt.hour}:${lt.minute}:${lt.second} wd=${lt.weekday} yday=${lt.yday}")

        // An ordinary wall clock, one the spring jump skipped, and one the
        // fall back repeats.
        print(label(z.to_unix(2024, 3, 10, 1, 30, 0)))
        print(label(z.to_unix(2024, 3, 10, 2, 30, 0)))
        print(label(z.to_unix(2024, 11, 3, 1, 30, 0)))

        // 2100 is past the last transition in the file, so this answer comes
        // from the footer's POSIX TZ string alone.
        print(z.format(4116758400, "%Y-%m-%d %H:%M:%S %z %Z %a %b %j"))
    } else {
        print("no zone database")
    }

    // The two zones that need no file.
    val utc = tz.utc()
    print(utc.format(0, "%Y-%m-%d %H:%M:%S %Z %z"))
    val kolkata = tz.fixed(19800)
    print(kolkata.format(0, "%H:%M %Z %z"))

    // A name with a `..` segment never becomes a path.
    val escape = tz.load("../../etc/passwd")
    if let Err(e) = escape {
        if let Denied = e {
            print("escape refused")
        } else {
            print("other error")
        }
    }
}
```

```sh
kelpc build example.kp -o example
TZDIR=/etc/zoneinfo ./example
```

```text
-18000 EST dst=false
-14400 EDT dst=true
2024-3-10 3:0:0 wd=0 yday=70
one 1710052200
gap
ambiguous 1730611800 1730615400
2100-06-15 12:00:00 -0400 EDT Tue Jun 166
1970-01-01 00:00:00 UTC +0000
05:30 +05:30 +0530
escape refused
```

## See also

- [`std/time`](/stdlib/time): the wall and monotonic clocks this module never reads
- [`datetime`](/libraries/datetime): calendar arithmetic with no zone and no database
- [Freestanding mode](/language/freestanding): why `std/tz` is hosted only
- [Limits in v1](/language/limits)
