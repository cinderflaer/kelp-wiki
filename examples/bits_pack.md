---
title: "bits_pack"
description: "Packs a flag and two narrow fields into one byte, reads them back, walks a fixed-size bit set, and prints a seeded byte stream that repeats on every run."
isPublished: true
tags: "example, data-formats"
---
Packs a flag and two narrow fields into one byte, reads them back, walks a
fixed-size bit set, and prints a seeded byte stream that repeats on every run.

| | |
| --- | --- |
| Source | [`src/bits_pack.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/bits_pack.kp) |
| Needs | `bits`, `prng` |
| Shows | MSB-first bit fields, `BitSet` over `Bytes`, and determinism from a seed |

## The dependencies

```toml
[dependencies]
bits = "Juniper/fpl/bits"
prng = "Juniper/fpl/prng"
```

Neither needs a capability. `prng` is arithmetic on a `u64`, which is why a
"random" byte stream can be part of a reproducible test.

## The program

```kelp project
impl "deps/bits/lib"
impl "deps/prng/lib"

fun main() {
    // One flag, then a 4-bit value, then a 3-bit value: eight bits, one byte.
    var writer = bits.writer_new()
    writer.write_bit(true)
    writer.write_bits(5, 4)
    writer.write_bits(3, 3)
    val packed = bits.finish(writer)

    print("bits       bytes written = ${packed.len()}")
    print("bits       the byte = ${packed.get(0)}")

    var reader = bits.reader_new(packed)
    print("bits       flag = ${reader.read_bit()}")
    print("bits       first field = ${reader.read_bits(4)}")
    print("bits       second field = ${reader.read_bits(3)}")
    print("bits       bits left = ${reader.remaining_bits()}")

    // A BitSet is fixed at construction. Bit 0 is the top bit of byte 0.
    var flags = bits.new(10)
    flags.set(0, true)
    flags.set(9, true)
    print("bits       bitset length = ${flags.len()}")
    print("bits       count_ones = ${flags.count_ones()}")
    print("bits       get(1) = ${flags.get(1)}")
    flags.clear()
    print("bits       after clear = ${flags.count_ones()}")

    // Seeded, so two runs print the same three bytes.
    var rng = prng.new(7)
    print("prng       byte 1 = ${prng.below(rng, 256)}")
    print("prng       byte 2 = ${prng.below(rng, 256)}")
    print("prng       byte 3 = ${prng.below(rng, 256)}")

    // Same seed, same sequence: this line repeats the first draw.
    var again = prng.new(7)
    print("prng       same seed, first byte again = ${prng.below(again, 256)}")
}
```

## Run it

```sh
kelpc run bits_pack.kp
```

## Output

```
bits       bytes written = 1
bits       the byte = 171
bits       flag = true
bits       first field = 5
bits       second field = 3
bits       bits left = 0
bits       bitset length = 10
bits       count_ones = 2
bits       get(1) = false
bits       after clear = 0
prng       byte 1 = 174
prng       byte 2 = 174
prng       byte 3 = 34
prng       same seed, first byte again = 174
```

The byte is `171` because the stream is MSB-first: `1 0101 011` padded with a
zero on the right is `10101011`.

## What to take from it

- **Writing is MSB-first, and `finish` pads the last partial byte with zeros on
  the right.** That is what makes a packed stream readable by any other
  MSB-first reader, including a hand-written one in another language.
- **`finish` takes the writer by value.** It is declared `move BitWriter`, because
  a `mut` receiver only borrows and the buffer cannot be moved out of a borrowed
  value. After `finish` the writer is gone, and reusing it does not build.
- **`BitSet` needs the bit count up front,** and both `get` and `set` panic past the
  end. Bit 0 is the most significant bit of byte 0, so `set(0, true)` on a one-byte
  set is `128`, not `1`.
- **`read_bits` returns a `u32`,** so a single call reads at most 32 bits.
- **The seeded draws repeat exactly.** Two generators built with seed `7` produce
  the same sequence, which is what makes a "random" fixture a test rather than a
  coin flip. `std/rand` is the opposite: unseeded, and gated on `rand`.
- **`below(n)` is a modulo reduction,** so its bias is acceptable for small `n` and
  not for a fairness-critical draw.

## See also

- [`bits`](/libraries/bits) and [`prng`](/libraries/prng)
- [`std/rand`](/stdlib/rand) for the unseeded source
- [`hash`](/libraries/hash) for turning a buffer like `packed` into a key
