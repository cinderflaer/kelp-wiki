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

fun mk() => Name = Name(text = String.from_str("kelp"))

fun show(n: Name) {
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

fun mk() => Name = Name(text = String.from_str("kelp"))

fun show(n: Name) {
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

A hosted build refuses some shapes by name. These are not ownership errors. They come from
the collector, which has to see every value it may reclaim. The messages say "in a hosted
build" and name the reason, for example:

```text
'Leaf' cannot be a List element in a hosted build: 'Leaf' is a resource, and a resource never enters the collected heap
```

- **A resource in a container or a heap slot.** The same refusal applies to a `Map` key or
  value, an array element, the payload of a `Box`, a field of a heap-resident `datac`, and a
  value captured by a closure environment. A resource stays in a local, a parameter or a
  field of a stack value. The classifier is in `kelpc/src/managed.rs`.
- **Channel ends and pool values.** A channel end (`SendEnd`, `RecvEnd`, `Sender`,
  `Receiver`) is a resource, so it is refused where a resource is refused, such as a `List`
  element, and in a `Mutex` or `RwLock` value (the form is given below). It is not refused as
  a thread argument or result: the channel records cross to a worker, by commit `c2503916`
  (`CROSSING_CHANNEL_RECORDS` in `kelpc/src/managed.rs`). A `fun` literal passed to
  [`thread.spawn`](/stdlib/thread) may also capture a `Sender`. A channel used inside one
  thread builds. A [`std/pool`](/stdlib/pool) value is a resource with a destructor, and it
  does not cross to a worker.
- **A `Mutex` or `RwLock` holding a resource.** The form is `'std.sync.Sender<i64>' cannot
  be the value of a Mutex or RwLock in a hosted build: 'std.sync.Sender<i64>' is a
  resource, ...`. A `Mutex` or `RwLock` holding a `List`, a `String` or a number is accepted:
  a local `Mutex<List<i32>>` locks, pushes and returns the length. A `Mutex` inside a `List`
  or a `Box` is refused, for example `'Mutex<i64>' cannot be a 'List' element: a mutex owns a
  runtime record and is reached by borrowing it`. Keep the mutex in a local or a field
  (`val m = Mutex.new(0)`) and lock it there.
- **A `Box<dyn Trait>` in a container or as a thread argument.** The form is `'Box<dyn
  Shape>' cannot be a List element in a hosted build: its declaration was not found, so it
  cannot be classified as memory`. A concrete type with a destructor is a resource, so it
  cannot be the payload of a `Box` either. See [Box dyn](/language/box-dyn).
- **An enum as a `Map` value.** The checker refuses an enum as a `Map` value: `'Status'
  cannot be a 'Map' value: a hosted build cannot describe an 'enum' inside a map's entry yet,
  and a 'datac' that holds the enum is refused the same way`. Keep the values in a
  `List<Status>` and store each value's index in the map. An enum is accepted as a `List`
  element and as a `Box` payload: the collector describes it as a heap object
  (`kelpc/src/gc_descr.rs`).
- **A closure that captures a resource.** One that captures a resource is refused as
  `'std.sync.Sender<i64>' cannot be a value captured by a closure environment in a hosted
  build: 'std.sync.Sender<i64>' is a resource, ...`. The exception is a `fun` literal written
  directly as the `thread.spawn` entry, which may capture a channel end
  (`closure_sender_send.kp` and `closure_sender_panic.kp` run). A closure that captures a
  memory value builds (`closure_mutex_list.kp` runs). A scoped closure that borrows its
  captures is not checked, because its environment stays on the stack.
- **A by-value aggregate in a user `extern fun`.** The message says the llvm backend cannot
  pass the struct, `String` or `List` to a native symbol, and asks for a pointer or a handle.
  See [User FFI](/language/externs).

For the messages that a manual block prints, see [the boundary](/memory/tidepool/boundary).

## Where to go next

- [The rules of ownership](/memory/rules): why each of these is refused
- [Pitfalls](/language/pitfalls): the full table of messages across the language,
  including the ones for tuples, arrays and text
