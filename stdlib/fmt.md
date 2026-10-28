---
title: "`std/fmt`"
description: "Formatting into String: numbers, bytes, padding, digit grouping and byte sizes, and the Display trait that lets a datac or enum appear in a template and in print. Ungated."
isPublished: true
tags: "stdlib, text"
---
Formatting into `String`: bytes, padding, digit grouping and byte sizes. Ungated.

Needs no `impl` line: the module is in scope by its own name.

## Numbers as text

A number's text is a method on the number, so no `fmt` call is needed first:

| Call | Returns | Notes |
| --- | --- | --- |
| `n.toText()` | `String` | an integer's decimal digits, `-` for a negative; the same text as `"${n}"` |
| `x.toText()` | `String` | a float's print form, the same text as `"${x}"` |
| `x.toText(decimals)` | `String` | a float with exactly `decimals` digits after the point; `x.toText(2)` is the usual call. The file needs `impl "std/str"` |

`fmt.int`, `fmt.uint` and `fmt.float` are retired. They still compile for one
release cycle, and each call prints an `outdated:` finding that names its
replacement. `--deny-outdated` makes the finding an error. The same goes for
`str.from_i64`, `str.from_u64` and `str.from_f64`.

## Other functions

| Function | Returns | Notes |
| --- | --- | --- |
| `fmt.hex(n: u64)` | `String` | lowercase hex |
| `fmt.bytes(b: Bytes)` | `String` | a debugging dump: lowercase hex, one space between bytes, `1f 8b 08` |
| `fmt.padLeft(s: &str, width: usize, fill: u8)` | `String` | pads on the left to `width`; a longer `s` is returned unchanged |
| `fmt.padRight(s: &str, width: usize, fill: u8)` | `String` | pads on the right |
| `fmt.commasU64(n: u64)` | `String` | a comma every three digits: `1234567` is `1,234,567` |
| `fmt.commasI64(n: i64)` | `String` | likewise, with the sign kept |
| `fmt.humanSize(bytes: u64)` | `String` | binary units, two decimals: `585.94 KiB`, `0 B` |
| `fmt.groupDigits(text: &str)` | `String` | the digit run of `text` with a comma every three digits; a leading `-` is kept and not counted |
| `fmt.humanScale(bytes: u64, div: u64, unit: &str)` | `String` | `bytes / div` with two decimals, then `unit` appended; the helper `human_size` is built on |

`print` itself formats floats with six decimals. For another count, use
`x.toText(decimals)`.

```kelp
impl "std/str"

fun main() {
    val n: i64 = -7
    print(n.toText())
    val u: u64 = 1024
    print(u.toText())
    val x: f64 = 1.5
    print(x.toText(2))
    print((1.0 / 3.0).toText(4))
    print(fmt.hex(255))
    print(fmt.padLeft("7", 3, '0'))
    print(fmt.padRight("ab", 5, '.'))
    print(fmt.commasU64(1234567))
    print(fmt.humanSize(1536))
    print(fmt.groupDigits("-9876543"))       // -9,876,543
    print(fmt.humanScale(bytes = 3000, div = 1000, unit = " kB"))   // 3.00 kB
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
-9,876,543
3.00 kB
```

## Notes

- `fmt.hex` takes one `u64`, not a buffer: use `fmt.bytes` for a buffer.
- The fill character is a **byte**, not a `char`: pass `'0'` (which is a `u8` in
  that position) rather than a string.
- Padding counts bytes, so a multi-byte character pads short.
- `commas_u64` and `commas_i64` exist as two names because a user module cannot
  overload a name.
- `human_size` is **binary** (1024) and not decimal, two decimals, one space
  before the unit: `"585.94 KiB"`. Binary is what a byte-count command-line
  option like `4k` means, so a tool that prints a size and takes one agrees with
  itself.
- There is no sign control, no scientific notation, and no width/precision
  mini-language: `x.toText(d)` is the whole float API.

## `Display`

The module also declares one trait:

```kelp
pub trait Display {
    fun Self.to_text() => String
}
```

A `datac` or `enum` that implements it may appear in `"${x}"` and as the argument
of `print`/`print!`; the front end lowers both to `x.to_text()`, so the value is
only borrowed and stays owned. A type without it is refused with a message that
names `Display`. Builtin types keep the formatting they always had. `to_text`
has to build its `String` without a template (a template is not a value), for
example with `String.empty()`, `push_str` and `n.toText()` for a number. A worked
example is [Operator traits and `Display`](/language/operator-traits).

## See also

- [`std/str`](/stdlib/str) for parsing and the other text functions
- [Operator traits and `Display`](/language/operator-traits)
- [`table`](/libraries/table), which is `fmt.padRight` over columns
