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

## Where to go next

- [The rules of manual memory](/memory/rules): why each of these is refused
- [Pitfalls](/language/pitfalls): the full table of messages across the language,
  including the ones for tuples, arrays and text
