---
title: "`std/fmt`"
description: "Formatting into String: numbers, bytes, padding, digit grouping and byte sizes, and the Display trait that lets a datac or enum appear in a template and in print. Ungated."
isPublished: true
tags: "stdlib, text"
---
Formatting into `String`: numbers, bytes, padding, digit grouping and byte
sizes. Ungated.

```kelp
impl "std/fmt"
```

| Function | Returns | Notes |
| --- | --- | --- |
| `fmt.int(n: i64)` | `String` | decimal, `-` for negatives |
| `fmt.uint(n: u64)` | `String` | decimal |
| `fmt.float(x: f64, decimals: i32)` | `String` | fixed point with exactly `decimals` digits |
| `fmt.hex(n: u64)` | `String` | lowercase hex |
| `fmt.bytes(b: Bytes)` | `String` | hex-ish view of a buffer |
| `fmt.pad_left(s: &str, width: usize, fill: u8)` | `String` | pads on the left to `width`; a longer `s` is returned unchanged |
| `fmt.pad_right(s: &str, width: usize, fill: u8)` | `String` | pads on the right |
| `fmt.commas_u64(n: u64)` | `String` | a comma every three digits: `1234567` is `1,234,567` |
| `fmt.commas_i64(n: i64)` | `String` | likewise, with the sign kept |
| `fmt.human_size(bytes: u64)` | `String` | binary units, two decimals: `585.94 KiB`, `0 B` |

All the number functions wrap `str.from_*`, so `fmt.int(n)` is `str.from_i64(n)`
with a name that reads well inside a call. `print` itself formats floats with six
decimals; use `fmt.float` when you want another count.

```kelp
impl "std/fmt"

fun main() {
    print(fmt.int(-7))
    print(fmt.uint(1024))
    print(fmt.float(1.5, 2))
    print(fmt.float(1.0 / 3.0, 4))
    print(fmt.hex(255))
    print(fmt.pad_left("7", 3, '0'))
    print(fmt.pad_right("ab", 5, '.'))
    print(fmt.commas_u64(1234567))
    print(fmt.human_size(1536))
}
```

```
-7
1024
1.50
0.3333
ff
007
ab...
1,234,567
1.50 KiB
```

## Notes

- `fmt.hex` takes one `u64`, not a buffer: use `fmt.bytes` for a buffer.
- The fill character is a **byte**, not a `char`: pass `'0'` (which is a `u8` in
  that position) rather than a string.
- Padding counts bytes, so a multi-byte character pads short.
- `commas_u64` and `commas_i64` exist as two names because a user module cannot
  overload a name, which is why `fmt` already spells `int` and `uint` apart.
- `human_size` is **binary** (1024) and not decimal, two decimals, one space
  before the unit: `"585.94 KiB"`. Binary is what a byte-count command-line
  option like `4k` means, so a tool that prints a size and takes one agrees with
  itself.
- There is no sign control, no scientific notation, and no width/precision
  mini-language: `fmt.float(x, d)` is the whole float API.

## `Display`

The module also declares one trait:

```kelp
pub trait Display {
    fun Self.to_text().R: String
}
```

A `datac` or `enum` that implements it may appear in `"${x}"` and as the argument
of `print`/`print!`; the front end lowers both to `x.to_text()`, so the value is
only borrowed and stays owned. A type without it is refused with a message that
names `Display`. Builtin types keep the formatting they always had. `to_text`
has to build its `String` without a template (a template is not a value), for
example with `String.empty()`, `push_str` and `fmt.int`. A worked example is
[Operator traits and `Display`](/language/operator-traits).

## See also

- [`std/str`](/stdlib/str) for `from_i64`/`from_f64` and parsing
- [Operator traits and `Display`](/language/operator-traits)
- [`table`](/libraries/table), which is `fmt.pad_right` over columns
