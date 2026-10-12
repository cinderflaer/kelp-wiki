---
title: "Common refusals"
description: "The compiler messages for the mistakes manual memory produces most often: use after a move, a borrow kept across a mutation, a borrow stored in a field, and a temporary borrowed into a call. Each is copied from kelpc check, with the fix."
isPublished: true
tags: "language, ownership, memory, errors"
---
Each section below is a program that `kelpc check` refuses. The error text is copied
from the 26.10.5 release compiler. The `-->` line gives the file and position; the
directory part of the path is cut here, and the compiler prints the full path. Under
each refusal is the change that fixes it, which compiles and runs with the output
shown.

## Use after a move

```kelp
fun main() {
    val a = String.from_str("x")
    val b = a
    print(a)
    print(b)
}
```

```text
error: use of moved value 'a'
  --> fail_move.kp:4:11
```

`val b = a` moved the string into `b`, so `a` is empty. Read the name that still
owns the value, or copy it first with `clone()`.

```kelp
fun main() {
    val a = String.from_str("x")
    val b = a
    print(b)
}
```

```text
x
```

## A borrow kept across a mutation

`first` borrows an element of `names`. The `push` runs while `first` is still read
on the next line, so the list cannot be changed.

```kelp
impl "std/str"

fun main() {
    var names: List<String> = List.empty()
    names.push(String.from_str("alpha"))
    val first = names.get(0)
    names.push(String.from_str("beta"))
    print(first.as_str())
    print(names.len())
}
```

```text
error: cannot borrow 'names' as exclusive: already borrowed as shared
  --> fail_mut_borrow.kp:7:5
```

Move the mutation after the last read of the borrow. The borrow is dead once
`first` is read for the last time, so the `push` is accepted there.

```kelp
impl "std/str"

fun main() {
    var names: List<String> = List.empty()
    names.push(String.from_str("alpha"))
    val first = names.get(0)
    print(first.as_str())
    names.push(String.from_str("beta"))
    print(names.len())
}
```

```text
alpha
2
```

## A borrow stored in a field

A `datac` may hold a `View` only when the text the view points into is moved into an
earlier field of the same value. Here the view points at a local, which the value
does not own.

```kelp
datac Doc(val body: View)

fun main() {
    val text = String.from_str("hello")
    val d = Doc(body = text.view())
    print(d.body.len())
}
```

```text
error: field 'body' borrows 'text', but that value is not moved into an earlier String/Bytes field of this datac
  --> fail_field_view.kp:5:13
```

Store an owned `String` instead. Copying the view into a `String` makes the field own
its text.

```kelp
datac Doc(val body: String)

fun main() {
    val text = String.from_str("hello")
    val d = Doc(body = text.view().to_string())
    print(d.body.len())
}
```

```text
5
```

## A temporary borrowed into a call

`&mk()` borrows the result of a call, and a call's result is not a place that can
be borrowed: it has no name for the borrow to point at.

```kelp
datac Name(val text: String)

fun mk().return: Name = Name(text = String.from_str("kelp"))

fun show(n: &Name) {
    print(n.text.len())
}

fun main() {
    show(&mk())
}
```

```text
error: cannot borrow a temporary value
  --> fail_temp_call.kp:10:10
```

Bind the value to a name first, then borrow the name.

```kelp
datac Name(val text: String)

fun mk().return: Name = Name(text = String.from_str("kelp"))

fun show(n: &Name) {
    print(n.text.len())
}

fun main() {
    val n = mk()
    show(&n)
}
```

```text
4
```

## Refusals of the collector

A hosted build refuses some shapes by name. These are not ownership errors. They come
from the collector, which has to see every value it may reclaim. The messages on current
`main` still say "in managed mode", which is the wording the compiler prints today.

- **A resource in a container or a heap slot.** `'Leaf' cannot be a List element in managed
  mode: 'Leaf' is a resource`. The same refusal applies to a `Map` key or value, an array
  element, the payload of a `Box`, a field of a `datac` that lives in the heap, and a
  value captured by a closure. A resource stays in a local, a parameter or a stack field.
- **Channels and pool values.** `'Job' cannot be a thread's argument`, and
  `'std.sync.ChanMeta' cannot be the value of a Mutex or RwLock`. Channels and
  [`std/pool`](/stdlib/pool) are refused on current `main` for this reason, until the step
  that lets the collector see values a thread or a lock holds.
- **A `Mutex` or `RwLock` holding a memory value.** `'List<i32>' cannot be the value of a
  Mutex or RwLock`. A `Mutex` holding a number is accepted.
- **A `Box<dyn Trait>` in a container.** `'Box<dyn Shape>' cannot be a List element`. A
  concrete type with a destructor cannot be the payload of a `Box` either. See
  [Box dyn](/language/box-dyn).
- **An `enum` as a `Map` key or value.** `managed mode describes the enum 'Kind' only as a
  heap object (a Box payload or a List element)`. An enum is accepted as a `List` element.
- **A thread closure that captures values.** `'thread.spawn' cannot take a closure that
  captures values in managed mode`.
- **A by-value aggregate in a user `extern fun`.** The message says the llvm backend cannot
  pass the struct, `String` or `List` to a native symbol yet, and asks for a pointer or a
  handle. See [User FFI](/language/externs).

## Where to go next

- [The rules of ownership](/memory/rules): why each of these is refused
- [Pitfalls](/language/pitfalls): the full table of messages across the language,
  including the ones for tuples, arrays and text
