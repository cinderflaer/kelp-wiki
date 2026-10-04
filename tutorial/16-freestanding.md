---
title: "Tutorial 16: Freestanding, a tiny kernel"
description: "Chapter 16 of the Kelp tutorial: a freestanding riscv64 project with no libc, a serial driver behind an mmio grant, a kernel that boots under QEMU and prints, and what a failed bounds check looks like on bare metal."
isPublished: true
tags: "tutorial, freestanding, kernel"
---
The same language runs with **no operating system**. A project opts in with a `[target]`
section in `coral.toml`; the compiler then emits its own `_start`, links no libc and no
runtime, and refuses anything that would need one at compile time. The reference is
[Freestanding mode](/language/freestanding) and [the kernel pages](/language/kernel);
`examples/kernel0` in the compiler repository is the original small kernel this chapter
follows.

QEMU is available in the compiler's `dev-kernel.nix` shell (`qemu-system-riscv64`
10.2.4), so everything below was really booted. Freestanding is **LLVM only by design**, so
for this chapter the "same output on both backends" check does not apply, and it is
shown below that the C oracle refuses the project.

## The project

```text
tinyk/
    coral.toml
    kernel.ld          the linker script
    src/main.kp
    src/uart.kp
```

```toml
name = "tinyk"
version = "0.1.0"

[target]
mode = "freestanding"
triple = "riscv64-unknown-none-elf"
entry = "kmain"
linker_script = "kernel.ld"
panic = "kp_panic"

# only the uart module contains `unsafe`
[unsafe]
modules = ["uart"]

# the one device window the kernel may name: QEMU virt's NS16550 UART
[caps]
mmio = ["0x10000000+0x100"]
```

- `mode = "freestanding"`, a `triple`, an `entry` function and a `linker_script` are the
  required `[target]` keys. `panic` names the function that every compiler-inserted check
  (a bounds check, an overflow) calls, with its static message.
- `[unsafe] modules = ["uart"]` lists the one module allowed to contain `unsafe`
  (chapter 15 used the same list).
- `[caps] mmio = ["0x10000000+0x100"]` is a **capability**, chapter 12's idea applied to
  hardware: a pointer may only be built from an address the module was granted, and this
  is the 256-byte register window of QEMU's `virt` serial port.

The linker script, `kernel.ld`, is the one from `examples/kernel0` unchanged. It places the
image at `0x80000000`, where QEMU's `-bios none` starts it, puts `.text.boot` first, and
reserves a 16 KiB stack that the generated `_start` loads into `sp`.

The driver, `src/uart.kp`:

```kelp
// The serial port of QEMU's riscv64 `virt` machine: an NS16550 at 0x10000000.
// Offset 0 takes the byte to send; bit 5 of the register at offset 5 says the
// transmitter is ready. Only this module contains `unsafe`.
impl "std/str"

const BASE: usize = 0x10000000

pub fun putc(c: u8) {
    unsafe {
        val status: Ptr<u8> = Ptr.from_addr(BASE + 5)
        // there are no bitwise operators here: bit 5 is (value / 32) % 2
        while (status.read_volatile() / 32) % 2 == 0 {}
        val data: Ptr<u8> = Ptr.from_addr(BASE)
        data.write_volatile(c)
    }
}

pub fun puts(s: str) {
    val n = str.len(s)
    var i: usize = 0
    while i < n {
        putc(str.byte(s, i))
        i += 1
    }
}

pub fun halt() {
    while true {
        unsafe {
            asm("wfi")
        }
    }
}
```

`Ptr.from_addr` is the only place an integer becomes a pointer, so it is the whole
surface the `mmio` grant guards; reading and writing through it needs `unsafe`, and
`read_volatile` and `write_volatile` stop the compiler from merging or removing the
accesses. The kernel itself, `src/main.kp`:

```kelp
impl "uart" caps(mmio = ["0x10000000+0x100"])

// print an unsigned number in decimal without allocating
fun put_num(n: u64) {
    if n >= 10 {
        put_num(n / 10)
    }
    uart.putc(48 + (n % 10).to_u8())
}

section(".text.boot") fun kmain() {
    uart.puts("tiny kernel booted\n")
    var sum: u64 = 0
    var i: u64 = 1
    while i <= 5 {
        sum += i * i
        uart.puts("square ")
        put_num(i)
        uart.puts(" -> ")
        put_num(i * i)
        uart.puts("\n")
        i += 1
    }
    uart.puts("sum of squares: ")
    put_num(sum)
    uart.puts("\n")
    uart.halt()
}

fun kp_panic(msg: str) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts("\n")
    uart.halt()
}
```

`impl "uart" caps(mmio = [...])` delegates the same window to `uart`: the entry module
holds it from `coral.toml`, and, exactly as in chapter 12, can pass on only what it holds.
`section(".text.boot")` puts `kmain` at the start of the image. `put_num` is a recursive
decimal printer, because there is no allocator and so no `String`.

## Booting it

The commands, run inside `nix-shell dev-kernel.nix` (which supplies QEMU and `ld.lld`):

```sh
kelpc build tinyk -o kernel.elf
timeout 20 qemu-system-riscv64 -machine virt -bios none -nographic -no-reboot \
    -serial mon:stdio -kernel kernel.elf
```

I wrapped that in a small script that stops QEMU once a marker line appears (the kernel
halts in a `wfi` loop and never exits on its own), and captured the serial port:

```text
tiny kernel booted
square 1 -> 1
square 2 -> 4
square 3 -> 9
square 4 -> 16
square 5 -> 25
sum of squares: 55
```

That is the whole bare-metal image's output: the compiler's `_start` zeroed `.bss`, set
the stack and called `kmain`, which wrote bytes to a device register one at a time.

## A fault on bare metal

Wrong code still stops. This kernel reads index 3 and 4 of a three-element array:

```kelp
impl "uart" caps(mmio = ["0x10000000+0x100"])

section(".text.boot") fun kmain() {
    uart.puts("about to read past an array\n")
    val cells: [u8; 3] = [1, 2, 3]
    var i: usize = 0
    var total: u32 = 0
    while i < 5 {
        total += cells.get(i = i).to_u32()
        i += 1
    }
    uart.puts("never printed\n")
    uart.halt()
}

fun kp_panic(msg: str) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts("\n")
    uart.halt()
}
```

```text
about to read past an array
panic: Array.get: index out of bounds
```

The bounds check the compiler inserted called the project's `kp_panic` with its static
message, which wrote to the same serial port and halted. That is what `[target] panic` is
for: with no process to end and no stderr, the project decides what a failure looks like.
(`panic` also accepts a three-argument shape that receives the file and line.)

## No C backend

```text
$ KELPC_ORACLE=c kelpc build tinyk -o out
error: 'tinyk' sets '[target] mode = "freestanding"', which only the llvm backend can build: the C backend's runtime preamble is libc (the KELPC_ORACLE switch cannot build a freestanding project)
```

## Exercises

1. Change `kmain` to print the cubes of 1 to 4 and then `done`. Boot it.
2. The linker script puts `.text.boot` first. What would happen if `kmain` were not placed
   there, given that QEMU's `-bios none` jumps to `0x80000000`? (This is a design question;
   the answer is in the comments of `kernel.ld`, and I did not boot a broken variant.)

<details>
<summary>Solutions</summary>

1. Only `main.kp` changes (`coral.toml`, the linker script and `uart.kp` are the same):

```kelp
impl "uart" caps(mmio = ["0x10000000+0x100"])

fun put_num(n: u64) {
    if n >= 10 {
        put_num(n / 10)
    }
    uart.putc(48 + (n % 10).to_u8())
}

section(".text.boot") fun kmain() {
    var i: u64 = 1
    while i <= 4 {
        uart.puts("cube ")
        put_num(i)
        uart.puts(" = ")
        put_num(i * i * i)
        uart.puts("\n")
        i += 1
    }
    uart.puts("done\n")
    uart.halt()
}

fun kp_panic(msg: str) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts("\n")
    uart.halt()
}
```

Booted the same way, the serial port showed:

```text
cube 1 = 1
cube 2 = 8
cube 3 = 27
cube 4 = 64
done
```

2. QEMU's `-kernel` with no firmware starts at `0x80000000` rather than at the ELF entry,
   so whatever the linker puts first in `.text` must be the code meant to run first.
   The script says so in its comments, and the compiler's `_start` stub is what the ELF
   entry names. I did not try the broken variant.

</details>

Next: [Polyp UI](/tutorial/17-polyp).
