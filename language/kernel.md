---
title: "Kernel 0"
description: "The freestanding examples that boot under QEMU: the UART driver, trap handlers, per-CPU statics, Sv39 page tables, a user-mode trap frame and syscall ABI, a bump allocator behind `List`/`String`/`Bytes`, panic locations, a stack guard and `mmio` grants."
isPublished: true
tags: "language, freestanding, kernel"
---
**Kernel 0** is the first proof that Kelp can be a kernel language: a bare-metal
image QEMU's RISC-V `virt` machine starts, which sets up a stack, writes a line
to the NS16550 UART at `0x10000000`, and halts, written in Kelp with no C and no
libc. The order of work that reached it is
[`plan/kernel-path.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel-path.md);
what could not be done is
[`plan/kernel0-status.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel0-status.md).
The build side is [Freestanding mode](/language/freestanding).

## Running one

The examples need `qemu-system-riscv64`, `qemu-system-aarch64` and `ld.lld`,
which `dev-kernel.nix` supplies. Each has a `run.sh` that builds the project,
boots it under `timeout 20 qemu-system-riscv64 -machine virt -bios none
-nographic -no-reboot -serial mon:stdio -kernel <elf>`, reads QEMU's own stdout
until the last expected line appears, kills QEMU, and asserts every expected
line appears whole. Nothing in the script reads the kernel's intent: the
assertion is a comparison against the bytes that came out of the serial port.

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0/run.sh'
```

The script builds with `target/debug/kelpc` by default; `KELPC` points it at
another binary. The real output, from a build of the current tree:

```text
run.sh: booted /home/juniper/Projects/kelp-native-ui/overnight/wt-docs2/examples/kernel0 and the UART printed:
hello from kelp
```

| Example | What it proves | Serial output |
| --- | --- | --- |
| `examples/kernel0` | the driver, the entry, the halt | `hello from kelp` |
| `examples/kernel0-trap` | a trap vector, an `ecall`, `mret` | `trap: ecall` then `done` |
| `examples/kernel0-panic` | the compiler's bounds check reaches the handler | `panic: Array.get: index out of bounds` |
| `examples/kernel0-panic2` | the location-carrying handler, one check per boot, and a double panic | `panic: <message> at <file>:<line>` per phase, then `double panic` |
| `examples/kernel0-bss` | `_start` erased a marker the image loaded into `.bss` | `bss clear` |
| `examples/kernel0-heap` | `List<i32>` over a bump allocator | `heap sum 55` then `balanced` |
| `examples/kernel0-string` | `String`/`Bytes` on the project allocator | `s: hello kelp!`, `n: 12345`, `b: 300`, `balanced` |
| `examples/kernel0-percpu` | `percpu static mut` on two harts | `cpu0 4`, `cpu1 7`, `idx 1`, `count 2` |
| `examples/kernel0-vm` | Sv39 tables, the S-mode drop, a high alias | nine `vm:` lines |
| `examples/kernel0-vm-fault` | the load and store page faults | `fault: scause 0xd stval 0x40000000`, `fault: scause 0xf stval 0x3ffffff000` |
| `examples/kernel0-stack` | an unmapped guard page and the stack probe | both faults print `stack overflow: scause 0xf stval 0x...` |
| `examples/kernel0-user` | the trap frame, `ecall`, U-mode | `hello from user`, `bad write -> E`, `user exited 7` |
| `examples/kernel0-aarch64` | the second architecture | `hello from kelp (aarch64)` |

Every manifest under `examples/kernel0*` also carries an `mmio` grant now, the
stage-16 check that a freestanding module may name only an address it was
granted. The UART drivers hold exactly their device's window
(`0x10000000+0x100` for the riscv64 NS16550, `0x09000000+0x1000` for the aarch64
PL011), and the modules that build a pointer from a computed address (a
page-table frame, a trap-frame slot, a user page) hold the whole-address-space
`["*"]`. See [Capabilities](/language/capabilities#mmio-device-registers).

The four RISC-V boots, run one after another:

```text
run.sh: booted .../examples/kernel0-trap and the UART printed:
trap: ecall
done
run.sh: booted .../examples/kernel0-panic and the UART printed:
panic: Array.get: index out of bounds
run.sh: booted .../examples/kernel0-bss and the UART printed:
bss clear
run.sh: booted .../examples/kernel0-heap and the UART printed:
heap sum 55
balanced
```

And the aarch64 boot, on QEMU's `virt` machine with `-cpu cortex-a57`:

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-aarch64/run.sh'
```

```text
run.sh: booted .../examples/kernel0-aarch64 and the UART printed:
hello from kelp (aarch64)
```

## The driver

The NS16550 `THR` (offset 0) is the byte to send; `LSR` (offset 5) bit 5 is set
while the transmit holding register is empty, so a byte is written only after
that bit reads back set. Every access goes through `Ptr<u8>` and is volatile, so
the compiler can neither merge, reorder nor elide it. The base, the offsets and
the bit are the driver's own claim about the hardware.

```kelp
impl "std/str"

const UART_BASE: usize = 0x10000000
const LSR_OFFSET: usize = 5

pub fun putc(c: u8) {
    unsafe {
        val lsr: Ptr<u8> = Ptr.from_addr(UART_BASE + LSR_OFFSET)
        while (lsr.read_volatile() / 32) % 2 == 0 {}
        val thr: Ptr<u8> = Ptr.from_addr(UART_BASE)
        thr.write_volatile(c)
    }
}

pub fun puts(s: str) {
    val n = str.len(s)
    var i: usize = 0
    while i < n {
        putc(str.byte(s, i))
        i = i + 1
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

Text arrives as a `str`, the same type a hosted program writes, and
`str.len`/`str.byte` are the compiler's own byte loops, so no `strlen` and no
`[u8; N]` copy sits between the caller and the device. `wfi` has no Kelp
spelling, so the halt is inline `asm`; v1 has no bitwise operators, which is why
bit 5 of `LSR` is written `(value / 32) % 2`.

The entry and the panic handler are ordinary Kelp in the entry module:

```kelp
section(".text.boot") fun kmain() {
    uart.puts("hello from kelp\n")
    uart.halt()
}

fun kp_panic(msg: str) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts("\n")
    uart.halt()
}
```

`[target] panic = "kp_panic"` is what routes every compiler-inserted check to
that handler. `kernel0` and `kernel0-panic` declare the one-argument shape; the
three-argument shape that also carries the source location is the section below.
The message is the check's own text, byte-identical to the
C backend's, which is why `kernel0-panic` can assert that the line contains
`index out of bounds` (the line the compiler writes, not one the example chose).

## Panic location and the double panic

A freestanding handler may take the compiler's location as well as the message:
`examples/kernel0-panic2` declares the three-argument form, and the compiler
refuses every other shape by name.

```kelp
fun kp_panic(msg: str, file: str, line: u32) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts(" at ")
    uart.puts(file)
    uart.puts(":")
    put_u32(line)
    uart.puts("\n")
    uart.halt()
}
```

`file` is the source file name the diagnostic's `-->` ends with (`main.kp`) and
`line` is the 1-based line of the statement the check was inserted into. The
location names the statement, not the exact sub-expression, because one `locate`
per statement is what the hosted line tables carry too. A check that lives
inside a generated accessor shared by every call site (`Array.get`, `List.get`,
`Bytes.get`, the allocator's out-of-memory path) reads the caller's statement
from two `.bss` globals the compiler stored before it, so the line it names is
the user's; a panic raised inside `std/option`'s own body names `option.kp`.

Every check calls one compiler-emitted entry, and the entry calls the handler
only once: it exchanges a `.bss` flag, and a check that fires while the handler
is already running reaches `kelp_double_panic` instead of recursing. The
compiler defines that weakly as a `wfi` loop; `examples/kernel0-panic2` links a
strong definition beside the object (the same link-time override the `memcpy`
fallbacks use) and prints `double panic`.

One boot can show only one check, because a panic ends the machine, so `run.sh`
rewrites the selector in a scratch copy and boots the project once per check:

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-panic2/run.sh'
```

```text
phase 1: panic: Array.get: index out of bounds at main.kp:37
phase 2: panic: i32.to_u8: value out of range at main.kp:43
phase 3: panic: str.byte: index out of bounds at str.kp:24
phase 4: panic: deliberate panic at main.kp:54
phase 5: panic: Option.unwrap: value is None at option.kp:68
phase 6: double panic
run.sh: all six phases printed the lines the compiler named
```

Every expected line is computed from the source the compiler read (the message
from the check, the line from a `panic-line: <name>` comment in `main.kp` or
from the stdlib file), so the assertion is QEMU's serial bytes against the
compiler's own claim. Integer overflow wraps and division by zero is unchecked
UB, so neither has a message. [Freestanding
mode](/language/freestanding#panic-semantics) carries the whole table of checks.

## The trap vector

`kernel0-trap` installs `mtvec` with `csrw mtvec, {0}` and takes a machine-mode
`ecall`. `mtvec`'s low two bits are the vector mode, so `trap_handler` carries
`align(4)` and its own `section(".text.trap")`; it is a `naked fun` whose whole
body is one `asm`, so no prologue, no epilogue and no compiler-generated `ret`
are emitted around it.

```kelp
pub fun install() {
    unsafe {
        asm("csrw mtvec, {0}", in("r") Ptr.from_fn(trap_handler).addr())
        asm("csrw mscratch, {0}", in("r") Ptr.from_fn(report).addr())
    }
}

section(".text.trap") align(4) naked fun trap_handler() {
    asm("
            csrr t0, mepc
            addi t0, t0, 4
            csrw mepc, t0
            addi sp, sp, -128
            sd ra, 0(sp)
            ... save the caller-saved registers ...
            csrr t0, mscratch
            jalr ra, t0, 0
            ... restore them ...
            addi sp, sp, 128
            mret
        ")
}
```

`Ptr.from_fn(trap_handler)` is the checked address of a declared `fun`, so no
mangled symbol is spelled in the file: the address the checker names is the one
the linker resolves. `report` is reached through `mscratch` for the same reason,
and because an inline-asm operand would make the compiler materialise a register
before the handler had saved anything.

The full `asm` body, the register save list and `examples/kernel0-trap/src/trap.kp`
are in the repository; the point here is that the vector is a naked function
plus one `asm`, and the language never sees the trap.

## Address spaces: Sv39

The mapping stage is `examples/kernel0-vm`. Its Sv39 module, `src/vm.kp`, is
written in the language the earlier stages built and the one construct it leans
on is the stage-5 `asm`: a linker-script symbol has no Kelp spelling, so the
frame region arrives through `asm("la {0}, __frames_start", out("r") _)`, the
same way the compiler's own `_start` reaches `__stack_top`. The design is
[`plan/address-spaces.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/address-spaces.md).

The module carries the PTE bit constants (`V R W X U G A D`), the three-level
VPN split, the PTE and `satp` encoders and decoders, a bump frame allocator
over `__frames_start..__frames_end` (one zeroed 4 KiB frame per call, because a
fresh table's absent entries must read as invalid), `map_page`, `map_range`,
`unmap_page` and `translate(root, va) -> Option<usize>`. Every memory access is a
`Ptr<u64>` volatile load or store, and the only two CSRs are `satp` and
`sfence.vma`, both written through `asm`, so `vm` is on the manifest's
`[unsafe] modules` list.

The boot in `src/main.kp` prints one line per step: machine-mode start, a root
table, an identity map, the UART page, the high page, the drop to supervisor
mode, paging on, the alias and the unmap. The image, its stack and the frame
region are identity-mapped as one 4 MiB RWX span; splitting `.text`/`.rodata`/
`.data` apart needs section bounds the language cannot name, and the point of the
stage is the walk, not W^X. One page at `0x3F_FFFF_F000` (one page below 2^38,
the highest canonical Sv39 low address) maps to a fresh frame. Under paging the
kernel writes `0xC0FFEE` through the high virtual name, reads it back, asks
`translate` for the physical address and reads the same bytes through the
identity map, then unmaps the high page, flushes the TLB and checks that
`translate` answers `None`.

The transition to S-mode is the standard path, all four steps in
`enter_supervisor`: `pmpaddr0` all ones with `pmpcfg0 = 0x1F` (one NAPOT entry
covering memory, without which every S-mode access faults because no entry
matches), `medeleg` granting the page faults to S-mode, `mstatus.MPP = S`, and
`mret` through `mepc`. The tables are built in machine mode, which does not
translate, and `satp` is written in supervisor mode, so the code that turns the
MMU on is already running at the privilege the MMU applies to.

The second example, `examples/kernel0-vm-fault`, is the S-mode handler. `stvec`
names a naked `align(4)` function, the stage-5 idiom, which saves the
caller-saved registers, calls its report function through `sscratch`, and either
advances `sepc` by the faulting instruction's own length (read from its low bits,
because the target enables the compressed extension) and `sret`s, or halts.
`kmain` maps one leaf with R and no W, and `smain` takes two faults on purpose:
a load from an address no leaf maps (`scause` 13, `stval` the address) and a
store to the read-only leaf (15). One boot prints both.

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-vm/run.sh; examples/kernel0-vm-fault/run.sh'
```

```text
run.sh: booted .../examples/kernel0-vm and the UART printed:
vm: m-mode
vm: root
vm: identity
vm: uart page
vm: high page
vm: s-mode
vm: paging on
vm: alias ok
vm: unmap ok
run.sh: booted .../examples/kernel0-vm-fault and the UART printed:
fault: m-mode
fault: paging on
fault: scause 0xd stval 0x40000000
fault: scause 0xf stval 0x3ffffff000
```

What this stage deliberately leaves out: TLB shootdown (`flush_tlb` is one local
`sfence.vma`), ASIDs (`satp` always carries ASID 0), huge pages (the walker
translates a superpage leaf and refuses to split one, but `map_page` only writes
a 4 KiB leaf), Sv48 (only mode 8 is encoded), W^X, and demand paging. Frames are
never freed once a table holds them.

## Traps, user mode and the syscall ABI

`examples/kernel0-user` is the same Sv39 boot plus five things: `src/trap.kp`
(the `TrapFrame`, the naked `trap_entry`, `trap_dispatch` and `enter_user`),
`src/syscall.kp` (the numbers, `write` and `exit`, and the copy path),
`src/user.kp` (two hand-written user programs, each a naked function in its own
section, copied into its program's code page at boot), `src/vm.kp` (the walker
plus `user_page_pa`, the walk that demands the U and R bits), and a `kernel.ld`
with the hart's trap stack and the enlarged frame region. The design is
[`plan/syscall-abi.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syscall-abi.md).

The trap frame is a convention the compiler cannot see, so both ends pin it:

```kelp
repr(c) datac TrapFrame(
    val x1: u64, ... val x31: u64,
    val sepc: u64, val sstatus: u64)
```

`x1`..`x31` sit at offsets 0 to 240, `sepc` at 248 and `sstatus` at 256, so the
frame is 264 bytes and 8-byte aligned. Only `x2` is special: the hardware leaves
`sp` in the register, not the frame, so the entry recovers the interrupted `sp`
from `sscratch` and stores it in the `x2` slot, and the resume path puts it back
through `sscratch` as well. Each hart gets one 4 KiB trap stack, and `sscratch`
holds its top while user code runs, so the entry's first instruction is
`csrrw sp, sscratch, sp`. The 40 bytes above the frame are a slot block holding
the entry `sp`, the resume `ra` and `sp`, and the address of `trap_dispatch`, so
the naked entry has no instruction of its own to compute an address. The entry
calls `trap_dispatch` with `a0` = the frame address; a nonzero return resumes the
program, zero means the kernel leaves and picks up `enter_user`'s frame from the
slots. `enter_user(root, entry, sp)` writes `satp` and one `sfence.vma`, sets
`sepc`, `sscratch` and the entry slot, clears `sstatus.SPP` and sets `SPIE`, and
`drop_to_user`, a naked `sret`, is the last call. The boot prints
`user: frame ok` only when `size_of<TrapFrame>()`, `offset_of("x17")`,
`offset_of("sepc")` and `offset_of("sstatus")` agree with the same constants the
asm uses.

An `ecall` from U-mode puts the number in `a7`, the arguments in `a0`..`a5`, and
the result in `a0`; a negative result is an error. Registers move through the
frame, and `sepc` advances by 4 (an `ecall` is never the compressed form).

| number | name | arguments | returns |
| --- | --- | --- | --- |
| 0 | `write` | `a0` = fd (only 1), `a1` = pointer, `a2` = length | the length written |
| 1 | `exit` | `a0` = code | does not return |

Errors are the small negative errno values: `-9` (`EBADF`) for a file descriptor
other than 1, `-14` (`EFAULT`) for a pointer the kernel will not copy from, and
`-38` (`ENOSYS`) for a number the kernel does not know. `exit` is the one syscall
that does not return: the handler prints `user exited <code>` and the dispatcher
tells the entry to leave the kernel rather than resume the program.

`write` is the only way user memory crosses into the kernel, and it copies
through a kernel buffer. Before any byte moves, the pointer is validated:

- `len > 4096` is refused, so one call can never ask for more than the kernel's
  one-frame copy buffer.
- `ptr > USER_LIMIT - len`, with `USER_LIMIT = 2^38` (one past the highest
  canonical Sv39 low address), refuses a range that would wrap `ptr + len` and
  refuses every pointer at or above the user limit. The arithmetic is written so
  the addition itself cannot overflow, because a wrap would slip a range past
  the bound check instead of being refused.
- The copy walks the program's page table one page at a time with
  `vm.user_page_pa`, which answers only when the leaf has **both** `PTE_U` and
  `PTE_R`. A kernel address that happens to be mapped (the identity map is in
  every program's table) is not user-readable, so it is refused here and not by
  a lucky address range.
- Each page's bytes are read from the **physical** address the walk returned,
  through the identity map, into the buffer, and the buffer is what the UART
  driver writes. The user virtual address is never dereferenced, so a page the
  walk rejects cannot be reached by a second access that races a remap.

The refused pointer prints the demo's own line (`user: efault ok`) and returns
`-14`; the kernel keeps running and the program sees the error in `a0`.
Program one calls `write(1, "hello from user\n", 16)`, then
`write(1, 0x80000000, 16)` (a mapped kernel page), builds `bad write -> X` on its
stack, replaces `X` with `55 + (-a0)` (the hex digit of the errno magnitude, so
`-14` prints `E`), writes it, and calls `exit(7)`. Program two loads from
`0x40000000`, which no leaf maps in its address space: the load page fault is
`scause` 13, the handler prints `user killed: scause 13` and leaves, and the
kernel prints `kernel survived`.

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-user/run.sh'
```

```text
run.sh: booted .../examples/kernel0-user and the UART printed:
user: m-mode
user: s-mode
user: paging on
user: frame ok
hello from user
user: efault ok
bad write -> E
user exited 7
user killed: scause 13
kernel survived
```

What is deliberately **not** here: no scheduler (one process at a time, one hart,
no run queue and no context switch between two live programs, since program two
starts only after program one has ended), no preemption (no timer interrupt is
armed, so a spinning program is never killed), no `fork`, `exec`, `wait` or
process teardown (pages are never freed and no address space is ever reused), no
ASIDs or TLB shootdown, no copy-on-write, demand paging, guard pages or address
space abstraction, and no interrupt path (`trap_entry` assumes the trap came from
U-mode; a kernel-mode fault would swap the stack pointer out from under the
running handler). There are no signals, and no more than six syscall arguments.

## Stack guards and probing

`examples/kernel0-stack` is the overflow made loud. Every function a freestanding
LLVM build emits carries LLVM's `"probe-stack"="inline-asm"` attribute, so a
frame larger than one page is built by touching each page in order from the top;
a frame that reaches the guard page below the stack faults instead of a single
`sub sp` stepping over the hole. Hosted builds carry no attribute, because a
hosted process has no guard page to probe for.

The linker script puts a 16 KiB trap stack below the image, an unmapped 4 KiB
guard page above it and the 8 KiB kernel stack above the guard. `kmain` identity
maps `[image, __guard_bottom)` and `[__guard_top, __frames_end)` and leaves the
guard page with no leaf.

One boot takes the two overflows on purpose. Phase a recurses with a 16-byte
frame until the frame that crosses `__stack_bottom` stores its saved `ra` into
the guard; the S-mode handler runs on the trap stack, prints the `scause` and
`stval` it saw, checks `stval` against the guard bounds and, for the first fault,
points `sepc` at phase b and returns. Phase b calls a function whose single
`[u8; 16384]` frame is larger than the whole kernel stack: the probe walks it
down page by page into the same guard, which is the case a `sub sp` alone would
miss.

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-stack/run.sh'
```

```text
run.sh: booted .../examples/kernel0-stack and the UART printed:
stack: m-mode
stack: paging on
stack: guard 0x80007000 0x80008000
stack: phase a
stack overflow: scause 0xf stval 0x80007ff8
stack: stval in guard
stack: phase b
stack overflow: scause 0xf stval 0x80007de0
stack: stval in guard
stack: halted
```

Both faults are `scause 0xf`, a store page fault, and each `stval` falls inside
the guard the kernel printed. `run.sh` asserts the seven `stack:` lines, and the
suite's boot test parses the printed bounds and both fault addresses to check
the same range independently.

What this is not: the guard page is the linker script's, not the compiler's
(`probe-stack` only turns a large frame into stores, and whether they land on an
unmapped page is the script's business), the probe does not compare `sp` against
a bound and does not run on a `naked` function, and nothing maps a page to grow
the stack. See
[`plan/stack-guard.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/stack-guard.md).

## The `.bss` clear

`_start` zeroes `[__bss_start, __bss_end)` after it loads `sp` and before it
calls the entry, with both bounds declared weak. `kernel0-bss` proves the loop
ran by having the image load a 64-byte marker into a `PROGBITS` section the
script places inside that range, so `bss clear` can only be printed if the bytes
were erased first. The marker is defined by assembler directives (`@progbits`),
because LLVM's own section-name heuristic turns any `.bss.*` name into `NOBITS`
and the initializer would be lost.

## The linker script

QEMU's `-bios none` starts the image at `0x80000000`, not at the ELF entry, so
`_start` has to hold that address. `.text.boot` is placed first, and naming it
first is not enough on its own: `lld` places an unnamed orphan (`.eh_frame`,
which LLVM emits for the driver functions' unwinding tables) *before* `.text`,
so the script names `.eh_frame` explicitly and gives it its own output section.
`kernel.ld` also defines `__stack_top` 16 KiB above the image, which the stub
loads into `sp`. These two facts are the only ones the stage-4 note said a
script could get wrong silently.

## What is still missing

The remaining gaps, in order, from
[`plan/kernel0-status.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel0-status.md):

- **Interrupts are not set up.** `kernel0-trap` installs `mtvec` itself and
  nothing enables `mstatus.MIE`, models the privilege transition or claims an
  interrupt line as a capability. Panic semantics with no OS, the row's other
  half, is the [section above](#panic-location-and-the-double-panic).
- **The `interrupt`/calling-convention attributes** stage 5 deferred are still
  open, so a trap handler is a naked body the compiler does not understand as a
  handler.
- **`Ptr.alloc`/`Ptr.free` still have no allocator hook.** The global allocator
  reroutes `Box`/`List`/`Map`/`String`/`Bytes`, and stage 13 added the
  [`std/arena`](/stdlib/arena) bump region and the fallible `Ptr.try_alloc`, but
  the `Ptr.alloc`/`free` pair is still the hosted `malloc`/`free` and is refused
  in freestanding.
- **Stages 6, 8, 9, 12, 13, 14 and 16 have shipped.** User `Drop` (stage 6) is
  [`fun mut T.drop()`](/language/drop); per-CPU storage (stage 8) is
  [per-CPU statics](/language/percpu); the MMU and the syscall ABI (stage 9) are
  the two examples above; freestanding `String`/`Bytes` and arena/`try_alloc`
  (stages 12 and 13) are [Freestanding mode](/language/freestanding) and
  [`std/arena`](/stdlib/arena); the stack guard and the `probe-stack` attribute
  (stage 14) are the section above; and the `mmio` capability (stage 16) is the
  grant every example now carries.
- **IRQ lines and physical frames** (the rest of the capabilities row) are what
  remains: an abort message and a register dump are still not here.
- **No C-oracle coverage.** Freestanding is LLVM-only by design, so the usual
  "both backends, same behaviour" rule does not apply to these images. It still
  holds everywhere else.

## See also

- [Freestanding mode](/language/freestanding): the `[target]` section, the
  allowed set and the allocator hook
- [Unsafe code and raw pointers](/language/unsafe): the `Ptr<u8>` volatile
  stores and `Ptr.from_fn`
- [Statics and `defer`](/language/statics-and-defer): `static mut`, the atomic
  static and cleanup on the way out
- [User `Drop`](/language/drop): the destructor a value runs on the way out
- [Per-CPU storage](/language/percpu): one copy of a static per CPU, and the two
  intrinsics that read it back
- [Capabilities](/language/capabilities#mmio-device-registers): the `mmio`
  grant every example carries
- [`std/arena`](/stdlib/arena): the bump region a kernel reaches for after the
  allocator hook
