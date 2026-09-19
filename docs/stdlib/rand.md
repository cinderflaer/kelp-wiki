# `std/rand`

An unseeded system random source. **Gated on `rand`.**

```kelp
impl "std/rand" with caps(rand = [])
```

| Function | Returns | Notes |
| --- | --- | --- |
| `rand.u64()` | `u64` | a full-width random value |
| `rand.below(n: u64)` | `u64` | in `[0, n)` |
| `rand.bytes(n: usize)` | `Bytes` | `n` random bytes, for a token or a salt |

```kelp
impl "std/rand"

fun main() {
    val r = rand.u64()
    print(r >= 0)                 // any u64 is a valid draw
    print(rand.below(10) < 10)
    print(rand.bytes(16).len())
}
```

## Notes

- **Unseeded on purpose**: this is the system source, so it is not reproducible.
  For anything that must replay — tests, simulations, a shuffle you want to
  reproduce from a seed — use [`prng`](../libraries/prng.md), which needs no
  capability at all because it is arithmetic on a `u64`.
- `rand.below` is the modulo-reduction helper here; `prng.below` has the same
  modulo bias caveat.
- There is no `shuffle`, no range helper, no float draw in this module. `prng`
  has all three.

## See also

- [`prng`](../libraries/prng.md) — seeded, reproducible, capability-free
- [Capability patterns](../reference/capability-patterns.md)
