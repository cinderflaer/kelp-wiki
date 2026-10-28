---
title: "Checksums, encodings and dates"
description: "Checksums, encodings and dates over one short string, which is most of what a build tool does with text before it writes a cache key or a log line."
isPublished: true
tags: "example, text"
---

The `checksums-encodings-dates` program prints checksums of one short string.
It also prints two encodings with their round trips, and a date made from Unix seconds.

| | |
| --- | --- |
| Source | [`src/checksums-encodings-dates.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/checksums-encodings-dates.kp) |
| Needs | `hash`, `encoding`, `datetime` |
| Shows | three content hashes, two encodings and their round trips, a date from a seconds count |

## The dependencies

```toml
[dependencies]
hash     = "Lilly/fpl/hash"
encoding = "Lilly/fpl/encoding"
datetime = "Lilly/fpl/datetime"
```

None of them needs a capability. `datetime` in particular does not read the clock:
it converts a Unix seconds count the caller supplies, which is why this example
prints a fixed date instead of today's.

## The program

```kelp project
impl "deps/hash/lib"
impl "deps/encoding/lib"
impl "deps/datetime/lib"

fun main() {
    val text = "kelp"

    print("hash       crc32   = ${hash.crc32_str(text)}")
    print("hash       fnv1a32 = ${hash.fnv1a_32_str(text)}")
    print("hash       fnv1a64 = ${hash.fnv1a_64_str(text)}")

    val bytes = Bytes.from_str(text)
    val encoded = encoding.base64Encode(&bytes)
    print("encoding   base64  = ${encoded}")

    val decoded = encoding.base64Decode(encoded.as_str())
    if let Ok(round_trip) = decoded {
        print("encoding   round trip = ${round_trip.as_str()}")
    }

    val escaped = encoding.percentEncode("kelp lang/1?q=a b")
    print("encoding   percent = ${escaped}")
    val unescaped = encoding.percentDecode(escaped.as_str())
    if let Ok(plain) = unescaped {
        print("encoding   unescaped = ${plain.as_str()}")
    }

    // 1700000000 is 2023-11-14T22:13:20Z, and day 2 of the week is Tuesday.
    val civil = datetime.from_unix(1700000000)
    val stamp = datetime.format_iso8601(&civil)
    print(str.concat("datetime   1700000000 = ", stamp.as_str()))
    print("datetime   day of week = ${datetime.day_of_week(&civil)}")
    print("datetime   is_leap_year(2024) = ${datetime.is_leap_year(2024)}")

    val parsed = datetime.parse_iso8601("2024-02-29T12:34:56Z")
    if let Ok(moment) = parsed {
        print("datetime   parsed seconds = ${datetime.toUnix(moment)}")
        print("datetime   days from epoch = ${datetime.days_from_civil(1970, 1, 2)}")
    }

    // A bad escape is a value, not a panic.
    val broken = encoding.percentDecode("%zz")
    print("encoding   %zz is an error = ${result.isErr(broken)}")
}
```

## Run it

```sh
kelpc run checksums-encodings-dates.kp
```

## Output

```
hash       crc32   = 439546690
hash       fnv1a32 = 3832167273
hash       fnv1a64 = 6360897793009387625
encoding   base64  = a2VscA==
encoding   round trip = kelp
encoding   percent = kelp%20lang%2F1%3Fq%3Da%20b
encoding   unescaped = kelp lang/1?q=a b
datetime   1700000000 = 2023-11-14T22:13:20Z
datetime   day of week = 2
datetime   is_leap_year(2024) = true
datetime   parsed seconds = 1709210096
datetime   days from epoch = 1
encoding   %zz is an error = true
```

The CRC-32 value is the zlib/PNG/gzip variant, so `439546690` is what `crc32` in a
shell tool prints for `kelp` too.

## What to take from it

- **`crc32_str` and the `fnv1a` pair are hashes for keys and caches, not for
  security.** There is no SHA in the catalogue.
- **Percent-encoding leaves the RFC 3986 unreserved set alone:** letters, digits,
  `-`, `.`, `_` and `~`. So `kelp lang/1?q=a b` becomes
  `kelp%20lang%2F1%3Fq%3Da%20b`, and a space is `%20`, never `+`.
- **`percent_decode` is URL decoding, not form decoding.** A `+` stays a `+`.
- **Decoding returns a `Result`,** so a malformed escape is a value: `%zz` is
  `Err(Invalid)`. The program asks `result.isErr`, which is a free function in
  `std/result`, not a method.
- **`base64_decode` refuses whitespace** rather than skipping it, so text read
  from a file with line breaks needs the break removed first.
- **Dates are arithmetic on an `i64`,** so the same value formats the same way on
  any machine and no clock is involved. `parse_iso8601` accepts a trailing `Z` or
  a space instead of `T`, and no offset or fractional seconds.
- **A binding may not be named `when`.** That is a keyword, and the compiler says
  `expected identifier, found When`. This example names its parsed date `moment`
  for exactly that reason.

## See also

- [`hash`](/libraries/hash), [`encoding`](/libraries/encoding), [`datetime`](/libraries/datetime)
- [`std/time`](/stdlib/time) for the clock these libraries do not read
- [Text](/language/text) for `str` against `String`
