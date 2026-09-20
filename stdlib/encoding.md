---
title: "`std/encoding`"
description: "base64, base32, base58, hex and percent encoding over Bytes and str. Ungated."
isPublished: true
tags: "stdlib, text"
---
The alphabet-and-codec module: base64, base32, base58, hex and percent
encoding. Ungated, because it only shuffles bytes it is handed.

```kelp
impl "std/encoding"
```

Every encoder takes `&Bytes` and returns `String`; every decoder takes `&str`
and returns `Result<Bytes, DecodeErr>`, except the two percent decoders, which
return `Result<String, DecodeErr>`. One failure case, `DecodeErr.Invalid`, for
every decoder: the input is not in the alphabet, or its shape is not the one the
scheme defines. The decoders carry no position, so there is nothing for a richer
error to say.

| Function | Returns | Notes |
| --- | --- | --- |
| `encoding.base64_encode(b: &Bytes)` | `String` | RFC 4648 §4 alphabet, `=` padded |
| `encoding.base64_decode(s: &str)` | `Result<Bytes, DecodeErr>` | length must be a multiple of 4 |
| `encoding.base32_encode(b: &Bytes)` | `String` | RFC 4648 §6 alphabet (`A`-`Z`, `2`-`7`), `=` padded to 8 |
| `encoding.base32_decode(s: &str)` | `Result<Bytes, DecodeErr>` | length must be a multiple of 8 |
| `encoding.base58_encode(b: &Bytes)` | `String` | Bitcoin alphabet, no padding |
| `encoding.base58_decode(s: &str)` | `Result<Bytes, DecodeErr>` | |
| `encoding.hex_encode(b: &Bytes)` | `String` | lowercase, two characters per byte |
| `encoding.hex_decode(s: &str)` | `Result<Bytes, DecodeErr>` | either case, even length |
| `encoding.percent_encode(s: &str)` | `String` | RFC 3986 §2.3, a space is `%20` |
| `encoding.percent_decode(s: &str)` | `Result<String, DecodeErr>` | `+` is left alone |
| `encoding.form_encode(s: &str)` | `String` | form-urlencoded: a space is `+` |
| `encoding.form_decode(s: &str)` | `Result<String, DecodeErr>` | `+` is a space |
| `encoding.dump(b: &Bytes)` | `String` | a `hexdump -C`-shaped rendering |

```kelp
impl "std/encoding"
impl "std/result"

fun main() {
    val b = Bytes.from_str("hello")
    print(encoding.base64_encode(b))          // aGVsbG8=
    print(encoding.hex_encode(b))             // 68656c6c6f
    print(encoding.base32_encode(b))          // NBSWY3DP
    print(encoding.percent_encode("a b/c"))   // a%20b%2Fc

    val r = encoding.base64_decode("aGVsbG8=")
    if let Ok(decoded) = r {
        print(String.from_bytes(decoded.clone()))
    }
}
```

```
aGVsbG8=
68656c6c6f
NBSWY3DP
a%20b%2Fc
hello
```

## Notes

- **A decoder's payload is a borrow**, because that is what `Result`'s header
  promises: `if let Ok(decoded) = r` binds `&Bytes`, so the copy out is explicit
  (`decoded.clone()`). The same holds for `percent_decode`, whose payload is a
  `&String`. `result.unwrap` is only offered for a `Copy` payload.
- **Percent against form.** `percent_encode`/`percent_decode` are the URL form:
  a space is `%20` and `+` is data. `form_encode`/`form_decode` are
  `application/x-www-form-urlencoded`: a space is `+` and `+` is a space. Keeping
  them apart is the point, because guessing which one a caller meant is how a
  `%2B` turns into a space.
- **Base32 is uppercase and padded**, and lowercase is refused rather than
  folded: RFC 4648's reference encoder emits uppercase. The leftover bits of a
  final group must be zero, as the reference decoder requires.
- **Base58 has no padding** and drops `0`, `O`, `I` and `l`, so a transcribed
  value cannot be read two ways. Leading zero bytes become leading `1`s.
- **Whitespace is not skipped by any decoder.** If the source may contain line
  breaks, trim or join it first.
- `encoding.hex_encode` is the buffer spelling. `fmt.hex` is a different
  function: one `u64` without leading zeros.

## See also

- [`std/fmt`](/stdlib/fmt) for `fmt.hex`, `fmt.pad_left` and numbers
- [`std/result`](/stdlib/result) for the failure payload the decoders hand back
- [`std/str`](/stdlib/str) for `str.byte`, `str.len` and `str.is_digit`, which
  the alphabets are read through
