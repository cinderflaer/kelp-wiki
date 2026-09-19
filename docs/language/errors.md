# Errors and panics

Source section:
[`syntax.md` §18](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Kelp has **no exceptions and no `try`**. A failure is a value: `Option<T>` when
the failure carries nothing, `Result<T, E>` when it carries something. A
condition that cannot be handled becomes a `panic`, which ends the process.

## `Option` and `Result`

Both are ordinary enums, and the compiler knows their *shape*, not the module
they came from, so a program's own declaration of either works identically:

```kelp
enum Option<T> {
    Some(val value: T)
    None
}

enum Result<T, E> {
    Ok(val value: T)
    Err(val error: E)
}
```

Neither has methods: an `enum` carries no methods in v1, so the combinators are
free functions in [`std/option`](../stdlib/option.md) and
[`std/result`](../stdlib/result.md).

```kelp
val parsed = str.parse_i64(text)
if let Ok(n) = parsed {
    print(n + 1)
}

if option.is_none(o = maybe) {
    print("nothing")
}

print(result.unwrap_or(r = parsed, fallback = 0))
```

## `?`: propagation

`expr?` evaluates `expr`; if it carries a failure, that failure is returned out of
the enclosing function, otherwise the expression's value is the success payload.

```kelp
fun quarter(n: i64).R: result.Result<i64, str.ParseErr> {
    val h = half(n = n)?
    return half(n = h)
}
```

- The enclosing function must return the same shape with the **same failure
  payload type**. v1 has no error conversion: `Result<i64, String>` cannot be
  propagated out of a function returning `Result<i64, IoErr>`: `result.map_err`
  is the bridge.
- A function returning `Unit` (including `main`) has nowhere to propagate to.
- The value composes: `1 + half(n = n)?`.
- A failure returns immediately, dropping the frame's locals exactly as a
  `return` does.
- It moves a payload out of the operand, so a **borrow cannot be an operand**.

## `panic` and `assert`

`panic(message)` ends the program with a non-zero status; `assert(cond)` is the
checked form (`panic: assertion failed`).

```
panic: assertion failed
panic: i32.to_u64: value out of range
panic: Bytes.get: index out of bounds
panic: String.from_bytes: input is not valid utf-8
```

Almost everything that can fail with no value to return panics: out-of-range
indices, popping an empty list, `option.unwrap` on `None`, a failing syscall, a
division by zero in [`complex.div`](../libraries/complex.md), a scale mismatch in
[`decimal`](../libraries/decimal.md).

**The divergence rule.** A block whose *last statement* is a `panic(...)`
diverges, so it satisfies any declared return type, including a borrowed one.
That is what makes a "this cannot happen" accessor expressible:

```kelp
fun unwrap<T>(o: &Option<T>).R: T {
    if let Some(v) = o {
        return v
    }
    panic("Option.unwrap: value is None")
}
```

It applies to a function body's tail and nowhere else: a `panic` cannot be the arm
of an `if`/`when` used as a value.

## Which to use

| Situation | Tool |
| --- | --- |
| absent value | `Option<T>` |
| failure with a reason | `Result<T, E>` |
| failure the caller cannot act on | `panic` |
| invariant that must hold | `assert` |
| a library's accessor for a known-valid conversion | `panic` at the end, per the divergence rule |

## See also

- [`std/option`](../stdlib/option.md), [`std/result`](../stdlib/result.md)
- [Control flow](control-flow.md) for `if let` and `when`
- [Pitfalls](pitfalls.md)
