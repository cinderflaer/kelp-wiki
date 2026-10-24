---
title: "Return types and `return`"
description: "The => T clause, expression and block bodies, what return does, the divergence rule for panic, and the rule that a returned borrow must come from a parameter."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §7.1 and §6.4](/design/syntax).

## The `=> T` clause

The return type is written **after** the parameter list, introduced by `=>`:

```kelp
fun add(a: i32, b: i32) => i32 = a + b     // expression body, requires =>
fun greet(name: &str) {                    // no => returns unit
    print(str.concat("hello, ", name))
}
```

- `=>` marks "this returns". There is no `->` return marker and no trailing type.
- **No `=>` means `unit`.** A function with no return clause returns the
  absent value.
- There is no inferred return type for a block body. The signature always says
  what comes back, and the body has to agree with it.
- `unit` has no representation, so it cannot be stored in a field, a tuple, a
  `List` element or a `Map` value. A binding of a `unit` value is allowed, and it
  holds nothing: `val x = noise()` compiles. A function that returns `unit` has
  nowhere for `?` to propagate to, and that includes `main`
  ([Errors and panics](/language/errors)).
- A generic function may write a type parameter in the return type
  (`fun identity<T>(x: T) => T`). `main` may not take type parameters
  ([Generics and type parameters](/language/generics)).

## Bodies

An **expression body** is `= expr`. It may write `=> T`, or leave the return
type out, and then the type of the expression is the return type:

```kelp
fun double(x: i32) => i32 = x * 2      // written return type
fun triple(x: i32) = x * 3             // return type taken from the body: i32
```

A body with no `=> T` is refused in these cases, and the type has to be written:

- the body calls itself, directly or through other bodies with no `=> T`; the
  error is `recursive expression-bodied function 'f' requires a '=> T' return type`,
  and the fix is to write the type on each function in the cycle;
- the body is a `when` with more than one arm, or an `asm` body;
- the function is generic, or is a method of a generic type, or is a trait method;
- the body's type is a borrow, since a return type is always owned;
- the function is `pub` and its type names a private type.

A **block body** is `{ ... }`, and its value comes from one of two places:

1. a `return expr` statement, or
2. the block's last expression, when that expression is the last thing in the
   block.

```kelp
fun abs_diff(a: i32, b: i32) => i32 {
    if a > b {
        return a - b
    }
    return b - a
}

fun max2(a: i32, b: i32) => i32 {
    if a > b { a } else { b }      // the last expression is the value
}
```

There are no semicolons, so "the last statement is an expression" is the only
signal for tail-expression status. An expression-bodied function does not use
`return` at all.

`return` with no value is allowed in a function with no `=> T`.

## What `return` does

- `return expr` delivers the value the signature promises. A mismatch between
  `expr` and `=>` is an error: `return type mismatch: expected 'i32', found 'str'`.
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
impl "std/option"

fun unwrap<T>(o: &option.Option<T>) => T {
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

A function whose `=> T` is a borrow must return something derived from its
**first reference parameter**:

```kelp
fun head(text: View, n: usize) => View = text.slice(0, n)

fun as_str(v: &Json) => &str {
    if let Str(s) = v {
        return s.as_str()
    }
    panic("json.as_str: value is not a string")
}
```

- A payload bound by a pattern counts as derived from the scrutinee it came out
  of, which is why the second function type-checks.
- `=> View` therefore means "a view of one of my parameters". A view of a
  local is refused by name:
  `cannot return a borrow of 'local': 'View' borrows from its first reference parameter 'text', so the returned value must be derived from 'text'`.
  Return an owned `String`, or take the view as a parameter.
- When a whole `when` is the returned value, the arm bindings are out of scope
  before the merged root is computed. Return from *inside* the arm
  (`if let S(s) = v { return s.as_str() }`) instead of returning the `when`.
- A `fun` literal cannot return a borrow: an indirect call has no parameter an
  elided lifetime could bind to. Return an owned value.
- A direct `as_str()` or `view()` binding promotes its temporary receiver, so the
  result remains valid for that binding's scope. A returned borrow still cannot
  escape the function, because its promoted owner ends with the frame:

  ```kelp refused
  impl "std/str"

  // error: a temporary would be dropped before the borrow is used
  fun bad() => str = String.from_str(s = "x").as_str()

  fun main() {
      val ok = String.from_str(s = "x").as_str()
      print(str.len(ok))
  }
  ```

  A field of a call's result follows the same rule: `val name =
  mkName().name.as_str()` is valid, while returning that borrow is not.

## See also

- [Functions](/language/functions)
- [Control flow](/language/control-flow) for `return` and the loop forms
- [Methods and receivers](/language/methods)
- [Ownership and borrowing](/language/ownership) for drops and the elision rule
- [Errors and panics](/language/errors) for `?`, `panic` and `assert`
