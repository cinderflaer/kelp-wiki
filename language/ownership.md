---
title: "Ownership and borrowing"
description: "Ownership in Kelp: moves, borrows that end at their last use, cursors, partial moves, and when values are dropped."
isPublished: true
tags: "language, ownership"
---
Source: [`syntax.md` §10](/design/syntax).

Owned values (`String`, `Bytes`, `List`, `Map`, `Box`, `datac`, `enum`) have
exactly one owner. The owner's scope end is where a resource closes, on every exit
path. In a hosted build a memory value is not freed at that point: the collector
reclaims it later. See [Drops](#drops) and [Working with Kelp memory](/memory).

## Moves

Rebinding, reassigning or returning an owned value moves it:

```kelp
val a = String.from_str("x")
val b = a
print(b)        // ok
print(a)        // error: use of moved value 'a'
```

**Passing an owned value to a parameter is not a move**: parameters borrow:

```kelp
fun greet(s: String) { print(s) }

val name = String.from_str("bob")
greet(name)
print(name)               // still owned here
```

`move T` is the parameter form that *does* take the value:

```kelp
fun consume(s: move String) => usize = s.len()

val a = String.from_str("bob")
print(consume(a))
print(a)                  // error: use of moved value 'a'
```

A temporary is already an owner, so `consume(String.from_str("bob"))` needs no
binding. A **borrow cannot be moved out of**: `fun forward(s: String) => usize =
consume(s)` is an error, because `s` belongs to the caller.

A tuple is an owned value like any other. A parameter of the tuple's type borrows
the argument. To take the tuple over, write `move (A, B)`, as in
`fun take(p: move (String, i32))`.

Assignment to an existing `var` moves the new value in and drops the old value,
which is how a recursive structure is rebuilt in a loop:

```kelp
var list = Node(value = 1, next = Box.empty())
list = Node(value = 2, next = Box.of(list))
```

## Borrowing

```kelp
val r = &c            // shared borrow
var w = &mut c        // exclusive borrow
print((*r).count)     // dereference, then read a field
(*w).count = 9        // dereference, then write a field
```

Rules the checker enforces:

- A borrow ends at its **last use**, not at the end of its scope. A `val` that
  holds a borrow pins its owner until the binding is last read; after that the
  owner may be mutated, moved or reassigned. A borrow taken *inside an
  initializer* still ends with that statement, because the bound value does not
  borrow it: so `val back = str.parse_i64(cand.as_str())` borrows `cand` for one
  call and keeps nothing of it, and `return cand` a few lines later is fine. A
  binding that *is* the borrow (`val v = l.get(0)`) pins its owner until `v`'s
  last use, and a use inside a loop body counts for every iteration, so the
  borrow is live for the whole loop.
- While a value is borrowed exclusively, nothing else may borrow it and the owner
  may not be assigned or moved.
- While a value is borrowed shared, it cannot be borrowed exclusively, and it
  cannot be assigned or moved, but a `Copy` value can always be *read*, because
  reading one is a copy rather than a move.
- **Two fields of one owner are different places** (26.10.3). A borrow of
  `s.items` and a borrow of `s.count` do not overlap, so one call may take both
  exclusively (`bump(s.count, s.items)`), a live `&mut s.count` leaves
  `s.items` usable, and a scoped block that writes `s.count` can run in a call
  that borrows `s.items`. A borrow of the whole `s` overlaps every field, two
  borrows of the same field overlap, and a field of a field is a part of the
  field (`s.a.b` is a part of `s.a`). Only a field read straight off a local
  struct (or off a `mut`/`&` parameter) is a path: a field reached through an
  `enum` payload, a `Box`, a trait object or an index is still the whole owner.
- Dereferencing a `&mut` gives write access; dereferencing a `&` does not.
- A function whose `=> T` is a borrow must return something derived from its
  **first reference parameter**, and a payload bound by a pattern counts as
  derived from the scrutinee it came out of:

  ```kelp
  fun as_str(v: &Json) => &str {
      if let Str(s) = v {
          return s.as_str()
      }
      panic("json.as_str: value is not a string")
  }
  ```

## Borrows end at their last use

A bound borrow is live until its last use, so the owner can be mutated once the
borrow is dead. `first` below is read once, and the `push` after that read no
longer conflicts, even though `first` is still in scope:

```kelp
impl "std/str"

fun main() {
    var names: List<String> = List.empty()
    names.push(String.from_str("alpha"))
    val first = names.get(0)
    print(first.as_str())
    names.push(String.from_str("beta"))   // accepted: `first` is dead here
    print(names.len())
}
```

That program prints `alpha` then `2`. The order is what
matters: move the `push` before the `print` and the borrow is still used after
the mutation, so it is refused:

```kelp refused
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
$ kelpc check swap.kp
error: cannot borrow 'names' as exclusive: already borrowed as shared
  --> swap.kp:7:5
```

Two structured cases follow from statement granularity. A use inside a loop body
keeps the borrow live for the whole loop, including the statements before the use
in the body, because the next iteration reaches them. A use in one arm of an
`if` keeps the borrow live through the whole `if`, because the branch point is
before the statement; a mutation in the other arm is therefore still refused.

Before this rule a bound borrow lived to the end of its block, and the workaround
was to wrap the read in an extra `{ }` so its scope ended early. That workaround
is obsolete and should not be written: the borrow ends at the last use on its
own.

## Cursors and provenance

A binding whose type is a reference, a `View`, a `str` or a `&dyn` carries a
**root set**: the owners its current value may borrow from. A `val`/`var` sets it
from the initializer, `cur = expr` replaces it and releases the root the cursor
left, and an `if`/`when` or a loop that assigns different owners unions the arms'
roots. A borrow made through the cursor is a borrow of the **owner**, so the
owner stays pinned while any cursor into it is live, while rebinding the cursor
itself is accepted. That is what makes a pointer local a usable cursor:

```kelp
datac Node(val value: i32, val next: Box<Node>)

fun main() {
    var list = Node(value = 1, next = Box.of(Node(value = 2, next = Box.of(Node(value = 3, next = Box.empty())))))
    var cur = &list
    var sum = 0
    sum += cur.value
    while !cur.next.is_empty() {
        cur = cur.next.get()   // accepted: `cur` is rebound, `list` stays the root
        sum += cur.value
    }
    print(sum)
}
```

That prints `6`. The same shape works over a `List` by index:
`var cur = xs.get(0)`, then `cur = xs.get(i)` in a loop, keeps `xs` pinned for as
long as `cur` is used. Re-pointing a cursor from one owner to another releases
the first at the assignment, so the first owner is mutable again.

What stays refused, each with the message it produces:

- mutating an owner while a cursor into it is still used:
  `cannot assign to 'list' while it is borrowed`;
- two exclusive cursors into one root, or copying a `&mut` into a second binding
  (`val q = p` where `p: &mut T`, refused because Kelp references are `Copy`):
  `cannot borrow 'a': already borrowed exclusively`;
- moving an owner while a cursor into it is live:
  `cannot move 'list' while it is borrowed`;
- returning a cursor derived from a frame local:
  `cannot return a borrow of 'local': '&Node' borrows from its first reference parameter 'start', so the returned value must be derived from 'start'`.

The older message `cannot assign to 'cur' while it is borrowed` no longer appears
for `cur = cur.next.get()`: the assignment is accepted now. It survives only as
the owner-mutation refusal above, with the owner's name instead of the cursor's.

## Partial moves

Reading an owned field of an owned local binding by value takes that field out
and leaves the rest of the binding owned:

```kelp
datac Bag(val xs: List<i32>, val name: String)

fun use(bag: move Bag) {
    val xs = bag.xs          // `xs` moves out of `bag`
    print(bag.name)          // `name` stayed, and is readable
    print(xs.len())
}
```

The binding is still dropped as a whole at the end of its scope, and the moved
field's slot is cleared at the read, so nothing is dropped twice. On a `val` local
the field is gone for good; on a `var` local a fresh value assigned into the
field owns it again. A move on one branch of an `if` takes the field only on
that path, and after the merge only the fields that stayed are read by name.

The field path has to start at a local this frame owns: a `val` local, a `var`
local, or a `move T` parameter. A borrow and a temporary are refused, because
the frame has nothing of its own to give away there. An owned field chain is
also a path into that local, so it may move its final owned field while its
siblings remain usable:

```kelp
fun steal(b: &Bag) => List<i32> = b.xs
// error: cannot move the field 'xs' out of 'b': the value is borrowed
```

After `val text = person.name.text`, `person.name.id` and `person.city` remain
readable, but `person.name` and `person` cannot be used as whole values. A
fresh assignment to the moved nested field on a `var` local restores that path.

Once a field is gone, reading it again and handing the binding on as a whole are
both refused, because the empty slot would go with it:

```kelp
val xs = bag.xs
val again = bag.xs         // error: use of moved value 'bag.xs'
val whole = bag            // error: cannot use 'bag' as a whole value: its field 'xs' was moved out
```

Borrowing a field that stayed is still fine (`bag.name.as_str()`), and a `Copy`
field is always readable. To *take* an owned field that only a borrow reaches,
hold it in a `Box` and `take()` it.

**A tuple's positions obey the same rule.** A destructuring binding moves its
initializer into the binding, exactly as `val p = place` takes a place, and then
reads each position out of that value, which is the partial move. The value's own
drop drops the positions that stayed, and the source place cannot be bound again:

```kelp
fun use(p: move (String, String)) {
    val (first, _) = p          // `p` moves into the binding; the other position stays
    print(first.as_str())
}

fun peek(p: &(String, i32)) {
    val (text, n) = p           // error: cannot read an owned position out of a borrow
}
```

Reading the same position twice, taking the source apart a second time, and
reading an owned position out of a *borrow* are each refused, and a `Copy`
position is always readable. A tuple is owned as a whole, so every rule above
applies to it: a parameter of the type borrows it, `move (A, B)` takes it, and it
is dropped position by position at the end of its scope
([Types](/language/types)).

An owned `enum` payload obeys the same rule: a `when`/`if let` over an owned place
binds the payload **by value** and takes it out of the enum, so the enum cannot be
used as a whole afterwards and the same payload cannot be bound twice on one path.
Over a borrow the payload binds as a borrow and nothing moves:

```kelp
enum Held {
    Word(val text: String)
    Blank
}

fun take_word(h: move Held) => String = when h {
    Word(text) -> text        // the payload moves out of the owned `h`
    Blank -> String.from_str(s = "")
}

fun peek_word(h: &Held) => usize = when h {
    Word(text) -> text.len()  // `text` is a `&String` here; nothing moved
    Blank -> 0
}
```

Some helpers take their receiver as a borrow, and they only work on `Copy`
payloads. Examples are `option.or_else` and `result.and_then`. Others take the
receiver with `move`, so they also work on owned payloads. Examples are
`option.unwrap` on an `Option<String>` and `result.map` on a `Result<T, MyErr>`.

## Drops

Owned values are dropped at the end of the scope that owns them, on every exit path
including `return` and either branch of an `if`. What a drop does depends on the
value:

- A value that holds a resource runs its destructor, or closes, at that point. These
  need a drop: a `datac` or `enum` with a destructor or a resource field, a `Thread`,
  a `Mutex`, an `RwLock`, a `Condvar`, a closure, and a `dyn` box.
- A memory value owes no drop in a hosted build. A `String`, a `Bytes`, a `List` of
  plain values or a `Box` of plain data is reclaimed by the collector once no path
  reaches it.

A `datac` drops its fields, a `List` drops its elements, and a `Box` drops what it
holds. An owned `pd` is freed once at process exit. There is no `free`, no `deinit`, and
no way to leak deliberately. A type can hook these drop points with its own
destructor, `fun mut T.drop()`; see [User `Drop`](/language/drop).

## The two rules that explain most borrow errors

1. **An owned value is moved once.** If the compiler says "use of moved value",
   either borrow instead of moving, make a second owned copy (`xs.clone()`,
   `s.clone()`), or reorder so the last use really is last.
2. **A borrow needs an owner.** A call's result and a **field of a call's
   result** have no source-level storage of their own. Kelp promotes the owner
   for a direct `as_str()` or `view()` binding, so `val r =
   mkName().name.as_str()` is valid until `r` leaves scope. An explicit borrow
   still needs a place: `val r = &mkName().name` is `cannot borrow a temporary
   value`. A chain that steps through a borrow (`headers.get(i).name`) is not a
   temporary case at all: the storage belongs to whatever `get` pointed at.

[Pitfalls](/language/pitfalls) lists the exact error messages and their fixes.

## See also

- [Types](/language/types)
- [Return types and `return`](/language/returns)
- [Bindings and assignment](/language/bindings)
- [Collections](/language/collections)
- [Errors and panics](/language/errors)
- [Pitfalls](/language/pitfalls)
