---
title: "`datetime`: civil calendar math over Unix seconds"
description: "Gregorian date/time arithmetic from an i64 count of Unix seconds to a Civil value and back, plus leap years, day of week, and ISO-8601 parse/format."
isPublished: true
tags: "library, time"
---
Gregorian date/time arithmetic from an `i64` count of Unix seconds to a `Civil`
value and back, plus leap years, day of week, and ISO-8601 parse/format.

**No capability.** This library never reads the clock: it is pure integer
arithmetic from a seconds count the caller supplies. For the current time use
`std/time.now_unix()` (gated on `time`) and pass the result in.

```toml
[dependencies]
datetime = "Juniper/fpl/datetime"
```

```kelp
impl "deps/datetime/lib"
```

## Types

```kelp
datac Civil(val year: i64, val month: i32, val day: i32, val hour: i32, val min: i32, val sec: i32)
datac Ymd(val year: i64, val month: i32, val day: i32)

enum ParseErr {
    Invalid
}
```

All values are UTC; there is no timezone or offset handling.

## Unix seconds to civil, and back

| Function | Returns |
| --- | --- |
| `from_unix(seconds: i64)` | `Civil`: the UTC civil time of that instant |
| `to_unix(c: &Civil)` | `i64`: the inverse |
| `civil_from_days(z: i64)` | `Ymd`: days since 1970-01-01 to a date |
| `days_from_civil(year: i64, month: i32, day: i32)` | `i64`: the inverse |
| `add_seconds(c: &Civil, delta: i64)` | `Civil` |
| `diff_seconds(a: &Civil, b: &Civil)` | `i64`: `a - b`, in seconds |
| `day_of_week(c: &Civil)` | `i32`: 0 = Sunday ... 6 = Saturday |
| `is_leap_year(year: i64)` | `bool` |

The days conversion is Howard Hinnant's `civil_from_days`/`days_from_civil`:
proleptic Gregorian, valid for every representable `i64`, and it relies only on
C's truncating integer division, which Kelp's `/` matches.

`from_unix` normalizes a negative `seconds` correctly (`-1` is
1969-12-31T23:59:59Z), so pre-1970 instants work.

## ISO-8601

| Function | Returns |
| --- | --- |
| `format_iso8601(c: &Civil)` | `String`: `YYYY-MM-DDTHH:MM:SSZ` |
| `parse_iso8601(s: &str)` | `result.Result<Civil, ParseErr>` |
| `parse_stamp(s: &str)` | `result.Result<Civil, ParseErr>`: a bare `YYYY-MM-DD` is read as midnight UTC of that day |
| `parse_stamp_unix(s: &str)` | `result.Result<i64, ParseErr>`: the same input as a seconds count, ready to compare against `std/time.now_unix()` |

`parse_iso8601` is strict: exactly `YYYY-MM-DDTHH:MM:SS` (or the same with a
space instead of `T`), and an optional trailing `Z`. No fractional seconds, no
`+HH:MM` offset. It accepts a leap second (`:60`) and validates the field
ranges: month 1..12, day 1..31 (not days-per-month), hour 0..23, minute 0..59,
second 0..60.

`parse_stamp` is the lenient door for a command-line flag: a value ten
characters long is a date and gets `T00:00:00` appended, anything else goes to
the strict parser unchanged, and `parse_stamp_unix` is that same value as the
`i64` a comparison wants.

`format_iso8601` zero-pads to four year digits; a year outside `[0, 9999]`
prints with more or fewer digits rather than being clamped or refused.

Helpers `pad2(n: i32)` and `pad4(n: i64)` return a zero-padded `String`;
`parse_field(s, from, to)` parses one `YYYY`-style slice as `Result<i64, ParseErr>`.

## Example

```kelp
impl "deps/datetime/lib"

fun main() {
    val c = datetime.from_unix(1700000000)
    print(datetime.format_iso8601(&c))
    print(c.year)
    print(c.month)
    print(c.day)
    print(datetime.day_of_week(&c))
    print(datetime.is_leap_year(2024))
    val p = datetime.parse_iso8601("2024-02-29T12:34:56Z")
    if let Ok(x) = p {
        print(datetime.to_unix(x))
        print(datetime.format_iso8601(x))
    }
    val c2 = datetime.add_seconds(&c, 3600)
    print(datetime.diff_seconds(&c2, &c))
    print(datetime.days_from_civil(1970, 1, 1))
    val ymd = datetime.civil_from_days(0)
    print(ymd.year)
}
```

Output:

```
2023-11-14T22:13:20Z
2023
11
14
2
true
1709210096
2024-02-29T12:34:56Z
3600
0
1970
```

## Notes

- The example passes `x` rather than `&x`: a parameter of a borrowed type takes
  the value bare, and `p` is an owned local, so `if let Ok(x) = p` binds `x` by
  value rather than as a `&Civil` (syntax.md §6.1, §10.2).
- `parse_iso8601` does not reject an impossible date: `2024-02-31` parses, and
  `to_unix` then gives the same instant as 2024-03-02. Validate day-of-month
  yourself if that matters.
- Leap-year and day-of-week logic use the proleptic Gregorian calendar for all
  years, including before 1582.
- `diff_seconds(a, b)` is `to_unix(a) - to_unix(b)`, so it is negative when `a`
  is earlier.
