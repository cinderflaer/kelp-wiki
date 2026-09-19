# `bits` (`BitSet`, `BitWriter`, `BitReader`)

A fixed-size `BitSet` over `Bytes`, and an MSB-first `BitWriter`/`BitReader`
pair for packing bit-fields narrower than a byte.

Needs only the bitwise operators (`& | ^ << >> ~`), which `u8`/`u32` have.

No capability.

```toml
[dependencies]
bits = "Juniper/fpl/bits"
```

```kelp
impl "deps/bits/lib" as bits
```

## Bit order

**Bit 0 is the most-significant bit of byte 0.** `write_bits`/`read_bits` write
and read their `n`-bit field most-significant-bit first: the order a wire format
or a compressed index almost always wants.

## `BitSet`

```kelp
datac BitSet(var data: Bytes, val n_bits: usize)
```

| Function | Returns | Notes |
| --- | --- | --- |
| `new(n_bits: usize)` | `BitSet` | allocates `(n_bits + 7) / 8` zeroed bytes |
| `bs.get(i: usize)` | `bool` | **panics** `bits.BitSet.get: index out of bounds` when `i >= n_bits` |
| `bs.set(i: usize, v: bool)` | `Unit` | same panic |
| `bs.len()` | `usize` | the declared bit count |
| `bs.count_ones()` | `usize` | walks every bit |
| `bs.clear()` | `Unit` | zeroes the whole backing buffer |

`data` is a public field, so a caller can hand the raw bytes to a hash or a
socket.

## `BitWriter`

```kelp
datac BitWriter(var out: Bytes, var pending: u8, var pending_bits: usize)
```

| Function | Returns |
| --- | --- |
| `writer_new()` | empty writer |
| `w.write_bit(bit: bool)` | `Unit` |
| `w.write_bits(v: u32, n: usize)` | `Unit`: the low `n` bits of `v`, `n` up to 32, MSB first |
| `finish(w: move BitWriter)` | `Bytes`: pads the last partial byte with zero bits and returns the buffer |

`finish` takes the writer **by value** (`move`): a `mut` receiver only borrows,
and moving `out` out of a borrowed receiver is the partial move v1 refuses, so
getting the `Bytes` out needs ownership of the whole writer. After `finish` the
writer is gone.

Writes are buffered in `pending` until a full byte accumulates, then pushed to
`out`.

## `BitReader`

```kelp
datac BitReader(val data: Bytes, var pos: usize)
```

| Function | Returns |
| --- | --- |
| `reader_new(data: move Bytes)` | reader over `data`, at bit 0 |
| `r.read_bit()` | `bool`; **panics** `bits.BitReader.read_bit: no bits left` |
| `r.read_bits(n: usize)` | `u32`, `n` up to 32, MSB first |
| `r.remaining_bits()` | `usize`: `data.len() * 8 - pos` |

`reader_new` takes the `Bytes` by `move`.

## Example

```kelp
impl "deps/bits/lib" as bits

fun main() {
    var bs = bits.new(10)
    bs.set(0, true)
    bs.set(9, true)
    print(bs.get(0))
    print(bs.get(1))
    print(bs.len())
    print(bs.count_ones())
    bs.clear()
    print(bs.count_ones())

    var w = bits.writer_new()
    w.write_bit(true)
    w.write_bits(5, 4)
    val out = bits.finish(w)
    print(out.len())
    print(out.get(0))

    var r = bits.reader_new(out)
    print(r.read_bit())
    print(r.read_bits(4))
    print(r.remaining_bits())
}
```

Output:

```
true
false
10
2
0
1
168
true
5
3
```

The written stream is `1` then `0101`, padded to `10101000` = 168.

## Notes

- The `BitSet` is fixed size at construction; there is no grow, and `n_bits` is
  not a multiple of 8's worth of slack for you.
- No `and`/`or`/`xor` between two `BitSet`s, no population-count intrinsic,
  no search-for-set-bit.
- `read_bits` returns a `u32`, so a field wider than 32 bits is not expressible
  in one call.
- A write past a byte boundary is padded on the left (high-order bits) because
  writing is MSB-first: a stream read back with a `BitReader` sees exactly the
  bits written, with trailing zeros after the last one.
