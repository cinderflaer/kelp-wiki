---
title: "Writing tools in Kelp"
description: "How the Kelp family projects are structured, how to build them, and the compiler errors a first real program runs into (temporaries, borrows that outlive a condition, mut methods) with the fix for each."
isPublished: true
tags: "family, getting-started"
---
This page collects what building [WebKelp](/family/webkelp), a 2,100-line text-processing
program, showed about writing real tools in Kelp: the structure that worked, and the
errors that came up more than once. Nothing here is specific to WebKelp.

## Structure

**One module holds the authority.** Put every `fs`, `process` or `net` call in the entry
module and pass strings to the rest. A parser that takes a `&str` and returns a `String`
needs no `impl` beyond `std/str`, so it is testable without a filesystem, and its imports
show at a glance that it cannot do anything else.

**Return small `datac`s, not tuples.** A function that produces two values returns a named
record. The fields name what each value is, and a caller reads `r.end` instead of
destructuring.

**Model "did not match" in the return value.** A scanner returns the index after what it
consumed, or the index it was given to decline. A lookup returns `-1` as an `i64`. There is
no exception to catch, and `Option` is heavier than a sentinel for byte scanning.

**Test with goldens.** For anything that turns text into text, keep inputs and their
expected outputs in a directory, diff them in a shell script, and add an `--update` mode.
See [Testing what you write](/getting-started/testing) for Coral's own fixture runner.

## A small server

[`std/http`](/stdlib/http#the-server) now has a server, with `Limits`, keep-alive and worker threads. A server
can also be written directly on `std/net`: `net.listen(port)`, `net.accept`, then `net.recv`,
`net.sendAll` and `net.close` on each socket, which is what the
[playground backend](/family/webkelp#playground) does. Points that mattered:

- **Bound everything the client controls.** Cap the header and body size, and use `sock.waitReadable(ms)`
  before each `recv` so a client that stops sending cannot hold the loop.
- **Validate before you construct.** `String.from_bytes` wants valid UTF-8, so an untrusted body is checked
  first and rejected with a `400` rather than risking a panic. A panic ends the process.
- **`net.listen` binds every interface.** Keep it behind a reverse proxy and let the service manager
  restrict it (systemd `IPAddressDeny=any` plus `IPAddressAllow=localhost`).
- **Let the supervisor handle crashes.** There are no exceptions, so run the server with `Restart=always`.

## Build and run

```sh
kelpc run .                  # build and run the project in this directory
kelpc build . -o mytool      # keep the binary
```

`kelpc` links with `ld.lld` and needs no C compiler. On NixOS, where `ld.lld` is not on `PATH` by default, use `nix-shell -p lld openssl --run '…'`.

## Errors you will meet

### A borrow of a temporary

```kelp
out.push_str(str.concat("a", "b").as_str())     // error
```

`.as_str()` on a value that has no name is refused, because the `String` would be dropped
before the borrow was used. Bind it first:

```kelp
val joined = str.concat("a", "b")
out.push_str(joined.as_str())
```

The same applies to a call that returns a borrow of its receiver, such as a method returning
`&str`, and to `x.render().as_str()` chains. When a project keeps doing this, a small helper
that returns the `String` (`text.cat3(a, b, c)` in WebKelp) removes most of it.

### A condition keeps its borrow alive

```kelp
if looks_like_attrs(inner.as_str()) {
    return Braces(attrs = attrs.parse(inner.as_str()), end = e)   // error: cannot move 'inner' while borrowed
}
```

A borrow taken inside an initializer ends with that statement, but one taken in an `if`
condition lasts through the block. Compute the answer first:

```kelp
val ok = looks_like_attrs(inner.as_str())
if ok { … }
```

### Assigning to something you just borrowed

```kelp
body = str.trim(sp.body.as_str())   // error: cannot assign to 'body' while it is borrowed
```

When a variable is rebuilt from a borrow of itself or of a value derived from it, use a
fresh `val` for the result rather than reassigning the `var`.

### Methods that mutate

```kelp
fun Attrs.add_class(name: str) { classes.push_str(name) }
// error: cannot write to 'self': it is a shared borrow, not 'mut'
```

A method that changes its receiver is `fun mut Attrs.add_class(…)`. Inside it, calling
another method of the same type needs `self.`: `self.add_class(value)`. And `pub` is not
allowed on a method: mark the *type* `pub` and its methods follow.

### A borrow of a borrow

A parameter already is a borrow, so `&lines` on a `lines: &List<String>` parameter is
refused with `Kelp has no '&&T'`. Pass `lines`. Locals are the opposite: `&items` is right
for a `val items`.

### `trim_start` is not like `trim`

`str.trim` and `str.trimEnd` return a `String`. `str.trimStart` returns a **`&str`**, so it
has no `.len()` or `.as_str()`: use `str.len(t)` on it, or copy it with `String.from_str`.
Check the return type in [`std/str`](/stdlib/str) before chaining.

### Loops that end through the condition

`break` and `continue` exist ([Iterators, `for` and `break`](/language/iterators)), but an
exit written in the condition keeps a scanner's termination visible:

```kelp
var found = false
while i < n && !found {
    if matches(i) {
        found = true
    } else {
        i += 1
    }
}
```

### Fields must be owned

A `datac` field is a `String`, never a `str`. Constructing one from a literal converts
automatically (`Split(body = "", attrs = "")`), and a borrowed value needs
`String.from_str(x)`.

### `str.byte` costs the length of the string

A `str` is a NUL-terminated pointer with no stored length, so `str.byte(s, i)` and `str.len(s)` have to walk to
the end of `s`. A loop over every byte of a long string is therefore quadratic. For a string you scan
repeatedly, take a `View` once (`val v = s.view()`) and use `v.get(i)` and `v.len()`, which are constant time.
A `View` cannot be stored in a `datac`, but it can be a parameter, which is all a scanner needs.

### `$` in string literals

A `$` starts an interpolation inside a string literal, so text that contains one (a
JavaScript or regex snippet emitted by a generator) needs care. WebKelp's embedded
stylesheet has none, which is why it can be written as plain `push_str` lines.

## See also

- [How WebKelp is built](/family/webkelp-internals)
- [Ownership and borrowing](/language/ownership) and [Pitfalls](/language/pitfalls)
- [Text](/language/text)
- [Kelp family](/family)
