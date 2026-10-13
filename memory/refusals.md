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
`main` say "in a hosted build" and name the reason, for example `'Leaf' cannot be a List
  element in a hosted build: 'Leaf' is a resource, ...`. The text "in managed mode" is
  retired.

- **A resource in a container or a heap slot.** `'Leaf' cannot be a List element in a hosted
  build: 'Leaf' is a resource, and a resource never enters the collected heap ...`. The
  same refusal applies to a `Map` key or value, an array element, the payload of a `Box`,
  and a value captured by a closure environment. A resource stays in a local, a parameter
  or a field of a stack value.
- **Channel ends and pool values.** A channel end (`SendEnd`, `RecvEnd`, `Sender`,
  `Receiver`) is a resource. Built examples: `'std.sync.Sender<i64>' cannot be a List
  element in a hosted build: 'std.sync.Sender<i64>' is a resource, ...`, the same refusal
  as a thread argument, a `Mutex` value and a closure capture. A channel used inside one
  thread builds. [`std/pool`](/stdlib/pool) is refused because its `PoolShared` record is
  a resource: `'std.pool.PoolShared' cannot be a thread's argument in a hosted build:
  'std.pool.PoolShared' is a resource, ...`.
- **A `Mutex` or `RwLock` holding a resource.** The form is `'std.sync.Sender<i64>' cannot
  be the value of a Mutex or RwLock in a hosted build: 'std.sync.Sender<i64>' is a
  resource, ...`. A `Mutex` or `RwLock` holding a `List`, a `String` or a number is
  accepted: a local `Mutex<List<i32>>` locks, pushes and returns the length. A `Mutex`
  inside a `List` or a `Box` is refused, for example `'Mutex<i64>' cannot be a 'List'
  element: a mutex owns a runtime record and is reached by borrowing it, while a
  container's own routines move and drop an element like a plain location. Keep the mutex
  in a local or a field ('val m = Mutex.new(0)') and lock it there`, and the `Box` form
  says `'Box' element`.
- **A `Box<dyn Trait>` in a container or as a thread argument.** The form is `'Box<dyn
  Shape>' cannot be a List element in a hosted build: its declaration was not found, so it
  cannot be classified as memory`. A concrete type with a destructor is a resource, so it
  cannot be the payload of a `Box` either. See [Box dyn](/language/box-dyn).
- **An enum as a `Map` value.** The checker refuses an enum as a `Map` value: `'Status'
  cannot be a 'Map' value: a hosted build cannot describe an 'enum' inside a map's entry
  yet, and a 'datac' that holds the enum is refused the same way. Keep the values in a
  'List<Status>' and store each value's index in the map instead`. As a key, `Map<Kind, i32>`
  was refused in a build of `main` before that check, with `a hosted build describes the
  enum 'Kind' only as a heap object (a Box payload or a List element); an enum stored inside
  a datac is not described yet`. Whether an enum is accepted as a `List` element or a `Box`
  payload was not built in this lane.
- **A closure that captures a resource.** One that captures a resource is refused as
  `'std.sync.Sender<i64>' cannot be a value captured by a closure environment in a hosted
  build: 'std.sync.Sender<i64>' is a resource, ...`. A closure that captures a memory value
  was not built in this lane. A scoped closure that borrows its captures is not checked,
  because its environment stays on the stack.
- **A by-value aggregate in a user `extern fun`.** The message says the llvm backend cannot
  pass the struct, `String` or `List` to a native symbol yet, and asks for a pointer or a
  handle. See [User FFI](/language/externs).

## Where to go next

- [The rules of ownership](/memory/rules): why each of these is refused
- [Pitfalls](/language/pitfalls): the full table of messages across the language,
  including the ones for tuples, arrays and text
