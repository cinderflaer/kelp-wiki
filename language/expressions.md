---
title: "Operators and expressions"
description: "Operator precedence and arithmetic, bitwise operators and shifts, == on user types, borrows, the ? operator and tuple values."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §5](/design/syntax).

## Precedence

From the loosest binding to the tightest:

| Level | Operators | Associativity |
| --- | --- | --- |
| 1 | `\|\|` | left |
| 2 | `&&` | left |
| 3 | `==` `!=` | left |
| 4 | `<` `<=` `>` `>=` | left |
| 5 | `\|` (bitwise or) | left |
| 6 | `^` (bitwise xor) | left |
| 7 | `&` (bitwise and) | left |
| 8 | `<<` `>>` | left |
| 9 | `+` `-` | left |
| 10 | `*` `/` `%` | left |
| 11 | unary `-` `!` `~` `&` `&mut` `*`, postfix `?`, call, field access | none (binds tightest) |

> **The bitwise operators bind tighter than the comparisons**
>
> Unlike C, and deliberately:
>
> ```kelp
> if flags & MASK == 0 { }   // Kelp: (flags & MASK) == 0
> ```
>
> In C the same line reads `flags & (MASK == 0)`, which is the classic bug.
>
> `|` stays looser than `^`, which stays looser than `&`, so masking still
> reads the way C programmers expect (`a | b & c` is `a | (b & c)`); only the
> comparison boundary moved.

## Arithmetic

```kelp
val a = 7 / 2        // 3: integer division truncates toward zero
val b = -7 % 3       // -1: % follows the dividend's sign, as in C
val c = 7.0 / 2.0    // 3.5
```

- Integer `/` truncates toward zero and `%` follows the dividend's sign.
- **Division by zero is undefined.** It is not checked at run time.
- Integer `+`, `-` and `*` overflow is **not checked**: it wraps. If a wrap
  matters, use the checked or saturating helpers in
  [`mathx`](/libraries/mathx).
- Float arithmetic is IEEE: `nan`, `inf` and `-0.0` behave as usual, and
  `math.is_nan` / `math.is_finite` exist to test them.
- A `datac` or `enum` gets `+ - * / %`, unary `-` and `< <= > >=` by implementing
  the [`std/ops`](/language/operator-traits) traits, and `"${x}"` and `print(x)` by
  implementing `fmt.Display`; see
  [Operator traits and `Display`](/language/operator-traits). Builtin types keep
  their builtin operators.

## Evaluation order

Kelp evaluates expressions **strictly left to right**. This includes call
arguments, template interpolations, binary operands, constructor fields and
list elements. Each expression is evaluated once. `&&` and `||` keep their
usual short-circuit rule: the right side runs only when the left side requires
it, and runs after the left side.

This is a language rule, not a property of one backend. It makes side effects
in a template predictable:

```kelp
print("removed ${items.remove(0)}, ${items.len()} left")
```

removes first, then reads the length, on both the LLVM backend and the C
backend. Code may still bind intermediate results when that makes it easier to
read, but it does not need to do so for backend agreement.

## Bitwise

`& | ^ << >> ~` require two integers **of the same type** (or one, for `~`) and
produce that type. `bool` is not a bitwise domain: `a & b` on two booleans reads
as a non-short-circuiting `and`, and `&&` is right there.

A shift count is the same type as the value. A shift by an amount outside
`0..width` (a negative one included, on a signed type) is checked at run time
like an out-of-bounds index and panics with `shift amount out of range`, on both
backends, hosted and freestanding. A shift by a *constant* amount that is already
out of range is a compile error naming the type and the amount. `>>` on a signed
type is arithmetic (sign-propagating), and `~x` is `0 - x - 1`, so on a `u32` it
flips all 32 bits. Mask it (`~x & 255`) when you wanted a byte.

`x.wrapping_shl(n)` and `x.wrapping_shr(n)` are the escapes that mask the amount
to `n & (width - 1)` instead of panicking. A shift whose amount is a literal in
range carries no check.

```kelp
fun shift(x: u32, n: u32) => u32 = x << n

fun main() {
    print(shift(1, 31))
    print(shift(1, 32))
    print("unreachable")
}
```

The panic
goes to standard error. On a terminal the `print` line appears first, as below.
When standard output is a pipe or a file, the `print` output is buffered until
the program exits, so the panic line comes first there:

```text
2147483648
panic: shift amount out of range
```

The exit status is 1 and `unreachable` is never printed; the panic names no
amount.

A constant amount never reaches run time:

```kelp refused
fun main() {
    val x: u32 = 1
    print(x << 33)
}
```

```text
$ kelpc check shift_const_too_wide.kp
error: a shift by 33 is not defined for a 'u32', whose width is 32 bits: the amount has to be in 0..32 (use wrapping_shl/wrapping_shr to mask it)
  --> shift_const_too_wide.kp:3:11
```

A named `const` amount is folded and refused the same way. For example,
`x >> AMOUNT` with `const AMOUNT: u8 = 8` on a `u8` fails with `a shift by 8 is
not defined for a 'u8', whose width is 8 bits`.

The masking forms take the amount modulo the width. Here `one: u32 = 1` and
`big: u32 = 0x80000000`:

```kelp
print(one.wrapping_shl(33))   // 2, the amount is 33 & 31
print(one.wrapping_shl(32))   // 1
print(big.wrapping_shr(35))   // 268435456, the amount is 35 & 31
```

The legal extremes behave as written: `1u8 << 7` is `128`, `255u8 << 4` is `240`
(the high bits are lost, as in every wrapping step), `1i32 << 31` is
`-2147483648` and `-8i32 >> 31` is `-1`.

```kelp
val masked = flags & 3
val high = byte >> 4
val low = byte & 15
val flipped = ~byte
```

## Equality

`==` and `!=` work for scalars, for two `View` values (byte-wise and
length-aware, exactly like `view.eq`), and for a `View` against a `str` (the
`str` is viewed first). Comparing two `str` values is refused, because it would
compare addresses; use `str.eq`.

**A type gets `==` and `!=` by declaring `eq`.** A `datac` or `enum` `T` that
declares `fun T.eq(other: &T) => bool` gets the operators from that method:

```kelp
datac P(val x: i32, val tag: i32)

fun P.eq(other: &P) => bool = self.x == other.x && self.tag == other.tag

fun main() {
    val a = P(x = 1, tag = 1)
    val b = P(x = 1, tag = 1)
    val c = P(x = 2, tag = 1)
    print(a == b)   // true
    print(a != c)   // true
}
```

- `a == b` means `a.eq(&b)` and `a != b` means `!a.eq(&b)`. The front end
  rewrites the operator into that call *before* borrow checking and code
  generation, so both are ordinary calls of the declared body and no backend
  gains an operator. Each operand is evaluated exactly once, left to right, and
  is only borrowed, never moved, so an owned binding, a `&T`/`mut T` borrow, or
  a mix of the two all compare.
- `eq` alone is enough for the operator. A `Map` *key* still needs the pair,
  `hash` and `eq`, and a lone `hash` is still refused
  ([Collections](/language/collections)).
- The signature is fixed: exactly one parameter, a **shared borrow** of `T`,
  returning `bool`. The compiler refuses any other shape where the method is
  declared. For example:

  ```
  error: 'P.eq' must take 'other: &P': a lookup compares the caller's key against an entry the caller does not own, so the argument cannot be moved
  ```

- **Nothing is derived.** A `datac` or `enum` without a declared `eq` cannot be
  compared, and `<`, `<=`, `>` and `>=` are refused on any user type that has no
  ordering impl:

  ```
  error: cannot compare 'P' values with '==': a datac has no generated equality
  error: cannot compare 'P' values with '<': a datac has no generated equality
  ```

- The two operands must be the same type: `cannot compare 'A' with 'B'`.

## Borrows and dereference

```kelp
val r = &c                 // shared borrow
var w = &mut c             // exclusive borrow
val field = (*r).count     // dereference, then field access
(*w).count = 9             // dereference, then write
```

`&x` borrows, `a & b` masks: position decides. See
[Ownership and borrowing](/language/ownership) for the rules the checker enforces.

## The `?` operator

`expr?` evaluates `expr` and, if it carries a failure, **returns that failure out
of the enclosing function**. Otherwise the expression's value is the success
payload.

```kelp
fun quarter(n: i64) => result.Result<i64, String> {
    val h = half(n = n)?          // half returns Result<i64, String>
    return result.Result.Ok(value = h / 2)
}
```

Rules (§5.2):

- It works on `Option` **or** `Result`. The compiler checks the shape of the enum,
  not the module it came from.
- The enclosing function must return an enum of the same shape, with the same
  failure payload type, or one that an `impl From<E1> for E2` converts: `?` calls
  `E2.from(e1)` when the two differ ([Generic traits](/language/generic-traits)).
  Without such an impl, `Result<i64, String>` cannot be propagated out of a
  function returning `Result<i64, IoErr>`.
- A function returning `unit` (including `main`) has nowhere to propagate to.
- The value composes: `1 + half(n = n)?`.
- A failure returns immediately, so the enclosing function's locals are dropped
  on the way out, exactly as any `return` drops them.
- `?` is postfix and binds tighter than every binary operator. Because it moves a
  payload out of the operand, **a borrow cannot be an operand**: match a
  borrowed operand with `when` or `if let` instead.
- It applies to the expression it is written on and to nothing else, so a tuple
  is never its operand. When a tuple is the *success* payload, `?` reaches the
  `Result` the element is and hands the tuple back: with
  `fun mk(n: i32) => Result<(i32, i32), String>`, the line
  `val (a, b) = mk(n)?` binds the tuple and takes it apart. A tuple is not an
  `enum`, so `?` written on the tuple itself is the ordinary "the operand must be
  an `enum`" refusal ([Types](/language/types)).

## Tuple values

`(lo, hi)` is a tuple value, and `(i32, i32)` is its type: two or more positions,
in order ([Types](/language/types)).

```kelp
val pair = (1, 2)
val (lo, hi) = min_max(xs)      // destructuring reads every position
val first = pair.0              // or one position by constant index
```

- `(e)` is the parenthesized expression `e`, not a one-element tuple: `val x =
  (5)` binds an `i32`.
- `()` is the absent value, of type `unit`. You can bind it, return it and pass it,
  but you cannot print it or store it in a tuple, a field or a container.
- A position is read by a **constant index**: `pair.0`, and `pair.1.0` for a
  nested tuple. The index is a literal; reading an owned position of a local is a
  partial move, as for a `datac` field. A destructuring binding
  ([Bindings and assignment](/language/bindings)) reads several at once.
- `print` takes a scalar, a `str` or a `String`. To print a tuple, print each
  position.

## Assignment

Assignment and compound assignment (`+=`, `-=`, `*=`, `/=`, `%=`) are covered on
[Bindings and assignment](/language/bindings).

## See also

- [Control flow](/language/control-flow)
- [Operator traits and `Display`](/language/operator-traits)
- [Ownership and borrowing](/language/ownership)
- [Errors and panics](/language/errors)
