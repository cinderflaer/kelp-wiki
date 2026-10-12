---
title: "Traits and static dispatch"
description: "Traits: methods with optional default bodies, supertraits, impl Trait for Type, bounds such as fun f<T: A + B>, static dispatch, &dyn trait objects, generic and blanket impls."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §9.5 and §9.5.1-9.5.2](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

A `trait` is a named set of methods. `impl` makes a type provide them, and a
generic function may then require that its type parameter implements one. A
method may carry a **default body**, a trait may name **supertraits**, and a
trait may be implemented for a **builtin** type that already carries methods. A
bound is dispatched **statically**: the method a `T` calls is the one the
concrete type declares, resolved once per instantiation, exactly as
[Generics and type parameters](/language/generics) resolves any type parameter.
The dynamic form is a **trait object**: `&dyn Name`, a borrowed fat pair and a
vtable, which is a section below, and the owned `Box<dyn Name>`
([Owned trait objects](/language/box-dyn)).

## Declaring a trait

```kelp
trait Shape {
    fun Self.area().return: f64
    fun Self.describe().return: String { return "a shape" }
    fun mut Self.scale(f: f64)
}

trait Named: Shape {
    fun Self.name().return: str
}
```

A trait is a top-level declaration. Its body is one or more methods in the
receiver form of [Methods and receivers](/language/methods), with `Self` where
the method's type would be. A method with **no body** is a **signature**:
`fun [mut] Self.name([param, ...])[.return: T]`, no `=` and no `{ ... }`.

- **A method with a body is a default method**: `fun Self.describe().return: String
  { ... }`, written exactly like an ordinary method, with `Self` standing for
  the implementing type. A default body may call the trait's other methods
  through `self` (`self.area()`), and it is checked once per implementing type,
  exactly as a generic function's body is.
- **A trait may name supertraits** after a `:`, one or more trait names
  separated by `+`: `trait Named: Shape { ... }`. Implementing `Named` for a
  type requires an `impl Shape for` that type; the relation is transitive and
  must be acyclic.
- `Self` names the implementing type. It is also legal in the other types a
  method names, where it means the same thing:
  `fun Self.smaller_than(other: &Self).return: bool`.
- `mut` on the receiver is part of the signature, and the impl has to match it.
- The trait name is an ordinary top-level name. `pub trait Shape` exports it the
  way a `pub datac` is exported, and a trait declared in another module is
  reached through the alias as `shape.Shape`.
- A trait can take type parameters, as in `trait Scale<T>`. See
  [Generic traits](/language/generic-traits). A trait method cannot take type
  parameters of its own: `fun Self.m<T>()` inside a trait is refused. A signature
  names only `Self`, the trait's own parameters, and the types its module exports.
- `Drop` is the one name a user cannot use. `trait Drop` is refused where it is
  written, with the destructor spelling in the message:

  ```
  error: the trait 'Drop' is built in: a type's destructor is written 'fun mut T.drop()', not through a trait
  ```

  `fun mut T.drop()` is the destructor spelling. The `hash` and `eq` pair is also
  fixed by name ([Collections](/language/collections)).

## Implementing a trait

```kelp
datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = r * r * 3.14159
    fun mut Self.scale(f: f64) { r = r * f }
    // `describe` is omitted: the trait's default is used.
}

trait Counts {
    fun Self.count().return: i32 { return 0 }
}

// A trait whose methods are all defaulted is implemented by an empty block.
impl Counts for Circle {}
```

The impl line is `impl Trait for Type { ... }`. The parser tells it from an
import by the token after `impl`: a **string literal** is `impl "path"` (an
import), and an **identifier** is this form. The block declares one method per
declared signature, and each one is an ordinary method, so inside it the type's
fields are read and written by their bare names. The receiver is written
`Self`, not the type's own name, so the block reads the same whether it sits in
the trait's module or the type's.

- **A defaulted method may be omitted**, and the impl gets the trait's default,
  monomorphized per implementing type. It may instead **override** it, with
  exactly the declared signature. A method with no default must be implemented.
  An impl block whose trait declares only defaulted methods may be empty
  (`impl Counts for Circle {}`).
- **Coherence**: at most one impl of a trait for a type in the whole program. A
  second one is an error naming both:

  ```
  error: trait 'Shape' already has an impl for 'Circle' (written in module 'traits_duplicate_impl'): a trait is implemented for a type at most once
  ```

- **The impl lives in the trait's module or in the type's module**, and nowhere
  else. That is what keeps the type's own module able to add a behaviour, and
  the trait's module able to supply an impl for a type it did not declare,
  without a third module inventing a relation the two owners never agreed to:

  ```
  error: 'impl shape.Shape for circle.Circle' is written in module 'bad', which owns neither: an impl lives in the trait's module ('shape') or in the type's ('circle')
  ```

  For a **builtin type** the impl lives in the trait's module, because a builtin
  has no module of its own. See
  [Implementing a trait for a builtin type](#implementing-a-trait-for-a-builtin-type).
- **The type has to be a `datac`, an `enum`, or a builtin that already carries
  methods.** A container, a tuple, an array and a borrow are refused by name,
  and a generic *instantiation* (`impl Name for Pair<i32, String>`) is its own
  error:

  ```
  error: implementing a trait for a generic instantiation is not in this slice: a trait is implemented for a declared 'datac' or 'enum' name, or for a builtin type that already carries methods
  ```
- **Every non-defaulted declared signature must be implemented**, with exactly
  the declared signature: the same receiver spelling (`Self`, with or without
  `mut`), the same parameter names and types in the same order, and the same
  return type. A missing method, an extra method, a mismatched signature and a
  mismatched receiver are distinct errors, each naming the trait and the
  method.

  ```
  error: trait 'Shape' declares 'fun Self.name().return: str', and 'impl Shape for Circle' does not implement it: add 'fun Self.name().return: str { ... }' to the block
  error: 'shrink' is not declared by trait 'Shape': an 'impl' implements exactly the trait's methods, so remove it or add the signature to the trait
  error: method 'area' does not match trait 'Shape': the trait declares 'fun Self.area().return: f64', the impl writes 'fun Circle.area().return: i32'
  error: method 'grow' takes its receiver differently than trait 'Grow' declares it: the trait writes 'fun mut Self.grow(by: f64)', the impl writes 'fun Circle.grow(by: f64)'
  ```

- **An inherent method of the same name on the same type is refused at the
  impl**, because it would leave two answers to one call. Rename one of them:

  ```
  error: 'impl Shape for Circle' declares 'Circle.area', which 'Circle' already has as an explicit method: a trait method and an explicit method cannot share a name, so rename one of them
  ```

- An impl naming a trait that is not declared gets
  `'impl Shape for Circle' names no declared trait: declare 'trait Shape { ... }' first (or import the module that does)`.

Because a trait impl's methods *are* the type's methods, nothing else changes:
an impl method is reached through a value exactly as an inherent one is, it is
emitted through the same per-type function, and a trait method
on a type that also declares its own `drop` still drops through the same
generated `kelp_drop_<T>`.

## Bounding a type parameter

A type parameter carries bounds after a `:`, separated by `+`:

```kelp
fun area_of<T: Shape>(s: &T).return: f64 = s.area()
fun describe<T: Shape + Named>(s: &T).return: f64 = s.area() + s.name_length()
```

- **Inside the body, a method call on a `T` resolves exactly as it would on the
  concrete type**, because a generic function's body is already checked once per
  instantiation with `T` bound to the concrete type. The bound is what makes
  that resolution succeed; the emitted call is the ordinary direct call the
  type's method already had.
- **At every call, the type argument must implement every bound.** The check
  runs where the instantiation is created, so a satisfied call compiles to the
  same monomorphized function it would have without the bound, and an
  unsatisfied one is an error naming the callee, the type and the trait:

  ```
  error: the call to 'area_of' needs 'Point' to implement the trait 'Shape', and it does not: write 'impl Shape for Point { ... }' in the trait's module or in the type's
  ```

- **A supertrait is satisfied transitively**: a type that implements `B`, where
  `B: A`, satisfies a `T: A` bound, because the `impl B for` the type had to
  come with an `impl A for` it. A `T: B` may also call `A`'s methods on its
  argument. A cycle in the supertrait relation is refused where it closes:

  ```
  error: the supertrait relation is cyclic: B inherits from A inherits from B: a trait cannot inherit from itself
  ```

- Bounds are checked transitively, and that needs no symbolic reasoning:
  `fun f<T: A>(x: &T) { g(x) }` where `g<U: A>` is fine for every type that
  satisfies `f`'s bound, and calling `g<U: B>` from the same body is an error at
  that call as soon as `f` is instantiated with a type that does not implement
  `B`. A generic function that is never called is never checked, exactly as in
  [Generics and type parameters](/language/generics).
- As with any generic function, an explicit instantiation may be written at the
  call site: `area_of<Figure>(s = f)`.

## Static dispatch, end to end

This program compiles and runs with the output shown:

```kelp
trait Shape {
    fun Self.area().return: f64
    fun mut Self.scale(f: f64)
}

datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = r * r * 3.14159
    fun mut Self.scale(f: f64) { r = r * f }
}

fun area_of<T: Shape>(s: &T).return: f64 = s.area()

fun main() {
    var c = Circle(r = 2.0)
    print(area_of(c))
    c.scale(f = 2.0)
    print(area_of(c))
}
```

```
12.566360
50.265440
```

Nothing in either backend changes for static dispatch. There is no vtable, no
witness argument, no new `tir` node and no new C type, so a freestanding build
has traits too.

A trait may be implemented for a `datac` and for an `enum`, and a method on a
generic type may call a bounded generic with the receiver's own parameter. The
cross-module project works both ways the module rule allows: the type's module
implements an imported trait, and the trait's module implements a type it did
not declare (`tests/projects/traits_cross`, which prints `12.000000`, `27.000000`,
`circle`, `ring`, `12.000000`).

## Default methods and supertraits

The default body, the override, the empty impl, a supertrait and a transitive
supertrait bound, in one program:

```kelp
trait Shape {
    fun Self.area().return: i32
    fun Self.describe().return: i32 { return 7 }
    fun Self.summary().return: i32 { return self.area() + self.describe() }
}

trait Named: Shape {
    fun Self.name().return: i32 { return 3 }
}

datac Circle(val r: i32)

impl Shape for Circle {
    fun Self.area().return: i32 = r * r
    fun Self.describe().return: i32 = 9
}

// Every `Named` method is defaulted, so the block is empty; the `Shape` impl
// beside it is what the supertrait requires.
impl Named for Circle {}

fun area_of<T: Shape>(x: &T).return: i32 = x.area()
fun describe<T: Named>(x: &T).return: i32 = x.area() + x.name()

fun main() {
    val c = Circle(r = 3)
    print(c.area())       // 9, the written impl
    print(c.describe())   // 9, the override
    print(c.summary())    // 18: the default calls area() and describe()
    print(c.name())       // 3, the default the empty impl inherited
    print(area_of(c))     // 9, a `T: Shape` bound
    print(describe(c))    // 12: `Named: Shape`, so name() and area() both resolve
}
```

```
9
9
18
3
9
12
```

`summary` is checked against `Circle`, not against `Self` in the abstract, so
its call of `self.describe()` reaches `Circle`'s override. An override still has
to match the declared signature, and a default that calls a method the type does
not have is refused at the impl that uses it:

```
error: method 'describe' does not match trait 'Shape': the trait declares 'fun Self.describe().return: i32', the impl writes 'fun C.describe().return: i64'
error: datac 'C' has no method 'nope'
```

A missing supertrait is refused where the subtrait impl is written:

```
error: 'impl Named for C' is missing its supertrait: 'Named' needs 'impl Shape for C' as well, because trait 'Named' inherits from 'Shape'
```

A default body's **types, free function calls and consts** resolve in the
trait's module, but its capabilities and passdowns are read in the implementing
module, so a default that reaches a capability-gated call the trait's module
owns may be refused at the impl. `tests/projects/traits_default_cross` is a
default body naming the trait module's own type; it prints `10` and `10`.

## Implementing a trait for a builtin type

A trait may be implemented for a builtin type that **already carries methods**,
which is exactly the set the compiler's method table names: the integer scalars
(`i32`, `i64`, `u32`, `u64`, `u8`, `u16`, `usize`, `isize`), `String`, `str`,
`Bytes`, `View`, and an `Atomic<T>` alias.

```kelp
trait Doubler {
    fun Self.double().return: i32
    fun Self.triple().return: i32 { return self.double() + self.double() + self.double() }
}

trait Named {
    fun Self.label().return: String
}

impl Doubler for i32 {
    fun Self.double().return: i32 = self + self
}

impl Named for String {
    fun Self.label().return: String = String.from_str("a string")
}

fun twice<T: Doubler>(x: T).return: i32 = x.double() + x.double()
fun label_of<T: Named>(s: &T).return: String = s.label()

fun main() {
    val n = 6
    print(twice(5))      // 20
    print(n.triple())    // 36: the default calls the impl's double() three times
    val s = String.from_str("hi")
    print(label_of(s))   // a string
}
```

```
20
36
a string
```

The receiver is `self`, passed by value for a `Copy` scalar and borrowed for
`String`/`Bytes`, exactly as the compiler's own methods on those types are, so
`n.triple()` and `twice(5)` reach the same `i32#double` key an ordinary receiver
call uses.

**The orphan rule**: because a builtin has no module of its own, the impl has to
be declared in the trait's module. An impl for a builtin anywhere else is
refused by name:

```
error: 'impl shape.Doubler for i32' is written in module 'bad', but 'i32' is a builtin type, which has no module: implement a trait for a builtin in the trait's own module ('shape')
```

A builtin that carries **no** methods (`bool`, `char`, `f32`, `f64`, `unit`) is
refused too, and so is a container, a tuple, an array, a borrow, a function type
and a handle:

```
error: 'f64' is a builtin type that carries no methods, so 'impl Doubler for f64' has nothing to add: implement the trait for a 'datac'/'enum', or for a builtin whose methods the compiler already provides ('i32', 'String', ...)
```

## Trait objects: `&dyn` and `&mut dyn`

A trait is normally a bound on a type parameter, and the concrete type is known
at every call. An **object-safe** trait may also be used behind a borrow as a
**trait object**, `&dyn Name` or `&mut dyn Name`, so one function can call one
of several types through a runtime vtable. The value is still a borrow: the
compiler never owns a trait object.

```kelp
trait Shape {
    fun Self.area().return: f64
    fun Self.describe().return: String { return "a shape" }
    fun mut Self.scale(f: f64)
}

trait Named: Shape {
    fun Self.name().return: str
}

datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = r * r * 3.14159
    fun mut Self.scale(f: f64) { r = r * f }
}

impl Named for Circle {
    fun Self.name().return: str = "circle"
}

fun report(s: &dyn Shape).return: f64 {
    print(s.describe())
    return s.area()
}

fun grow(s: &mut dyn Shape) {
    s.scale(2.0)
}

fun through_named(s: &dyn Named).return: f64 = s.area()

fun main() {
    var c = Circle(r = 2.0)
    print(report(&c))
    {
        val d: &dyn Shape = &c
        print(report(d))
    }
    grow(&mut c)
    print(report(&c))
    print(through_named(&c))
}
```

```
a shape
12.566360
a shape
12.566360
a shape
50.265440
50.265440
```

The first `report(&c)` prints the default `describe` and `Circle`'s area. The
block binds a `&dyn Shape` to `d`, and `report(d)` forwards it on to another
function (the block is what releases `d`'s borrow of `c` before `grow` takes
`&mut c`). `grow` scales through the vtable, and `through_named` calls the
supertrait's `area` through a `&dyn Named`, which has `Shape`'s methods first.

### Where a trait object may be written

- The two type spellings are `&dyn Name` and `&mut dyn Name`. A bare `dyn Name`
  is refused, and the message names the owned form this language does not have:

  ```
  error: 'dyn Shape' is not a type on its own: an owned trait object is written 'Box<dyn Shape>', and a borrowed one '&dyn Shape'
  ```

- A trait object is legal **as a parameter type and as a local binding type**
  (`val`/`var`). A parameter includes a `fun` literal's parameter and the
  parameter of a function *type*. It is refused everywhere else by name: as a
  `.return:` return type, as a `datac`/`enum` field or payload, as a
  `List`/`Box`/`Map`/`Atomic`/array element or argument, as a tuple element, and
  as a `static`'s type.
- `Name` must be a declared trait:

  ```
  error: '&dyn Nope' names no declared trait: declare 'trait Nope { ... }' first (or import the module that does)
  ```

- The `mut` in `&mut dyn Name` is the whole mutability story. A `mut Self`
  method is callable through a `&mut dyn Name`; through a `&dyn Name` it is
  refused by name:

  ```
  error: 'Counter.bump' takes an exclusive receiver, and a shared '&dyn Counter' cannot call it; make the receiver '&mut dyn Counter'
  ```

### Coercion

A `&T` where `T` implements `Trait` coerces to `&dyn Trait` at exactly two
places, and both are implicit, that is, the caller writes the ordinary borrow:

- a **call argument**: `report(&c)` where `report(s: &dyn Shape)`;
- a **typed `val`/`var` binding**: `val d: &dyn Shape = &c`.

The rules, in full:

- The operand is an ordinary `&x` or `&mut x` (or a value that already is a
  `&T`, for example a parameter of a borrow type). A plain place with no `&` is
  not coerced, and the message says to write `&value`:

  ```
  error: expected '&dyn Shape', found 'Circle': a trait object is built from a borrow, so write '&value' (or '&mut value' for '&dyn Shape')
  ```

- `&T` coerces to `&dyn Trait`. `&mut T` coerces to both `&dyn Trait` and
  `&mut dyn Trait`. A `&T` never coerces to `&mut dyn Trait`.
- `T` must implement `Trait` (an `impl Trait for T` anywhere in the program):

  ```
  error: expected '&dyn Shape', found '&Other': 'Other' does not implement 'Shape', so write 'impl Shape for Other' first
  ```

- A `&dyn Trait` value coerces to the **same** `&dyn Trait` type, so one can be
  passed on to another function. It does not coerce to a different trait, and
  there is no upcast from `&dyn B` to `&dyn A` when `B: A`.
- An `&mut` operand also has to be a durable place, exactly as an `&mut`
  argument of a declared parameter does: `&mut <temporary>` is refused.

### Representation and vtables

A `&dyn Trait` value is **two pointers**: the address of the borrowed value (the
*erased data pointer*) and the address of a static, read-only vtable. It is
`Copy`, it owns nothing, and dropping it drops nothing: it is a borrow, exactly
like a `&T`, and the value it points at is still owned by whoever lent it.

- **One vtable per `(Trait, Type)` pair actually used in a coercion.** A pair
  that is never coerced to has no vtable. Each vtable is emitted once per
  program, as `static const` data.
- **One slot per method, in one fixed order**: the trait's supertraits first,
  recursively in declaration order, then the trait's own methods in source
  order. A supertrait method is callable on a `&dyn` of the subtrait.
- **Each slot is a thunk** whose first parameter is the erased data pointer and
  whose remaining parameters and return are the method's own. The thunk calls
  the concrete method (the same `Type#name` key an ordinary receiver call uses),
  including a defaulted method's synthesized per-impl copy.
- **A method call goes through the vtable**: `s.area()` where `s: &dyn Shape`
  becomes `s.vtable.area(s.data)`. The call is bounds-free and
  allocation-free: no libc, no allocator, no witness argument and no runtime
  type tag. A freestanding image can use `&dyn`, and the vtables cost only
  read-only data.
- A trait implemented for a `Copy` builtin is reached through `&dyn` too: a
  `val n: i32 = 21` passed to `twice(d: &dyn Doubler)` prints `84`, because the
  thunk loads the scalar out of the erased pointer.

### Object safety

A trait used behind `dyn` must be object safe. The rule is exact, and the
compiler refuses the trait by name, naming the offending method:

- No method may **return `Self`**, anywhere in its return type:

  ```
  error: '&dyn Cloneable' is not allowed: method 'dup' returns 'Self', and a trait object does not know the concrete type it would build
  ```

- No method may **take another `Self`**: no parameter other than the receiver
  may mention `Self`:

  ```
  error: '&dyn Comparable' is not allowed: method 'same_as' takes a 'Self' parameter, which a trait object cannot pass (the vtable erases the concrete type); make the parameter a borrow of a concrete type, or use a generic function instead
  ```

- Two methods of the same name are refused too, because the vtable names one
  field per method. This can only happen through a supertrait that repeats a
  name. A generic method is already impossible: a trait method declares no type
  parameters, so there is nothing to erase.

Object safety is checked where the `dyn` type is written, so the error names the
trait and the method even if that `dyn` value is never built.

### Borrows and soundness

The coercion is not a new borrow: the `&x` inside it is the borrow the language
already had, and the borrow checker sees the same node. So:

- a `val d: &dyn Shape = &c` keeps `c` borrowed for the rest of the scope,
  exactly as `val p = &c` does, and `c` cannot be moved or reassigned while `d`
  lives. A second borrow that conflicts is refused (`cannot borrow 'c' as
  exclusive: already borrowed as shared`), which is why the example scopes `d`;
- `&mut c` coerced to a `&mut dyn` is an exclusive borrow, so it excludes every
  other borrow, shared or exclusive;
- a `&dyn` passed as a call argument is a call-scoped borrow, released after the
  call, exactly as the `&x` it came from is;
- a `&dyn` never outlives its referent because it can never be stored and never
  returned. There is no lifetime syntax in v1 and v1 does not add one.

## What traits still do not do

These pages cover the features that grew out of traits: [associated types](/language/associated-types),
[generic traits and `From`](/language/generic-traits), the owned
[`Box<dyn Name>`](/language/box-dyn), the
[operator traits and `Display`](/language/operator-traits), and
[`impl Trait` in argument position](/language/const-generics#impl-trait-in-argument-position).

The following are still refused. Each is refused where it is written, with a message:

- **A bare `dyn Name`** (an unsized value in place). Refused by name.
- **`&dyn` in a field, a payload, a container element, a return type or a
  `static`.** These are positions where a borrow may not live. `Box<dyn Name>` is
  the owned form that can be stored and returned.

  ```
  error: '&dyn Shape' cannot be a return type: a borrowed trait object points at a value the caller owns, and a return would have to name how long that borrow lives; take it as a parameter, or return an owned value
  ```

- **Upcasting `&dyn B` to `&dyn A`** when `B: A`. A `&dyn` coerces only to its
  own type, and the same holds for `Box<dyn>`.
- **Object-unsafe traits** (returning `Self` or taking another `Self`), a generic
  trait and a trait with an associated type behind `dyn`, refused as above.
- An impl for **one instantiation** (`impl Name for Pair<i32, String>`). Blanket
  impls (`impl<T: A> B for T`) shipped in 26.10.4 and are described in
  [Blanket impls and coherence](#blanket-impls-and-coherence). The refusal reads:

  ```
  error: an impl for a generic type writes the type's parameters, in order, as its own: 'impl<T: Bound> Trait for Type<T>'; an impl for one instantiation ('Type<i32>') is not supported - implement the trait for a non-generic wrapper, or give the type an inherent method
  ```

## Generic impls and `where` (26.10.3)

An impl may declare type parameters, which are the generic type's own, in order,
with their bounds:

```kelp
trait Describe { fun Self.describe().return: i32 }
impl Describe for i32 { fun Self.describe().return: i32 = self }

datac Pair<A, B>(val a: A, val b: B)

impl<A: Describe, B: Describe> Describe for Pair<A, B> {
    fun Self.describe().return: i32 { return self.a.describe() * 10 + self.b.describe() }
}

fun show<T: Describe>(x: &T).return: i32 { return x.describe() }
```

- `Pair<i32, i32>` and `Pair<Pair<i32, i32>, i32>` implement `Describe`;
  `Pair<i32, bool>` does not, and the error names the argument whose bound fails.
- The impl's methods are template methods of the type, so dispatch stays static
  and an instance is made when it is used. The impl is checked against the trait
  where it is used, not where it is written; it must write every method the trait
  has no body for (it cannot use a default).
- An associated type may name the parameters (`type Item = I::Item`), so
  `impl<I: Iterator> Iterator for Twice<I>` works and `for x in twice(it)` walks
  it ([Iterators](/language/iterators)).
- The parameters are written as the type declares them (the same rule as a
  receiver on a generic type).
- **`where`** is a second spelling of a bound on a function or an impl:
  `fun f<T, U>(a: &T, b: &U) where T: A, U: A + B`. It bounds a parameter from the
  `<...>` list. A bound on a projection, such as `where I::Item: Display`, is not
  supported yet.
- Not supported on a generic impl: an impl for one instantiation, a const
  parameter on an impl, a `dyn` of a generic impl, and operators through a generic
  impl.
- **Operators through a trait of your own.** Only the `std/ops` traits and
  `fmt.Display` are used by the operators and by `"${x}"`.

A bound says that the trait's methods exist. It does not say they are the only
methods in scope. A call to an inherent method of the concrete type, or to a
method of another bound on the same parameter, also compiles. A default body is
checked only for the impls that use it.

## Blanket impls and coherence

Since 26.10.4 an impl may cover every type that meets a bound. A blanket impl
takes one type parameter, which is the whole self type, and it names no trait
arguments:

```kelp
trait Describe { fun Self.describe().return: i32 }
impl Describe for i32 { fun Self.describe().return: i32 = self }

trait Tagged { fun Self.tag().return: i32 }
impl<T: Describe> Tagged for T {
    fun Self.tag().return: i32 { return self.describe() * 100 }
}

fun main() {
    val n: i32 = 7
    print(n.tag())        // 700: i32 is Describe, so it is Tagged
}
```

- A type has the blanket trait's methods when every bound on `T` holds for it.
  A type without `Describe` has no `tag`, and a generic function bounded by
  `T: Tagged` accepts `i32` and any other `Describe` type.
- Coherence is overlap-free, with no specialization: two impls of one trait may
  not overlap, whatever their bounds. So `impl Describe for i32` next to
  `impl<T: Shown> Describe for T` is refused, and the error names both impls.
- A bound that leads back to the blanket impl's own trait (`impl<T: Describe>
  Describe for T`) is refused.

Refused by name, with the reason in the message:

- a blanket impl of a trait with type arguments (`impl<T> Into<U> for T`), or one
  that binds an associated type or has a trait default;
- a `dyn` coercion of a type whose trait comes from a blanket impl (`&dyn Tagged`
  from a `&i32`), since the blanket impl has no vtable of its own;
- a bound that cannot be checked on a builtin container: `List<i32>` answers to
  its bare name, so `xs.tag()` is refused for a `Tagged` blanket on `Describe`;
- a bound on a projection (`where I::Item: Describe`), which is not supported yet.

## See also

- [Associated types](/language/associated-types)
- [Generic traits, `From` and `?` conversion](/language/generic-traits)
- [Owned trait objects: `Box<dyn Trait>`](/language/box-dyn)
- [Operator traits and `Display`](/language/operator-traits)
- [Const generics and `impl Trait` arguments](/language/const-generics)
- [Generics and type parameters](/language/generics)
- [Methods and receivers](/language/methods)
- [`datac` and `enum`](/language/data-types)
- [Operators and expressions](/language/expressions)
- [Limits in v1](/language/limits)
