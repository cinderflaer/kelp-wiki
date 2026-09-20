---
title: "`prng`: seeded, reproducible pseudo-randomness"
description: "xorshift64 (Marsaglia's xorshift with Vigna's multiplicative finishing step). Deliberately not std/rand - that module is gated and unseeded on purpose (unreproducible is the point of a system..."
isPublished: true
tags: "library, math"
---
xorshift64* (Marsaglia's xorshift with Vigna's multiplicative finishing step).
Deliberately **not** `std/rand`: that module is gated and unseeded on purpose
(unreproducible is the point of a system RNG), while this one exists so the same
seed always produces the same sequence: for tests, simulations, and anything
that needs to replay a run.

No capability: this is arithmetic on a `u64`, not a random source.

```toml
[dependencies]
prng = "Juniper/fpl/prng"
```

```kelp
impl "deps/prng/lib"
```

## Type

```kelp
datac Rng(var state: u64)
```

Constants: `MULT` (`2685821657736338717`), `SEED_FALLBACK` (the nonzero constant
`0` is remapped to).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `new(seed: u64)` | `Rng` | xorshift64* needs a nonzero state; seed `0` is remapped to `SEED_FALLBACK`, so every `u64` is a usable seed |
| `next_u64(r: mut Rng)` | `u64` | advances the state |
| `next_f64(r: mut Rng)` | `f64` | `[0, 1)`, from the top 53 bits of `next_u64` (an `f64` mantissa's width) |
| `below(r: mut Rng, n: u64)` | `u64` | `[0, n)`; **panics** `prng.below: n must not be 0` |
| `range(r: mut Rng, lo: i64, hi: i64)` | `i64` | `[lo, hi)`; **panics** `prng.range: hi must be greater than lo` |
| `shuffle_i32(r: mut Rng, xs: mut List<i32>)` | `Unit` | in place, Fisher-Yates back to front |
| `choice_i32(r: mut Rng, xs: &List<i32>)` | `i32` | **panics** `prng.choice_i32: list is empty` |

The `Rng` is threaded as a `mut` parameter, so each call consumes the state:
`var r = prng.new(42)` then `prng.next_u64(r)` mutates `r`.

## Modulo bias

`below` uses `next_u64() % n`, which has a small bias for an `n` that does not
divide 2⁶⁴ evenly. That is acceptable for the sizes this is meant for (a shuffle,
a sampled index), not for a fairness-critical draw.

## Example

```kelp
impl "deps/prng/lib"

fun main() {
    var r = prng.new(42)
    print(prng.next_u64(r))
    print(prng.next_u64(r))
    print(prng.below(r, 10))
    print(prng.range(r, -5, 5))
    val f = prng.next_f64(r)
    print(f >= 0.0)
    print(f < 1.0)

    var xs: List<i32> = List.empty()
    xs.push(1)
    xs.push(2)
    xs.push(3)
    xs.push(4)
    prng.shuffle_i32(r, xs)
    print(xs.len())
    print(prng.choice_i32(r, xs))

    var r2 = prng.new(42)
    print(prng.next_u64(r2))
    var r3 = prng.new(0)
    print(prng.next_u64(r3))
}
```

Output:

```
6255019084209693600
14430073426741505498
6
0
true
true
4
3
6255019084209693600
973819730272012410
```

Two generators seeded `42` produce the same first value; seed `0` produces the
`SEED_FALLBACK` stream.

## Notes

- Not cryptographically secure. Do not use it for keys, tokens or anything an
  attacker benefits from predicting.
- Only `List<i32>` has `shuffle`/`choice` helpers; there is no generic list form
  (a user module cannot overload, per syntax.md §7.2, and no generic random
  helper is written).
- `next_f64` gives `[0, 1)`; for a range use `below`/`range` on integers and
  scale yourself for floats.
- The generator has a period of 2⁶⁴−1 and a state of 64 bits; it is fast and
  replayable, not statistically strong by modern standards.
