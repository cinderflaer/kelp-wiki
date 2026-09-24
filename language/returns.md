---
title: "Return types and `return`"
description: "Source section - syntax.md \u00a77.1 and \u00a76.4. The `.R: T` clause written after the parameter list, expression bodies against `return`, the divergence rule, and the elision rule for a borrowed return."
isPublished: true
tags: "language"
---
Source sections:
[`syntax.md` §7.1 and §6.4](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## The `.R: T` clause

The return type is written **after** the parameter list, introduced by `.R`:

```kelp
fun add(a: i32, b: i32).R: i32 = a + b     // expression body, requires .R
fun greet(name: &str) {                    // no .R: returns Unit
    print(str.concat("hello, ", name))
}
```

- `.R` marks "this returns". There is no `->` return marker and no trailing type.
- **No `.R` means `Unit`.** A function with no return clause returns the absent
  value.
- There is no inferred return type for a block body. The signature always says
  what comes back, and the body has to agree with it.
- `Unit` has no representation, so it is refused where a value has to be stored (a
  field, a `List` element, a `Map` value), while a binding of a `Unit` value is
  allowed and holds nothing: `val x = noise()` and `val y: unit = x` both compile,
  and a `Unit` parameter is not passed. A function returning `Unit` has nowhere for
  `?` to propagate to, which includes `main` ([Errors and
  panics](/language/errors)).
- A generic function may write a type parameter in the return type
  (`fun identity<T>(x: T).R: T`). `main` may not take type parameters
  ([Generics and type parameters](/language/generics)).

## Bodies

An **expression body** is `= expr`, and it requires `.R: T`:

```kelp
fun double(x: i32).R: i32 = x * 2
```

Writing `= expr` with no `.R` is refused with
`expression-bodied function requires a '.R: T' return type`.

A **block body** is `{ ... }`, and its value comes from one of two places:

1. a `return expr` statement, or
2. the block's last expression, when that expression is the last thing in the
   block.

```kelp
fun abs_diff(a: i32, b: i32).R: i32 {
    if a > b {
        return a - b
    }
    return b - a
}

fun max2(a: i32, b: i32).R: i32 {
    if a > b { a } else { b }      // the last expression is the value
}
```

There are no semicolons, so "the last statement is an expression" is the only
signal for tail-expression status. An expression-bodied function does not use
`return` at all.

`return` with no value is allowed in a function with no `.R: T`.

## What `return` does

- `return expr` delivers the value the signature promises. A mismatch between
  `expr` and `.R` is a `return type mismatch` error naming both types.
- `return` can appear anywhere in the block, so it is how a function leaves early.
- Returning drops the frame's locals on the way out, exactly as reaching the end
  of the body does ([Ownership and borrowing](/language/ownership)).
- A failure propagated with `?` returns immediately and drops the frame in the
  same way.

## The divergence rule

A block whose **last statement is `panic(...)`** diverges, so it satisfies any
declared return type, including a borrowed one. That is what makes a "this cannot
happen" accessor expressible:

```kelp
fun unwrap<T>(o: &Option<T>).R: T {
    if let Some(v) = o {
        return v
    }
    panic("Option.unwrap: value is None")
}
```

The rule applies to a function body's tail and nowhere else. A `panic` cannot be
the arm of an `if`/`when` used as a value, because that arm has to produce the
value the `if` produces.

## Returning a borrow: the elision rule

A function whose `.R: T` is a borrow must return something derived from its
**first reference parameter**:

```kelp
fun head(text: View, n: usize).R: View = text.slice(0, n)

fun as_str(v: &Json).R: &str {
    if let Str(s) = v {
        return s.as_str()
    }
    panic("json.as_str: value is not a string")
}
```

- A payload bound by a pattern counts as derived from the scrutinee it came out
  of, which is why the second function type-checks.
- `R: View` therefore means "a view of one of my parameters". A view of a local is
  refused by name:
  `cannot return this value as 'View': ... only a 'str' literal can be returned`.
  Return an owned `String`, or take the view as a parameter.
- When a whole `when` is the returned value, the arm bindings are out of scope
  before the merged root is computed. Return from *inside* the arm
  (`if let S(s) = v { return s.as_str() }`) instead of returning the `when`.
- A `fun` literal cannot return a borrow: an indirect call has no parameter an
  elided lifetime could bind to. Return an owned value.
- A call that returns a borrow of its receiver cannot be made on a temporary,
  because the temporary would be freed before the borrow could be used. Bind the
  receiver first ([Methods and receivers](/language/methods)):

  ```kelp
  // error: this call returns a borrow of its parameter 'self'
  print(set.union(a, b).len())

  val u = set.union(a, b)     // bind it first
  print(u.len())
  ```

  A field of a call's result is the same case one projection deeper, except that
  the compiler stages that temporary for the length of one call: reading the field
  or passing it as a borrow is fine, while handing the borrow back
  (`mkName().name.as_str()`) needs the binding.

## See also

- [Functions](/language/functions)
- [Control flow](/language/control-flow) for `return` and the loop forms
- [Methods and receivers](/language/methods)
- [Ownership and borrowing](/language/ownership) for drops and the elision rule
- [Errors and panics](/language/errors) for `?`, `panic` and `assert`
