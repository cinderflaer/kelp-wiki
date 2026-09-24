---
title: "Ownership and borrowing"
description: "Source section - syntax.md \u00a710."
isPublished: true
tags: "language, ownership"
---
Source section:
[`syntax.md` §10](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Owned values (`String`, `Bytes`, `List`, `Map`, `Box`, `datac`, `enum`) have
exactly one owner. There is no garbage collector: the owner's scope end is the
free, on every exit path.

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
fun consume(s: move String).R: usize = s.len()

val a = String.from_str("bob")
print(consume(a))
print(a)                  // error: use of moved value 'a'
```

A temporary is already an owner, so `consume(String.from_str("bob"))` needs no
binding. A **borrow cannot be moved out of**: `fun forward(s: String).R: usize =
consume(s)` is an error, because `s` belongs to the caller.

A tuple is an owned value like any other, so a parameter of the type borrows the
argument and `move (A, B)` is the parameter form that takes it over:
`fun take(p: move (String, i32))`.

Assignment to an existing `var` moves the new value in and frees the old value,
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

- A borrow lives **until the end of its scope**, not until its last use: with
  one statement-sized exception: a borrow taken *inside an initializer* ends with
  that statement, because the bound value does not borrow it. So
  `val back = str.parse_i64(cand.as_str())` borrows `cand` for one call and keeps
  nothing of it; `return cand` a few lines later is fine. A binding that *is* the
  borrow (`val v = l.get(0)`) still pins its owner for as long as `v` lives.
- While a value is borrowed exclusively, nothing else may borrow it and the owner
  may not be assigned or moved.
- While a value is borrowed shared, it cannot be borrowed exclusively, and it
  cannot be assigned or moved, but a `Copy` value can always be *read*, because
  reading one is a copy rather than a move.
- Dereferencing a `&mut` gives write access; dereferencing a `&` does not.
- A function whose `.R: T` is a borrow must return something derived from its
  **first reference parameter**, and a payload bound by a pattern counts as
  derived from the scrutinee it came out of:

  ```kelp
  fun as_str(v: &Json).R: &str {
      if let Str(s) = v {
          return s.as_str()
      }
      panic("json.as_str: value is not a string")
  }
  ```

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

The binding is still freed as a whole at the end of its scope, and the moved
field's slot is cleared at the read, so nothing is freed twice. On a `val` local
the field is gone for good; on a `var` local a fresh value assigned into the
field owns it again. A move on one branch of an `if` takes the field only on
that path, and after the merge only the fields that stayed are read by name.

The field has to be a **direct field of a local this frame owns**: a `val` local,
a `var` local, or a `move T` parameter. A borrow, a temporary and a field chain
are all refused, because the frame has nothing of its own to give away there:

```kelp
fun steal(b: &Bag).R: List<i32> = b.xs
// error: cannot move the field 'xs' out of 'b': the value is borrowed
```

To take a field out of a chain, move each hop into a local first: `val inner =
outer.inner` then `val xs = inner.xs`.

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
drop frees the positions that stayed, and the source place cannot be bound again:

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

fun take_word(h: move Held).R: String = when h {
    Word(text) -> text        // the payload moves out of the owned `h`
    Blank -> String.from_str(s = "")
}

fun peek_word(h: &Held).R: usize = when h {
    Word(text) -> text.len()  // `text` is a `&String` here; nothing moved
    Blank -> 0
}
```

The helpers whose receiver stays a borrow are `Copy`-only on the side they
rebuild: `option.or_else`, `result.unwrap`/`unwrap_or`/`unwrap_err`/`expect`/
`expect_err`/`and_then`/`or_else` and `list.filter` over a `List<String>`. `option.unwrap` on an
`Option<String>` and `result.map` over a `Result<T, MyErr>` take their receiver
with `move` and work.

## Drops

Owned values are freed at the end of the scope that owns them, on every exit path
including `return` and either branch of an `if`. A `datac` drops its fields, a
`List` drops its elements and then its buffer, and a `Box` drops what it holds.
An owned `pd` is freed once at process exit. There is no `free`, no `deinit`, and
no way to leak deliberately.

## The two rules that explain most borrow errors

1. **An owned value is moved once.** If the compiler says "use of moved value",
   either borrow instead of moving, make a second owned copy (`xs.clone()`,
   `s.clone()`), or reorder so the last use really is last.
2. **A borrow outlives its use.** If the compiler says a temporary would be freed
   before the borrow could be used, bind the value to a `val` first. A call's
   result and a **field of a call's result** are the same case: `mkName().name`
   has no storage of its own, so it can be borrowed for the length of one call
   (`print(mkName().name.len())`, `take(mkName().name)`) and the compiler stages
   the temporary until that call returns. Binding the borrow is refused instead
   (`val r = &mkName().name` is `cannot borrow a temporary value`), and so is
   handing it back (`mkName().name.as_str()` names the returned borrow). A chain
   that steps through a borrow (`headers.get(i).name`) is not a temporary case at
   all: the storage belongs to whatever `get` pointed at.

[Pitfalls](/language/pitfalls) lists the exact error messages and their fixes.

## See also

- [Types](/language/types)
- [Return types and `return`](/language/returns)
- [Bindings and assignment](/language/bindings)
- [Collections](/language/collections)
- [Errors and panics](/language/errors)
- [Pitfalls](/language/pitfalls)
