---
title: "`bigint`: arbitrary-precision integers"
description: "Arbitrary-precision integers over base-2\u00b3\u00b2 List<u32> limbs - from_i64, to_string, add, sub, mul, compare."
isPublished: true
tags: "library, math"
---
Arbitrary-precision integers over base-2³² `List<u32>` limbs: `from_i64`,
`to_string`, `add`, `sub`, `mul`, `compare`.

No capability.

```toml
[dependencies]
bigint = "Juniper/fpl/bigint"
```

```kelp
impl "deps/bigint/lib"
```

## Representation

```kelp
datac BigInt(val sign: i32, val limbs: List<u32>)
```

- `limbs` is little-endian base 2³²: limb 0 is the least significant.
- `sign` is `-1`, `0` or `1`.
- Zero is `sign = 0` with an empty limb list.
- `limbs` never carries a trailing zero limb, so two `BigInt`s with the same
  value always have the same representation, which is what makes `compare` a
  plain limb-by-limb walk.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `from_i64(n: i64)` | `BigInt` | `i64::MIN` is handled (its magnitude is built in `u64`, since negating it in `i64` overflows) |
| `zero()` | `BigInt` | `sign = 0`, empty limbs |
| `to_string(b: &BigInt)` | `String` | decimal, `-` prefix, `"0"` for zero |
| `compare(a: &BigInt, b: &BigInt)` | `i32` | `-1`, `0`, `1` |
| `add(a: &BigInt, b: &BigInt)` | `BigInt` | |
| `sub(a: &BigInt, b: &BigInt)` | `BigInt` | implemented as `add(a, negate(b))` |
| `mul(a: &BigInt, b: &BigInt)` | `BigInt` | schoolbook, O(n·m) |
| `negate(a: &BigInt)` | `BigInt` | |
| `normalize(sign: i32, limbs: move List<u32>)` | `BigInt` | drops trailing zero limbs and maps an all-zero magnitude to `sign = 0` |

Magnitude helpers, exposed and usable on their own:
`compare_mag(a: &List<u32>, b: &List<u32>) -> i32`,
`add_mag`, `sub_mag` (assumes `a >= b`), `clone_limbs`,
`div_small(limbs, divisor: u64) -> List<u32>`,
`mod_small(limbs, divisor: u64) -> u64`, `u64_to_str(n: u64) -> String`.

Constants: `BASE` (`4294967296`), `DECIMAL_CHUNK` (`1000000000`).

## No division

There is no `div`/`mod`/`divmod`. `to_string` works by repeatedly dividing the
limbs by 10⁹ with the single-limb `div_small`/`mod_small`, which is exactly the
piece a full long division would also need: a general long division is enough
more work than the rest of the library combined that it is deliberately out of
scope. Add it separately if a caller needs it.

## Example

```kelp
impl "deps/bigint/lib"

fun main() {
    val a = bigint.from_i64(123456789012345678)
    val b = bigint.from_i64(-987654321)
    print(bigint.to_string(&a))
    print(bigint.to_string(&b))
    print(bigint.compare(&a, &b))
    val s = bigint.add(&a, &b)
    print(bigint.to_string(&s))
    val d = bigint.sub(&a, &b)
    print(bigint.to_string(&d))
    val m = bigint.mul(&a, &b)
    print(bigint.to_string(&m))
    val n = bigint.negate(&b)
    print(bigint.to_string(&n))
    val z = bigint.zero()
    print(bigint.to_string(&z))
    print(bigint.compare(&z, &z))
    val huge = bigint.from_i64(1000000000)
    val huge2 = bigint.mul(&huge, &huge)
    val huge3 = bigint.mul(&huge2, &huge)
    print(bigint.to_string(&huge3))
}
```

Output:

```
123456789012345678
-987654321
1
123456788024691357
123456789999999999
-121932631124828531222374638
987654321
0
0
1000000000000000000000000000
```

## Notes

- `BigInt` is immutable data: every operation returns a fresh value; nothing
  mutates in place, so a loop of adding allocates per step.
- `to_string` of a huge number is O(digits²) in the worst case because each 10⁹
  chunk costs a pass over the limbs.
- There is no `from_str`, no comparison operators (`compare` returns the
  sign), no bit operations, no power.
