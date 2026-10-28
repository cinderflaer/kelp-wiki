---
title: "`std/arena`"
description: "A bump arena over a caller-owned byte region. Pure pointer arithmetic, so it works hosted and freestanding with no `[target] alloc` pair. Refuses a request that does not fit, an overflowing size and a non-power-of-two align; `reset` reclaims the region."
isPublished: true
tags: "stdlib, memory"
---
A bump arena over a byte region the **caller** owns. Ungated.

```kelp
impl "std/arena"
```

Nothing here allocates, frees or touches libc: the caller hands in one region (a
`static mut [u8; N]`, a local array, a frame, a device buffer) and takes
allocations out of it until it is full. The module is therefore legal in a
hosted program and in a freestanding image alike, and it needs no
`[target] alloc`/`dealloc` pair. It is one of the pure modules the freestanding
allowed set admits beside `std/atomic`, `std/option` and `std/result`.

## Types

```kelp
datac Arena(var base: Ptr<u8>, val cap: usize, var used: usize)
```

`base` is the region's first byte, `cap` its length in bytes and `used` the bump
position. `base` and `used` are `var` because an allocation moves `used`;
`cap` is fixed.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `new(base: Ptr<u8>, cap: usize)` | `Arena` | a fresh arena over `cap` bytes at `base`, nothing used |
| `Arena.used()` | `usize` | bytes handed out so far, alignment padding included |
| `Arena.remaining()` | `usize` | `cap - used`: bytes left before alignment, not a promise that a request of that size fits |
| `Arena.alloc(size: usize, align: usize)` | `Ptr<u8>` | a `size`-byte block whose address is `align`-aligned, or the null pointer |
| `Arena.allocZeroed(size: usize, align: usize)` | `Ptr<u8>` | `alloc`, then the block written to zero |
| `Arena.reset()` | `Unit` | sets `used` back to zero |

`new` is a module-level function, reached through the `impl` alias:
`arena.new(base = b, cap = c)`. Kelp has no `Arena.new(...)` associated call (a
dotted receiver is always a value, and `fun T.name` is a method with an implicit
`self`), so a constructor is spelled the way every shipped function is. The
datac's own literal constructor, `arena.Arena(base = b, cap = c, used = 0)`,
still works.

## How `alloc` behaves

- **Alignment is a power of two.** A zero or non-power value is a programming
  error and `alloc` panics with the module's own message:

  ```text
  panic: arena align must be a power of two
  ```

- **The returned address is aligned, not the offset.** The padding is measured
  from `base.addr()`, so a `base` that is not itself `align`-aligned still hands
  back an aligned pointer. The arithmetic is written with `%` and `/` and refuses
  at every step that could wrap: a `size` whose aligned end would overflow
  `usize` answers the null pointer rather than a short block.
- **A request that does not fit is the null pointer.** Nothing is written and
  `used` does not move. There is no growth: an arena reclaims in bulk (`reset`)
  or not at all, and a single allocation cannot be freed.
- **`reset` frees nothing and clears nothing.** It only sets `used = 0`, so the
  whole region is available again and the previous user's bytes are still there
  for whoever reads them next. Pointers handed out before the reset are
  use-after-reset, which the compiler cannot see. A caller that wants a clean
  block uses `alloc_zeroed`.

`alloc_zeroed` writes zeros through the returned raw pointer, so it is the
module's one `unsafe` operation. `std/arena` is the first module shipped with
the compiler to contain `unsafe`, admitted by the compiler's own
`stdlib::UNSAFE_MODULES` list; a project importing it does **not** list it under
`coral.toml`'s `[unsafe] modules`, and a project module cannot add itself to
that list.

## Example

Two blocks out of a local 256-byte region, each written and read back, then a
`reset` and an `alloc_zeroed` at the first block's address. The two zeros prove
the fresh block was cleared over the `170` the first user wrote.

```kelp project
impl "std/arena"

fun main() {
    var buf: [u8; 256] = [0; 256]
    val bp: Ptr<[u8; 256]> = Ptr.from_ref(&buf)
    val base: Ptr<u8> = bp.cast<u8>()
    var a: arena.Arena = arena.new(base = base, cap = 256)

    val p: Ptr<u8> = a.alloc(size = 4, align = 4)
    val q: Ptr<u8> = a.alloc(size = 4, align = 4)
    unsafe {
        p.write(170)
        q.write(187)
        print(p.read())
        print(q.read())
    }
    print(q.addr() % 4 == 0)
    print(p.addr() != q.addr())

    a.reset()
    val z: Ptr<u8> = a.allocZeroed(size = 4, align = 4)
    unsafe {
        print(z.read())
        print(z.offset(1).read())
    }
    print(z.addr() == p.addr())
}
```

```text
170
187
true
true
0
0
true
```

The region may be borrowed with `Ptr.from_ref` (no `unsafe` needed for the
borrow itself); only writing through the returned pointers needs an `unsafe`
block.

## Freestanding

`std/arena` is pure pointer arithmetic, so a bare-metal image may import it with
no `[target] alloc` pair at all. The acceptance fixture
(`kelpc/tests/projects/freestanding_arena`) is a riscv64 kernel that carves a
`static mut [u8; 4096]` region into aligned allocations, prints the addresses,
the null pointer that exhaustion and an overflowing size answer, and the zeros
`alloc_zeroed` wrote, then halts.

## See also

- [`std/mem`](/stdlib/mem): the owned `Bytes` buffer
- [Unsafe code and raw pointers](/language/unsafe): `Ptr.try_alloc`, the
  allocator hook and what the compiler does not check
- [Freestanding mode](/language/freestanding): the allowed set and the
  `[target]` allocator pair
