---
title: "User `Drop`"
description: "`fun mut T.drop()` gives a user `datac` or `enum` a destructor. It runs first at every drop point, then the fields drop; a moved value is not dropped, a partial move is refused, and a panic runs no destructor."
isPublished: true
tags: "language, ownership, kernel"
---
Owned values are already freed at the end of their scope, on every exit path
([Ownership and borrowing](/language/ownership)). A user **`Drop`** lets a type
run its own code at each of those drop points, so a lock flag can be coupled to
the value that holds it. The design is
[`plan/drop.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/drop.md).

## The surface

```kelp
datac LockGuard(val held: bool)

fun mut LockGuard.drop() {
    LOCK.store(value = false, order = atomic.Ordering.SeqCst)
}
```

`fun mut T.drop()` on a user `datac` or `enum` is that type's destructor. It
takes the value as an exclusive borrow (`mut` receiver), takes no parameters, and
returns nothing. There is no trait keyword, no `impl` block and no new
punctuation: the method name **is** the declaration, the shape A-12 slice 1
already chose for a declared `Map` key pair (`fun T.hash()` / `fun T.eq(other:
&T)`, syntax.md §9.4).

## Order of drops

When an owned value of a `Drop` type reaches a drop point, the generated drop
calls `fun mut T.drop()` **first** and then drops the fields recursively, in
declaration order (`enum`: the live variant's payload in declaration order).
Fields are dropped by the same generated `kelp_drop_<T>` the type already had, so
the user body is one extra call at the top and every existing drop point,
container drop and recursive drop reaches it unchanged.

The drop points are the ones the plan already had:

- the end of the owning block,
- before a `return`,
- reassignment of an owned `var`,
- an element a container frees,
- the drop of a containing `datac`/`enum`,
- the `atexit` drop of an owned `pd`.

Locals die last-in-first-out, so the field order above is the order within one
value, not across values.

The examples are the `kelpc/tests/fixtures/drop_*.kp` fixtures, hosted programs;
build one with `kelpc build <file.kp> -o <out>` and run it.

```kelp
datac Leaf(val tag: i32)

fun mut Leaf.drop() {
    print("leaf")
    print(self.tag)
}

datac Pair(val a: Leaf, val b: Leaf)

fun mut Pair.drop() {
    print("pair")
}

fun main() {
    val p = Pair(a = Leaf(tag = 1), b = Leaf(tag = 2))
    val l = Leaf(tag = 3)
    print("body")
}
```

```text
body
leaf
3
pair
leaf
1
leaf
2
```

`l` (declared last) drops before `p`; `p`'s own destructor runs before its two
fields, which drop in declaration order (`1`, then `2`).

A moved-out value is not dropped, exactly as before: a destructor cannot run for
a value that has an owner somewhere else.

```kelp
fun main() {
    val a = Leaf(tag = 1)
    val b = a
    print("moved")
}
```

```text
moved
leaf
1
```

Reassigning an owned `var` frees the value it replaces first:

```kelp
fun main() {
    var a = Leaf(tag = 1)
    a = Leaf(tag = 2)
    print("after")
}
```

```text
leaf
1
after
leaf
2
```

An `enum` runs its own body for every variant before the live variant's payload
drops (a payload-less variant still runs the body; only the field drop is
skipped). `drop_enum` prints `body`, then `maybe` twice, then `leaf 1`. A loop
body frees one value per iteration, and a `return` frees the frame's live locals
after the returned value is read (`drop_control_flow` prints `leaf 1`, the
returned `9`, `leaf 2`, `leaf 1`, the returned `0`, then `loop`, `leaf 10`,
`loop`, `leaf 11`).

## Containers and closures

A container drops each element through the element's own generated drop, so a
destructor runs for `List.clear`, for the element `List.pop` moves out (when that
new owner dies), and for a value held inside a `datac` held by a `List`.
`List<Guard>`, `Box<Guard>`, `Map<.., Guard>` (value drop), an
`Option<Guard>`-shaped enum and a `Guard` inside a `datac` inside a `List` all
work through the same function. A closure that captured a `Guard` owns it in its
environment and drops it where the environment is dropped, including on a worker
thread.

```text
$ ./drop_container
pushed
leaf
1
leaf
2
cleared
popped
3
holder
leaf
4
leaf
3
```

`List.pop` hands the element to the caller, so `3` drops when that binding dies,
last. A `Map<String, Guard>` prints `body`, `removed`, then `drop 1` for the
removed value and `drop 2` for the value the map still holds when it dies.

## What is refused

- **A partial move of a destructor-typed field or payload.** The partial-move
  lowering zeroes the slot the value came from, and the base's own drop would
  then run the destructor a second time on the empty slot. Move the value whole
  (`val g = holder`) or use it through a borrow.

```text
error: cannot move field 'leaf' out of 'h' by value: it is a type with a destructor, and a partial move zeroes the slot it came from, so the base's own drop would run that destructor a second time; take the whole value by moving it, or use it through a borrow
```

- **An explicit destructor call.** `g.drop()` is refused, because the value's
  drop already runs when the value dies and a second run would free a live
  resource twice.

```text
error: 'Leaf.drop' cannot be called: an explicit destructor call is an error, because the value's own drop already runs when its owner dies
```

- **Every derived-copy use.** A `Drop` type is not `Copy` (user types never are
  in v1) and is excluded from the derived-copy fixpoint, so `List<Guard>.clone()`
  and `List.slice`, `Map.values`/`get_or` and a `Map` key of a `Drop` type are
  refused rather than silently producing two owners of one resource.

```text
error: List<Leaf>.clone is not defined: 'Leaf' declares 'fun mut Leaf.drop()', and a type with a destructor is not `Copy`, so a second owner of the same resource would be freed twice
```

- **A declaration that is not the right shape.** A shared receiver, a parameter,
  a return value, a builtin receiver or a second destructor for the same type are
  each refused at the declaration.

```text
error: 'Leaf.drop' must take its receiver with 'mut': the drop body reads and may adjust the value it is running for, so write 'fun mut Leaf.drop()'
error: method 'Leaf.drop' is defined more than once
```

## A panic runs no destructor

There is still **no unwinding**. A `panic` abandons the frame: neither a
`defer` nor a destructor of any value in it runs, and the leak is the same one
the memory model already admits. On an ordinary exit a `defer` is spliced before
the block's ordinary drops, so a deferred action runs before the destructor of a
value in the same block.

```kelp
datac Leaf(val tag: i32)

fun mut Leaf.drop() {
    print("leaf")
}

fun main() {
    val a = Leaf(tag = 1)
    print("before")
    panic("boom")
}
```

```text
$ ./drop_panic >out 2>err
$ echo $?
1
$ cat out
before
$ cat err
panic: boom
```

`a`'s destructor never prints `leaf`. A destructor is not checked for being
idempotent, for dropping a value of the same type, or for being panic-free: a
destructor that panics is a panic from the drop point, with no unwinding to run
the remaining drops of the frame.

## See also

- [Ownership and borrowing](/language/ownership): the drop plan a destructor
  hooks into
- [Statics and `defer`](/language/statics-and-defer): `defer`, which runs before
  the destructors of its block
- [Concurrency in v1](/language/concurrency): a value moved into a worker
- [Errors and panics](/language/errors): the panic path, which runs no drop
