---
title: "The rules of ownership"
description: "The four rules behind Kelp's ownership: one owner, borrows that end at their last use, moves, and drops at scope end, each with a program that compiles and prints the shown output."
isPublished: true
tags: "language, ownership, memory"
---
Four rules decide what a Kelp program may do with a value. Each section below
states one rule and gives a complete program that compiles and prints the output
shown. The programs were compiled with the 26.10.5 release compiler. The refusals
these rules produce are on [Common refusals](/memory/refusals).

Owned values are `String`, `Bytes`, `List`, `Map`, `Box`, and any `datac` or
`enum`. A `View`, a `str` and a `&T` are borrows, and they own nothing.

## 1. Every owned value has one owner

A value's owner is the binding, field, element or temporary that holds it. When
the owner's scope ends, the value is dropped. A `datac` with a `drop` method runs
that method at the same point, and locals drop in the reverse of the order they
were declared. A resource is closed at that point. A memory value in a hosted build
is not freed there: the collector reclaims its memory later (see
[Working with Kelp memory](/memory)).

```kelp
datac Leaf(val tag: i32)

fun mut Leaf.drop() {
    print("drop ${self.tag}")
}

fun main() {
    val a = Leaf(tag = 1)
    val b = Leaf(tag = 2)
    print("end of main")
}
```

```text
end of main
drop 2
drop 1
```

## 2. A plain parameter borrows

Passing an owned value to a plain parameter lends it. The callee can read the
value, and the caller still owns it afterwards.

```kelp
fun show(s: String) {
    print(s)
}

fun main() {
    val name = String.from_str("kelp")
    show(name)
    show(name)
    print(name.len())
}
```

```text
kelp
kelp
4
```

## 3. A move transfers ownership

Assigning an owned value to another name moves it, and so does a `move T`
parameter. After a move the old name is empty, and using it is an error.

```kelp
fun consume(s: move String) => int = s.len()

fun main() {
    val a = String.from_str("kelp")
    print(consume(a))
}
```

```text
4
```

`consume` now owns the string, and it is dropped when `consume` returns. The caller
cannot print `a` after the call, and a return value moves out the same way.

## 4. A borrow ends at its last use

A `val` that holds a borrow keeps its owner pinned only until the borrow is read
for the last time. In this program `r` is last read before `w` is taken, so the
exclusive borrow is accepted even though `r` is still in scope.

```kelp
datac Counter(var count: i32)

fun main() {
    var c = Counter(count = 1)
    val r = &c
    print((*r).count)
    var w = &mut c
    (*w).count = 9
    print(c.count)
}
```

```text
1
9
```

Move the `print((*r).count)` line below the `&mut` and the checker refuses the
program with `cannot borrow 'c' as exclusive: already borrowed as shared`. The
last use of `r` is what counts, not the line where `r` was declared.

## 5. Drop runs at scope end

A block ends a scope, and the values declared in it drop when the block ends. A
moved value is not dropped by the place it came from, so only the new owner runs
the destructor.

```kelp
datac Leaf(val tag: i32)

fun mut Leaf.drop() {
    print("drop ${self.tag}")
}

fun main() {
    val a = Leaf(tag = 1)
    {
        val b = Leaf(tag = 2)
        print("inner")
    }
    print("outer")
}
```

```text
inner
drop 2
outer
drop 1
```

Assigning to a `var` drops the old value first, and a `return` drops the frame's
other live locals after the returned value is read. A `panic` runs no destructor
at all; see [Drop](/language/drop).

## What the compiler refuses

The checker enforces the four rules on every path. The common refusals are:

- **Use after a move.** The moved name cannot be read again.
- **A borrow kept across a mutation.** The owner cannot change while a borrow of
  it is still read later.
- **A borrow stored in a field.** A `datac` may hold a `View` only when the owner
  of its text is moved into an earlier field of the same value.
- **A temporary borrowed into a call.** A borrow needs a place to point into, and
  a call's result is not one.

Each of these has its exact message, and its fix, on
[Common refusals](/memory/refusals).

## See also

- [Patterns](/memory/patterns): the rules applied to real data structures
- [Ownership and borrowing](/language/ownership): the complete rules
