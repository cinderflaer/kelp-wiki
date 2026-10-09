---
title: "`hash`: CRC-32 and FNV-1a checksums"
description: "Non-cryptographic checksums over Bytes/str - CRC-32 (the zlib/PNG/gzip polynomial) and FNV-1a, 32- and 64-bit."
isPublished: true
tags: "library"
---
Non-cryptographic checksums over `Bytes`/`str`: CRC-32 (the zlib/PNG/gzip
polynomial) and FNV-1a, 32- and 64-bit.

No capability. These are content-addressing and cache-key hashes, not security
primitives: there is no SHA here.

```toml
[dependencies]
hash = "Lilly/fpl/hash"
```

```kelp
impl "deps/hash/lib"
```

## Functions

| Function | Returns |
| --- | --- |
| `crc32(data: &Bytes)` | `u32` |
| `crc32_str(s: &str)` | `u32` |
| `fnv1a_32(data: &Bytes)` | `u32` |
| `fnv1a_32_str(s: &str)` | `u32` |
| `fnv1a_64(data: &Bytes)` | `u64` |
| `fnv1a_64_str(s: &str)` | `u64` |

The `_str` forms build a `Bytes` from the text and call the byte form.

### Variants

- **CRC-32** is the zlib/PNG/gzip variant: init `0xFFFFFFFF`, reflected, final
  XOR `0xFFFFFFFF`, polynomial `0xEDB88320`. This is the value `crc32` prints in
  shell tools and what gzip stores.
- **FNV-1a** is `hash = offset; for each byte: hash = (hash XOR byte) * prime`,
  with the standard 32- and 64-bit offsets and primes.

Constants exposed: `CRC32_POLY`, `FNV32_OFFSET`, `FNV32_PRIME`, `FNV64_OFFSET`,
`FNV64_PRIME`. `crc32_table_entry(i: u32) -> u32` builds one table row
bit-by-bit and is callable on its own; the `crc32` loop calls it per byte.

## Example

```kelp project
impl "deps/hash/lib"

fun main() {
    print(hash.crc32_str("hello"))
    print(hash.fnv1a_32_str("hello"))
    print(hash.fnv1a_64_str("hello"))
    val b = Bytes.from_str("hello")
    print(hash.crc32(&b))
    print(hash.fnv1a_32(&b))
    print(hash.fnv1a_64(&b))
}
```

Output:

```
907060870
1335831723
11831194018420276491
907060870
1335831723
11831194018420276491
```

## Notes

- The CRC table row is computed bit-by-bit per index rather than cached: nothing
  here keeps module-level mutable state, so a hash call rebuilds the eight-round
  table entry for each byte. Fine for checksums and keys, not for a hot loop over
  gigabytes.
- Integer `*` and `^` in Kelp wrap, which is exactly what FNV needs.
