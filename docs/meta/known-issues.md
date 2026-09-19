# Known issues

The defects that affect **valid** Kelp programs, with a repro each. Everything
here was found by compiling and running real code: the examples in this wiki, all
twenty-five `fpl` libraries, and the standard library's own surface.

Environment for every report: `kelpc 0.2.2`, commit `3a2f6f9`, default `c` backend,
clang 21.1.8, Linux. The `asm` backend's own refusals are *not* listed: refusing a
construct by name is its documented behaviour.

The full reports, including the generated C, are in the loose file
`KelpLANG/bugreports.md` next to the repositories.

**BUG-1, BUG-2 and BUG-3 are fixed** on `main`, each with a regression fixture in
`kelpc/tests/fixtures/`; the reports stay here as the record the fixes were
written against, each with a **Fixed** note. The only open defect on this page is
the `pd var` one below.

---

## BUG-1: an owned local inside an `if let` arm or a `for` body gets its drop emitted out of scope

**Fixed.** `borrowck::DropPlan` keyed every drop point by source span, and
desugaring deliberately gives several distinct blocks one span: `if let`'s
synthesized `else` block carried the `then` block's span, and a `for` loop's
element block and its `while` body both carried the loop body's span. The plan now
keys a block's drops by the block's *identity* — both passes reach the same
`tir::Block` — and `tir::Block` carries no span at all, so no future key can be a
span by accident. Fixture: `heap_drops_in_desugared_blocks.kp`, also in the
AddressSanitizer list.

**Severity:** high. Valid Kelp is refused, and with a different nesting it would be
a bogus or double drop.

**Triggers:** an owned local (`String`, `Bytes`, `List`, `Map`, or a `datac`
holding one) declared inside

- the arm of an `if let`, or
- the body of a `for`.

**Does not trigger:** a plain `if`/`else` block, or a `while` body.

```kelp
enum Maybe {
    Yes(val value: i64)
    No
}

fun main() {
    val m = Maybe.Yes(value = 1)
    if let Yes(v) = m {
        var xs: List<i32> = List.empty()   // the drop lands outside this block
        xs.push(v.to_i32())
        print(xs.len())
    }
}
```

```
$ kelpc run b1.kp
error: cc failed:
build/b1.c:737:42: error: use of undeclared identifier 'kelp_xs'; did you mean 'kelp_m'?
```

The generated C declares and drops `kelp_xs` correctly inside the arm, and then
drops it **again in the `else` branch**, where the name does not exist:

```c
kelp_List__i32 kelp_xs = kelp_List__i32__empty();   // line 730: declaration
kelp_list_drop__i32(&kelp_xs);                      // line 733: correct drop
...
} else {
    kelp_list_drop__i32(&kelp_xs);                  // line 737: out of scope
}
```

The same shape appears at a `for` loop's exit path. Both are `c`-only: the `asm`
backend refuses the construct by name first.

**Workarounds:** declare the owned local before the block; move the body into a
helper function that owns the local; or use a plain `if` when the pattern is not
needed.

---

## BUG-2: a closure parameter that borrows a module-declared type emits a typedef before the type exists

**Fixed.** `types::container_elem_c_type` is the spelling a type gets inside a
typedef emitted before the `datac`s, and it now walks through a borrow — a `&Item`
parameter is spelled `const struct tag_Item*`, the forward-declared tag, rather
than `const struct_Item*`, a typedef name that does not exist yet. Fixture:
`closure_datac_borrow_param.kp`.

**Severity:** high for library authors. It makes any callback API over a module's
own type impossible to declare: `json` cannot offer `each_value(v, f)`, and
`listx`/`std/list` are fine only because their element type is a builtin.

```kelp
datac Item(val n: i64)

fun each(items: &List<Item>, f: closure(&Item)) {
    var i: usize = 0
    while i < items.len() {
        f(items.get(i))
        i += 1
    }
}

fun main() {
    var xs: List<Item> = List.empty()
    xs.push(Item(n = 1))
    each(xs, fun(x: &Item) = print(x.n))
}
```

```
$ kelpc run b2.kp
error: cc failed:
build/b2.c:546:29: error: unknown type name 'struct_Item'
build/b2.c:558:21: error: unknown type name 'struct_Item'
```

In the generated C, the closure typedef uses the typedef-name `struct_Item`, but
only the *tag* is forward-declared at that point:

```c
543: struct tag_Item;                             // tag forward-declared
546:     void (*fn)(void*, const struct_Item*);   // ...but this names struct_Item
563: typedef struct tag_Item { ... } struct_Item; // which only exists here
```

The identical program with a builtin element type (`closure(&i64)`) compiles and
runs.

**Workaround:** index the container in the caller and keep the closure parameter a
builtin type: the callback-free shape `json` documents (`count_nodes`,
`depth_of`, `collect_strings`).

---

## BUG-3: warning noise in the generated C

**Fixed**, both kinds. A condition that already renders as one parenthesized
group — every binary expression, `when`'s tag test included — is no longer wrapped
a second time, so `if a == b` emits `if (a == b)`; and a conversion bound the
source's own range rules out is dropped, so `i32.to_u32` no longer compares an
`int32_t` against `4294967295`. A fresh `json` build that emitted ~47 warnings now
emits none.

**Severity:** low (no miscompilation observed), but visible on every fresh build
and it buries real diagnostics.

Two kinds, both from `codegen_c`:

- extraneous parentheses on nearly every equality comparison:
  `if ((a == b))` → `-Wparentheses-equality`;
- a tautological out-of-range compare in the `i32.to_u32` bound check: the upper
  half is unreachable for an `i32` source → `-Wtautological-constant-out-of-range-compare`.

A program that pulls in `json` emits about 47 of these before the first real error.

---

## `pd var` does not thread through a call chain

A module-scope `pd var` counter is not seen by a function that only *calls* a
function which reads the passdown. That is why
[`testkit`](../libraries/testkit.md) takes an explicit `mut Report` parameter
instead of a global tally, and the pattern is worth copying:

```kelp
fun tally(r: mut Report, cond: bool, name: &str) { ... }   // not a `pd var`
```

---

## Not bugs

Noted so nobody re-investigates them:

- The `asm` backend refusing a construct by name (`does not support the enum
  Maybe yet`) is the documented design: a construct it cannot lower is refused,
  not silently miscompiled.
- A method call on a returned temporary being refused
  (`set.union(a, b).len()`) is the borrow rule for a receiver-derived return, and
  the diagnostic names the fix.
- `Option`/`Result` having no methods, and every combinator being a free function,
  is the v1 design (an `enum` carries no methods).
- Integer `+`/`-`/`*` wrapping silently is documented behaviour, which is why
  [`mathx`](../libraries/mathx.md) exists.
- `str` and `View` not being comparable with `==` is deliberate: `str.eq` is the
  comparison.

## See also

- [Pitfalls](../language/pitfalls.md): errors you can fix by writing different code
- [Contributing](contributing.md): how to report one of these
