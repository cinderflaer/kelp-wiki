---
title: "Per-CPU storage"
description: "`percpu static mut NAME: T = INIT` lays out one copy per CPU in a 64-byte-aligned `.percpu` array, `[target] cpus = N` sets the count, and `cpu_index()` / `cpu_count()` read it back. Freestanding only."
isPublished: true
tags: "language, freestanding, kernel"
---
A kernel keeps per-CPU state: a current-task pointer, a run queue, a scratch
area that must not be shared. **Per-CPU storage** is the storage class for one
copy of a value per CPU, plus the two intrinsics that say which copy the running
CPU is looking at. The design is
[`plan/percpu.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/percpu.md);
the bare-metal build around it is [Freestanding mode](/language/freestanding).

## The scalar names

```kelp
percpu static mut SLOT: usize = 7
```

`percpu` is a contextual word, not a keyword: it is a marker only when `static`
immediately follows it, exactly as `unsafe` and `naked` mark a `fun`. The rest of
the declaration is an ordinary `static mut`:

- `mut` is **required**. A read-only per-CPU value is just a `static` with extra
  address space, so `percpu static SLOT` is refused rather than silently
  read-only.

```text
error: a per-CPU static must be 'mut', written 'percpu static mut SLOT: T = INIT': a read-only per-CPU is just a 'static'
```

- `T` and `INIT` follow the `static` rules: a `Copy` scalar, an integer/`bool`/
  `char` array, a `datac` of those, or `Atomic<T>`, with an initializer that
  folds to a constant. A call in the initializer is the ordinary "the
  initializer is not constant" error.
- `pub` and `section("...")` apply in either order round `pub`, as on a
  `static`. The default section is `.percpu`.

Naming it is `unsafe`, because it **is** a `static mut` in every way: a read, a
write, a field access and taking its address are legal only inside
`unsafe { ... }` or an `unsafe fun`, and the module must be listed in
`coral.toml`'s `[unsafe] modules`. The gate is the same one
[Statics and `defer`](/language/statics-and-defer) describes.

```text
error: 'static mut SLOT' is an unsafe operation: reading, writing or taking its address can only be done inside 'unsafe { ... }' or in a function declared 'unsafe fun'
```

## The count, and the two intrinsics

```toml
[target]
cpus = 2
```

`[target] cpus` is an integer `1..=64`, default 1. It is the number of copies a
`percpu` static is laid out as and the value `cpu_count()` folds to. A value
outside the range is refused by the manifest reader.

```text
error: coral.toml value for '[target] cpus' must be between 1 and 64, found 0
```

`cpu_count() -> usize` is the manifest's `cpus` folded to a `usize` literal at
check time, so it is the same constant to both backends and costs nothing at run
time.

`cpu_index() -> usize` is the running CPU's index, read from the register the
**kernel** sets at boot: `tp` on riscv64 (one `mv`), `TPIDR_EL1` on aarch64 (one
`mrs`). The compiler never sets the register and never assumes it, and the call
takes no arguments and needs no `unsafe`. The example's `kmain` sets it by hand:

```kelp
unsafe { asm("li tp, 0") }
```

Both intrinsics are freestanding-only. `cpus` itself is read in either mode,
because a value that is simply unused is not a mistake.

## The lowering

A `percpu` static is `N` copies laid out as one global array `[N x T]` in section
`.percpu`, aligned to 64 bytes so no two copies share a cache line. A copy whose
type is smaller than a cache line is padded: the element type is
`{ T, [pad x i8] }` with `pad = (64 - size_of(T) % 64) % 64`, so the stride is
`round_up(size_of(T), 64)` and every copy starts on a 64-byte boundary. A type
already a multiple of 64 (including one with a `repr(align)` larger than a line)
is used directly. The folded initializer is replicated into every copy, so the
image carries `N` copies of one constant and no code runs at startup.

Naming the static computes `&NAME[cpu_index()]`: a GEP indexed by the register
read, then (when padded) a project to field 0. A read loads from it, a write
stores through it, and `Ptr.from_mut`/`from_ref` take its address, exactly as for
an ordinary `static`.

At `-O0` (the dev build) `cpu_index()` compares the register against `cpus` and
calls the project's own panic handler with `cpu index out of range` when it is
not below it, the same shape as every other bounds check. A release build trusts
the register: a kernel that leaves `tp` wrong gets misbehaviour it cannot
attribute. The check is deliberately per optimization level rather than
always-on, because the register is the kernel's contract, not a value the
language produced.

## The riscv64 `_start` stub parks the other harts

A `percpu` image with `cpus > 1` runs under QEMU's `-smp 2` with `-bios none`. Without
firmware, QEMU starts **every** hart at the entry. The riscv64 `_start`
stub therefore reads `mhartid` first and parks any hart whose id is not zero on
`wfi` **before** it loads `sp`, so a secondary never touches memory and never
reaches the entry. A single-hart image (the default `-smp 1`) reads 0 and falls
through unchanged.

## What is refused

| Written | Refused because |
| --- | --- |
| `percpu static mut SLOT: T = INIT` in a hosted build | a per-CPU copy needs a bare-metal target whose CPU index register the kernel sets |
| `percpu static SLOT: T = INIT` | the `mut` the storage class requires |
| `percpu static mut SLOT: T = seed()` | the initializer must fold to a constant |
| `SLOT` outside `unsafe { ... }` | a `percpu` static is a `static mut` |
| `[target] cpus = 0` or `65` | the range is `1..=64` |
| `cpu_index()` on a triple with no register read | refused by name |

```text
error: the per-CPU static 'SLOT' is only legal in a freestanding build: one copy per CPU needs a bare-metal target whose CPU index register the kernel sets, so '[target] mode = "freestanding"' and a '[target] cpus' are required
```

What the stage deliberately leaves out is bringing a hart up (the stub parks
secondaries, it does not start them), a per-CPU allocator or run queue, and
per-CPU stack protection. Those are kernel designs on top of the storage class,
not language work.

## Running the example

`examples/kernel0-percpu` boots a two-hart riscv64 `virt` with `-smp 2`. Hart 0
sets `tp = 0`, writes `4` into its copy and prints it; it then sets `tp = 1` by
hand, so the same name reads the untouched second copy; `cpu_index()` and
`cpu_count()` print `1` and `2`.

Run the script from a shell where `kelpc`, `qemu-system-riscv64` and `ld.lld` are on
`PATH`. A Nix shell for the repository provides all three:

```sh
examples/kernel0-percpu/run.sh
```

```text
run.sh: booted .../examples/kernel0-percpu and the UART printed:
cpu0 4
cpu1 7
idx 1
count 2
```

The linked image shows the layout the lowering promises: a 64-byte-aligned
`.percpu` section, `128` bytes for `cpus = 2` and a padded `usize`, and one
symbol.

```text
$ llvm-readelf -S scratch/kp-percpu.elf | grep percpu
  [ 4] .percpu           PROGBITS        0000000080000a40 001a40 000080 00 WAR  0   0 64
$ llvm-nm scratch/kp-percpu.elf | grep kelp_SLOT
0000000080000a40 d kelp_SLOT
```

## See also

- [Statics and `defer`](/language/statics-and-defer): the `static mut` rules and
  the `[unsafe]` gate a per-CPU static shares
- [Freestanding mode](/language/freestanding): the `[target]` section and the
  `_start` stub
- [Kernel 0](/language/kernel): the examples that boot under QEMU, with their
  real serial output
