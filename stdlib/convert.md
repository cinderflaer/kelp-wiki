---
title: "`std/convert`"
description: "The conversion traits From<T> and Into<T>. `?` calls `From` when an operand's failure type differs from the function's. No blanket impls, so Into is never derived. Ungated and freestanding."
isPublished: true
tags: "stdlib, errors"
---
`From<T>` and `Into<T>`. Ungated, pure language, and admitted to the freestanding
set.

```kelp
impl "std/convert"
```

```kelp
pub trait From<T> {
    fun from(value: T).return: Self
}

pub trait Into<T> {
    fun Self.into().return: T
}
```

`from` has no receiver, so it is called on the type: `AppErr.from(value = e)`, or
through a bound, `X.from(value = v)` for `fun f<X: convert.From<i32>>(...)`. A
type may implement several instances (`From<IoErr>`, `From<i32>`) and the call
picks one by the argument's type.

`?` uses `From` directly: in a function that returns `Result<_, AppErr>`, an
operand `Result<_, IoErr>` is propagated when `impl convert.From<IoErr> for
AppErr` exists, and the failure is converted by calling it. `Into` is declared
for programs that want to spell a conversion as a method; **nothing derives it
from `From`**, so a type that wants `into` writes its own
`impl convert.Into<U> for X`, and `?` never consults it.

A worked example with the `?` conversion is in
[Generic traits, `From` and `?` conversion](/language/generic-traits).

## See also

- [Generic traits, `From` and `?` conversion](/language/generic-traits)
- [Errors and panics](/language/errors)
- [`std/result`](/stdlib/result)
