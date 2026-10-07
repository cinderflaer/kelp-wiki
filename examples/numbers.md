---
title: "numbers"
description: "The numeric libraries in one program - exact big integers, fixed-point money, complex numbers, the arithmetic std/math omits, statistics, and a seeded generator."
isPublished: true
tags: "example, math"
---
The numeric libraries in one program: exact big integers, fixed-point money,
complex numbers, the arithmetic `std/math` omits, statistics, and a seeded
generator.

| | |
| --- | --- |
| Source | [`src/numbers.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/numbers.kp) |
| Needs | `bigint`, `decimal`, `complex`, `mathx`, `stats`, `prng` |
| Shows | where a float is the wrong tool, and where a random sequence must repeat |

## The dependencies

```toml
[dependencies]
bigint  = "Juniper/fpl/bigint"
decimal = "Juniper/fpl/decimal"
complex = "Juniper/fpl/complex"
mathx   = "Juniper/fpl/mathx"
stats   = "Juniper/fpl/stats"
prng    = "Juniper/fpl/prng"
```

Six libraries, six manifest lines, and none of them fetches another.

## The program

```kelp
impl "deps/bigint/lib"
impl "deps/decimal/lib"
impl "deps/complex/lib"
impl "deps/mathx/lib"
impl "deps/stats/lib"
impl "deps/prng/lib"
impl "std/option"
impl "std/str"

// A separate function, so the arithmetic stays out of `main`.
fun power_of_two(exponent: u32).return: bigint.BigInt {
    val two = bigint.from_i64(2)
    var result = bigint.from_i64(1)
    var i: u32 = 0
    while i < exponent {
        result = bigint.mul(&result, &two)
        i += 1
    }
    return result
}

// Money: a fixed scale, so 0.1 + 0.2 is exactly 0.30.
fun show_money(a: &decimal.Decimal, b: &decimal.Decimal) {
    val sum = decimal.add(a, b)
    val sum_text = decimal.to_string(&sum)
    print(str.concat("decimal   0.10 + 0.20 = ", sum_text.as_str()))

    // Multiplication is exact and widens the scale, here to 4.
    val product = decimal.mul(a, b)
    val product_text = decimal.to_string(&product)
    print(str.concat("decimal   0.10 * 0.20 = ", product_text.as_str()))
}

fun main() {
    // 2^64 exactly, which no i64 can hold.
    val big = power_of_two(64)
    val text = bigint.to_string(&big)
    print(str.concat("bigint    2^64 = ", text.as_str()))

    val dime = decimal.from_str("0.10", 2)
    val nickel = decimal.from_str("0.20", 2)
    if let Ok(a) = dime {
        if let Ok(b) = nickel {
            show_money(a, b)
        }
    }

    // Complex numbers: magnitude and angle.
    val z = complex.Complex(re = 3.0, im = 4.0)
    print("complex   |3+4i| = ${complex.abs(&z)}")
    print("complex   arg(3+4i) = ${complex.arg(&z)}")

    // The arithmetic std/math does not carry.
    print("mathx     gcd(12, 18) = ${mathx.gcd(12, 18)}")
    print("mathx     lcm(4, 6) = ${mathx.lcm(4, 6)}")
    print("mathx     is_prime(97) = ${mathx.is_prime(97)}")
    print("mathx     factorial(10) = ${mathx.factorial(10)}")

    // Checked arithmetic returns an Option instead of wrapping.
    val overflowed = mathx.add_checked_i64(9223372036854775807, 1)
    print("mathx     max + 1 = ${mathx.add_saturating_i64(9223372036854775807, 1)} (saturated)")

    // Statistics over a fixed list.
    var xs: List<f64> = List.empty()
    xs.push(2.0)
    xs.push(4.0)
    xs.push(4.0)
    xs.push(4.0)
    xs.push(5.0)
    xs.push(5.0)
    xs.push(7.0)
    xs.push(9.0)
    print("stats     mean = ${stats.mean(xs)}")
    print("stats     median = ${stats.median(xs)}")
    print("stats     population stddev = ${stats.stddev(xs)}")

    // A seeded generator is reproducible: same seed, same sequence.
    var rng = prng.new(42)
    print("prng      first = ${prng.next_u64(rng)}")
    print("prng      second = ${prng.next_u64(rng)}")
    print("prng      below(100) = ${prng.below(rng, 100)}")

    var deck: List<i32> = List.empty()
    deck.push(1)
    deck.push(2)
    deck.push(3)
    deck.push(4)
    deck.push(5)
    deck.push(6)
    deck.push(7)
    deck.push(8)
    prng.shuffle_i32(rng, deck)
    print("prng      shuffled 1..8 = ${deck.get(0)} ${deck.get(1)} ${deck.get(2)} ${deck.get(3)} ${deck.get(4)} ${deck.get(5)} ${deck.get(6)} ${deck.get(7)}")

    if option.is_none(o = overflowed) {
        print("mathx     max + 1 was caught, not wrapped")
    }
}
```

## Run it

```sh
kelpc run numbers.kp
```

## Output

```
bigint    2^64 = 18446744073709551616
decimal   0.10 + 0.20 = 0.30
decimal   0.10 * 0.20 = 0.0200
complex   |3+4i| = 5.000000
complex   arg(3+4i) = 0.927295
mathx     gcd(12, 18) = 6
mathx     lcm(4, 6) = 12
mathx     is_prime(97) = true
mathx     factorial(10) = 3628800
mathx     max + 1 = 9223372036854775807 (saturated)
stats     mean = 5.000000
stats     median = 4.500000
stats     population stddev = 2.000000
prng      first = 6255019084209693600
prng      second = 14430073426741505498
prng      below(100) = 46
prng      shuffled 1..8 = 5 1 2 4 3 6 7 8
mathx     max + 1 was caught, not wrapped
```

Every line is reproducible: the six seeded draws and the shuffle are the same on
every run, which is the property `std/rand` deliberately does not have.

## What to take from it

- **A `BigInt` is a `sign` plus base-2³² limbs, and every operation returns a new
  value.** `result = bigint.mul(&result, &two)` reads like an in-place multiply but
  allocates; the assignment moves the new value in and frees the old.
  There is no division, so `to_string` is the only decimal way out.
- **Explicit `&` is only allowed on a place.** `bigint.mul(&result, &two)` works
  because both are bindings; `&bigint.from_i64(2)` would be refused, which is why
  `two` is hoisted out of the loop. A parameter, by contrast, borrows a temporary
  for free.
- **`Decimal` carries its scale, and mixing scales panics.** `add` and `sub`
  require equal scales, `mul` adds them, and `rescale` rounds half away from zero.
  That is why `0.10 * 0.20` prints four decimals: the result's scale is the sum.
- **Checked arithmetic is an `Option`,** so `is_none` is `option.is_none`, not a
  method on the value. `result` has `is_ok`/`is_err`; `option` has
  `is_some`/`is_none`, and the two are different modules.
- **`stats` uses the population form** (divide by `n`), so a sample standard
  deviation needs the caller to scale it by `n / (n - 1)`.
- **`prng` is arithmetic on a `u64`, so it needs no capability**, unlike
  `std/rand`. The trade is that a seed of `0` is remapped, and the generator is
  not cryptographically secure.

## See also

- [`bigint`](/libraries/bigint), [`decimal`](/libraries/decimal), [`complex`](/libraries/complex)
- [`mathx`](/libraries/mathx), [`stats`](/libraries/stats), [`prng`](/libraries/prng)
- [Limits in v1](/language/limits) for what the numeric surface does not have
