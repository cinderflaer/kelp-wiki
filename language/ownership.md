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

## No partial moves

An owned field cannot be read out of a borrowed structure:

```kelp
datac Line(val text: String, val n: usize)

fun use_line(l: Line) {
    print(l.text)             // error: cannot read the owned field 'text' by value
    print(l.text.as_str())    // fine: a view of the field
    print(l.n)                // fine: `usize` is Copy
}
```

To *take* an owned field, hold it in a `Box` and `take()` it, or make the
parameter `move Line` and read the field out of the value you now own.

This is also why several stdlib combinators are `Copy`-only: `option.unwrap` on an
`Option<String>`, `result.map` over a `Result<T, MyErr>` and `list.filter` over a
`List<String>` each need a move out that v1 does not have.

## Drops

Owned values are freed at the end of the scope that owns them, on every exit path
including `return` and either branch of an `if`. A `datac` drops its fields, a
`List` drops its elements and then its buffer, and a `Box` drops what it holds.
An owned `pd` is freed once at process exit. There is no `free`, no `deinit`, and
no way to leak deliberately.

## The two rules that explain most borrow errors

1. **An owned value is moved once.** If the compiler says "use of moved value",
   either borrow instead of moving, make a second owned copy
   (`String.from_str(a.as_str())`), or reorder so the last use really is last.
2. **A borrow outlives its use.** If the compiler says a temporary would be freed
   before the borrow could be used, bind the value to a `val` first.

[Pitfalls](/language/pitfalls) lists the exact error messages and their fixes.

## See also

- [Types](/language/types)
- [Collections](/language/collections)
- [Errors and panics](/language/errors)
- [Pitfalls](/language/pitfalls)
