# `std/fmt`

Formatting into `String`: numbers, bytes, padding. Ungated.

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
```

## Notes

- `fmt.hex` takes one `u64`, not a buffer — use `fmt.bytes` for a buffer.
- The fill character is a **byte**, not a `char`: pass `'0'` (which is a `u8` in
  that position) rather than a string.
- Padding counts bytes, so a multi-byte character pads short.
- There is no grouping/separator option, no sign control, no scientific
  notation, and no width/precision mini-language — `fmt.float(x, d)` is the whole
  float API.

## See also

- [`std/str`](str.md) for `from_i64`/`from_f64` and parsing
- [`table`](../libraries/table.md), which is `fmt.pad_right` over columns
