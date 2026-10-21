---
title: "Types"
description: "How kelpc type checks a program without type variables: expected types, generic instances, traits, dyn coercion and the try operator. Covers the typed IR the checker produces."
isPublished: true
tags: "compiler"
---
The type checker, `infer.rs`, gives every expression a concrete type and writes the typed IR in `tir.rs`.
It has no type variables and no unification.
Each expression gets its type when it is checked, and the checker passes down the type the context expects.

## Types

`enum Ty` (`types.rs`) lists the types the checker can produce.
It has no variable variant, so every node of the typed IR has a concrete type.
The variants include:

- the scalars `I32`, `I64`, `U32`, `U64`, `F32`, `F64`, `Bool`, `Char`, `Unit`, `Str`, `U8`, `U16`, `Usize` and `Isize`;
- the owned types `Bytes`, `String` and the borrowed `View`;
- `Struct(String)`, which is used for both `datac` and `enum`, keyed by its canonical name;
- `List`, `Box`, `Map`, `Array`, `Atomic`, `Thread`, `Mutex`, `RwLock`, `Condvar`, `Handle` and `Ptr`;
- `Ref { mutable, inner }` for borrows, `Dyn` and `BoxDyn` for trait objects;
- `Fn`, `Closure` and `ScopedFn` for function values;
- `ConstInt` for const generic arguments.

`Option<T>` and `Result<T, E>` are not builtins.
They are ordinary generic enums in `std/option.kp:39` and `std/result.kp:32`.

## Where types come from

Four sources give an expression its type.

1. **The expected type.** `check_expr` (`infer/expr.rs`) takes an optional expected type.
   Call arguments, typed `val` initializers, `return` values, field initializers and block tails all pass one.
   A `val` with no written type takes the type of its initializer.
2. **Integer literals.** `int_lit_ty` (`infer/builtin_sigs.rs`) takes the expected integer type.
   Without one, the literal is `i32`.
   `check_int_literal` (`infer/builtin_sigs.rs`) rejects a value that does not fit.
3. **Generic arguments.** `bind_type_params` (`infer/generics.rs`) matches the written parameter types against the argument types.
   `bind_from_expected` (`infer/generics.rs`) fills the rest from the expected type.
   A type parameter that nothing binds is an error that asks for an annotation (`infer.rs`).
4. **Empty containers.** `List.empty()` with no type is allowed only as the initializer of a `val`.
   A later `push` decides the element type (`defer_empty_container`, `infer.rs`).

A parameter of a `datac` type is a borrow.
At a call site the checker borrows a plain place argument itself (`check_call_arg`, `infer/args_coerce.rs`).
Callers never write `&` for these parameters.

## Order of checking

`check_program` (`infer.rs`) runs three checks before any body:

- `check_pub_signatures` (`infer/exports.rs`), which applies the private-in-public rule;
- `check_extern_type_names` (`infer/fn_values.rs`);
- `check_program_pass` (`infer/program.rs`), which collects the declarations.

`check_program_pass` then checks each non-generic function body in source order (`infer/program.rs`).
It drains an instance worklist after that (`infer.rs`).
The checker runs this pass once, and a second time when it finds passdown modes that need a probe.

## Generics are monomorphised

A generic `datac` or `enum` is kept as a `GenericTemplate` (`infer.rs`).
Each use with concrete arguments creates one record or sum under the key `name<args>` (`instance_key`, `infer/env.rs`).
A generic function is a `FuncTemplate` (`infer.rs`).
Each distinct argument list gets one signature and one queued body.

The worklist checks each body with concrete types.
So a trait method call inside the body resolves against the concrete impl.
The checker stops after `MAX_FUNCTION_INSTANTIATIONS` (2048, `infer.rs`) instances, with an error about a generic function that grows without bound (`infer.rs`).

## Traits

- `collect_traits` (`infer/pd_wiring.rs`) records each trait's methods, supertraits, associated types and generic parameters.
- `collect_trait_impls` (`infer/trait_checks.rs`) records which type implements which trait.
- A normal impl may leave out a method that has a default body.
  A blanket impl (`impl<T: B> Trait for T`) must write every method.
- `check_trait_bounds` (`infer/claims_impls.rs`) checks the bounds on type arguments at each call.
- `I::Item` style projections are resolved by `assoc_type_of` (`infer/claims_impls.rs`).

### Dynamic dispatch

`&dyn Trait` and `Box<dyn Trait>` are created by `coerce_to_dyn` (`infer/args_coerce.rs`) and `coerce_box_to_dyn` (`infer/args_coerce.rs`).
`check_dyn_object_safety` (`infer/trait_checks.rs`) refuses a trait with associated types, and a trait with a method that cannot be called through a trait object.
The vtables go into `tir::Program.dyn_vtables`.

## Closures and function values

A `fun` literal is checked by `check_fn_literal` (`infer/loops_closures.rs`).
It takes parameter types from the expected function type when it has none.
Its body becomes a separate function with a generated key.

The literal's value is one of three forms:

- `FnRef`, when it captures nothing;
- `ClosureLit`, for an owned closure with captures;
- `ScopedClosureLit`, for a `scoped fun` that does not escape.

A plain function used where a closure is expected is wrapped with `FnToClosure` (`infer.rs`).

## The try operator

`check_try` (`infer/when_try_blocks.rs`) handles `?`.
`try_shape` (`infer/generics.rs`) accepts an enum with exactly two variants: `Ok` and `Err`, or `Some` and `None`.
Otherwise the checker reports an error.

The operand must be an enum held by value, and the enclosing function must return a try-shaped enum.
Both must agree on whether the failure carries a payload.
When the failure types differ, the checker looks for `impl From<Source> for Target` (`find_from_conversion`, `infer/when_try_blocks.rs`).
The result of `?` has the type of the success payload.

## The typed IR

`tir::Program` (`tir.rs`) holds the structs, enums, passdowns, functions, grants, gated functions, drop types, dyn vtables and the other tables the backends read.
`tir::Expr` (`tir.rs`) has a `kind`, a resolved `ty` and a `span`.
Borrowck and both code generators read this form.

## Tests

- `tests/compile_and_run.rs` runs most of the behaviour tests, using the fixtures under `tests/fixtures/`.
  Their names group by feature: `traits_*`, `closure_*`, `try_*`, `generic_*`, `const_generics_*` and `impl_trait_*`.
- `tests/check.rs` covers the output of `kelpc check`, not the type rules.

## See also

- [Front end](/compiler/frontend)
- [Ownership and drops](/compiler/ownership)
- [Backends](/compiler/backends)
- [Language: generics](/language/generics)
- [Language: traits](/language/traits)
