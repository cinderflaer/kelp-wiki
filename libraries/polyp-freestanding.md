---
title: "Polyp on bare metal: the freestanding framebuffer proof"
description: "How the same Polyp core, rasterizer, soft backend and todo program run with no libc on riscv64 and x86-64 QEMU: the two kernels, the shared step log, the checksum lines, and what a bare-metal project provides."
isPublished: true
tags: "library, ui, freestanding"
---
Polyp's display-free half draws into any framebuffer a `Platform` hands it, so it
also runs with no operating system under it. The proof is two bare-metal
projects, `examples/polyp-fb-riscv64/` and `examples/polyp-fb-x86_64/`, that link
the same `core.kp`, the same `backends/soft/soft/` rasterizer, the same `soft_backend.kp` and
the same application program into an image with no libc, boot under QEMU, and
print a checksum per frame. The claim is narrow and total: they draw the **same
pixels** as the hosted run. The original design is
[`plan/polyp-v3.md`](https://homelabone.xenoo.dev/gitea/Lilly/kelp/src/branch/main/plan/polyp-v3.md),
stage 4, with the display stretch in
[`libraries/polyp-freestanding.md`](/libraries/polyp-freestanding).
The v4 hosted demo is also checked against both freestanding kernels when the
corresponding QEMU and linker are available; see
[`libraries/polyp.md`](/libraries/polyp).
Freestanding mode itself is [its own language page](/language/freestanding); this
stage is LLVM-only, as every freestanding build is.

The soft backend, the rasterizer and the `Platform` contract are on
[Polyp on a framebuffer](/libraries/polyp-soft).

## The two kernels

Each project is a `[target]` freestanding build,
[the `kernel0` shape](/language/freestanding) plus four things:

- A `static mut FB: [u32; FB_W * FB_H]` at 320x200, 256 KiB of `.bss` that the
  compiler's `_start` stub zeroes like every other static. The project's platform
  hands it to the backend as an `fb.Fb` with `stride_px = FB_W`.
- A bump arena in a second `static mut [u8; N]`, named by `[target] alloc` and
  `[target] dealloc`, so `List`, `String` and `Box` allocate through the project
  and the image links no libc.
- A platform, `FbPlatform`, that implements `backends/soft/soft/platform.Platform`:
  `framebuffer` returns the static surface, `present` counts the rectangles it was
  handed and advances a fake clock by 100 ms, `now_ms` returns that clock, and
  `poll_event` answers from a timed script that is empty here, because the
  scenario drives the programmatic `core.Event` channel exactly as the hosted run
  does.
- A UART writer for the step lines, and a `[target] panic` handler that prints
  `panic: <msg>` and halts.

The two targets are the two `kernel0` boots:

| Project | Machine | Output | Halt |
| --- | --- | --- | --- |
| `polyp-fb-riscv64` | QEMU `virt`, `-bios none`, started at `0x80000000` | UART at `0x10000000` | `wfi` loop |
| `polyp-fb-x86_64` | QEMU `-M q35` through the PVH stub | COM1 at `0x3F8` | `hlt` |

Only the riscv64 manifest has a `[caps]` section: it grants `mmio` for the UART
window (`0x10000000+0x100`) and for the fw_cfg window the `ramfb` registration
writes through (`0x10100000+0x20`). The framebuffer is a static, not
memory-mapped, and the x86-64 port driver moves a COM1 byte through `in`/`out`,
so neither needs a grant and the x86-64 manifest has no `[caps]` section. Both
manifests list the modules that carry a pointer (`uart`, `fb_platform`,
`deps/polyp/backends/soft/soft/fb`, `deps/polyp/backends/soft/soft/draw`).

On riscv64 the project also registers its static surface with QEMU's `ramfb`
device through fw_cfg (`src/ramfb.kp` reads the file directory, finds `etc/ramfb`
and writes its 28-byte config, all big-endian), so `-device ramfb` scans out those
exact pixels on a real screen. That is the one place a display device appears; the
pixels still come from the same renderer.

## The shared scenario and the step lines

The three runs share their driver. `examples/polyp-todo/src/scenario.kp` builds
the program's initial state, applies `core.create_all`, paints and presents the
first frame, schedules every `app.script()` event on the backend, then calls
`soft_backend.frame` until the program quits, emitting one line per step:

```text
step <n> checksum 0x<16 hex digits> dirty <rectangles painted>
```

`n` is `0` for the first frame and `1..` for one scripted event each, because
`SoftBackend.pump` releases exactly one queued `core.Event` per frame. `dirty` is
`SoftBackend.last_painted`, the count `paint` returned for that frame, so an idle
frame reports `0`. `emit` is a plain `fun(str)`: the hosted entry prints, the
kernels write the bytes to their UART. The line is built in the scenario module,
not by the platform, so the two sides cannot format the same checksum differently.

The same driver finishes with the program's human-readable report
(`examples/polyp-todo/src/report.kp`, separate from `app.kp` because its body
calls `print`, which a freestanding build refuses wherever it appears). The plan
quotes the kernel's first and last step as:

```text
step 0 checksum 0xf0b341c4a10c78b5 dirty 1
...
step 11 checksum 0x0e6a6aa56d77ac07 dirty 0
```

The last line of a run is `display 0x<16 hex digits>`, and it is a different
checksum on purpose. `checksum` hashes all four pixel bytes including alpha, and
the renderer writes glyph coverage into a text pixel's alpha; a screen has no
alpha. `checksum_rgb` hashes blue, green and red with a constant `0xFF` where
alpha goes, and that is the value the display comparison uses.

## How to run it

Both projects and the equivalence test need `ld.lld` and an emulator on `PATH`,
which is the repository's `dev-kernel.nix` shell, and a `kelpc` built there
(`run.sh` looks for `target/debug/kelpc`; set `KELPC` to point at another binary).

The test that compares the kernels with the hosted run:

```sh
nix-shell dev-kernel.nix --run 'cd kelpc && cargo test --test compile_and_run polyp_fb'
```

The two manual boots:

```sh
nix-shell dev-kernel.nix --run 'examples/polyp-fb-riscv64/run.sh'
nix-shell dev-kernel.nix --run 'examples/polyp-fb-x86_64/run.sh'
```

`run.sh` builds the project, boots it under `timeout 20 qemu-system-<arch>`,
captures the serial bytes, waits for a whole-line marker (default `end` and
`done`), and asserts each requested line is present. It prints what the UART
actually said; nothing reads the kernel's intent. The scripts exit non-zero if the
emulator is not on `PATH`.

### What the comparison proves

The Rust test builds `examples/polyp-todo-soft`, runs it with
`POLYP_SOFT_SIZE=kernel` (320x200, the kernels' resolution), builds each kernel,
boots it under `timeout 20 qemu-system-<arch>`, and compares the two outputs line
by line from the first `step ` line to the report's `end`, dropping the hosted
entry's `-- todo --` separator. A single pixel difference anywhere fails it. The
report is compared too, on purpose: the same comparison that proves the pixels
also proves the whole state machine (both `update`s, the keyed diff, the counters
and the entry text) ran identically with no libc. The test also asserts that
`llvm-nm -u` reports no undefined symbol for each image, which is the proof that
nothing reached libc or a soft-float helper. Both tests skip where `ld.lld` and
the emulator are absent.

`polyp_fb_riscv64_shows_its_framebuffer_on_a_real_display` is the ramfb stretch:
it boots the riscv64 image with `-device ramfb -display none` and a monitor on a
pipe, asks for a `screendump`, and compares the captured PPM with the kernel's own
`display` line, so the display check is a checksum comparison and not a golden
image.

## What a bare-metal project must provide

There is no libc and no runtime behind a bare-metal Polyp image, so a project
writes a few more facts down in its `coral.toml`. `examples/polyp-fb-riscv64/` is
the worked example (about two hundred lines of project code;
`examples/polyp-fb-x86_64/src/fb_platform.kp` is literally the same file):

1. **A framebuffer.** The platform owns it. A `static mut [u32; W * H]` in `.bss`
   is enough, and `_start` zeroes `.bss`, so the surface starts black the way
   `HeadlessPlatform` zeroes its own buffer. A device framebuffer works too and
   needs the `mmio` grant.
2. **The platform itself**, in a module of the project: `framebuffer` returns the
   `Fb` over the static (bind the pointer with `Ptr.from_mut(FRAME)`, then
   `cast<u32>()`), `present` counts or composites, `now_ms`/`now_us` return the
   platform's clock or a fake one, and `poll_event` returns `None` or the next
   queued event.
3. **`[target] alloc` and `dealloc`** with the fixed signatures
   (`fun alloc(size: usize, align: usize) => Ptr<u8>`,
   `fun dealloc(p: Ptr<u8>, size: usize, align: usize)`). The bump arena is the
   smallest one that works; a real allocator implements a better bump or a free
   list against the same two names.
4. **`[target] panic`**, a handler that never returns, so a bounds or overflow
   check (and a failed allocation, which the compiler calls with
   `"out of memory"`) prints something instead of wedging.
5. **A way to write bytes out.** The examples' UART writer walks a line with
   `str.len`/`str.byte` one byte at a time; nothing in Polyp needs a formatted
   write, because the scenario builds its own lines.
6. **`[unsafe] modules`** for the modules that take a pointer to the surface or
   write a pixel (`fb_platform`, `backends/soft/soft/fb`, `backends/soft/soft/draw`) and the device driver.
   `core.kp`, `soft_backend.kp`, `font.kp`, `damage.kp`, `event.kp`,
   `platform.kp` and the scenario contain no `unsafe`.
7. **`[caps] mmio`, only for a memory-mapped device.** A UART at a fixed address
   needs the grant and an `impl "uart" caps(mmio = [...])` on the line that
   imports the driver. A port-mapped device needs no grant at all.
8. **Optional: a display device.** Putting the surface on a screen is one more
   device; the riscv64 example registers its static with QEMU's `ramfb` through
   fw_cfg, which is its own `mmio` window and one more `[unsafe]` entry.

What a freestanding project **cannot** do is [the usual list](/language/freestanding):
no `print`, no libc, no `std/*` outside the admitted subset, no passdowns, and no
`String`/`Bytes` without an allocator.

## What the core had to change

The whole Polyp program needed four source changes to fit the freestanding
allowed set. None is a compiler change:

1. **The progress fraction is an integer permille, not an `f64`.** `Props.permille`
   and the `progress` widget carry an `i32` in `0..=1000`. The `f64` comparison in
   `node_props_eq` and the view's `done.to_f64() / total.to_f64()` were two
   soft-float calls on a riscv64 target with no FPU. `backends/soft/soft/frac.kp`, which
   decoded an `f64`'s bits into a permille for the paint path, is deleted;
   `backends/gtk/gtk_backend.kp` and `backends/headless/headless_backend.kp` convert the permille to the `f64`
   GTK and the text dump want, hosted arithmetic no bare-metal image emits.
2. **The core's counters are `Atomic` statics.** A passdown is refused bare-metal
   because its initializer runs through `kelp_init_pds`, which only the hosted
   entry point calls. An `Atomic` static's methods write through a shared borrow,
   so the core still contains no `unsafe`.
3. **The entry-text snapshot moved to `core/diag.kp`.** It is the one
   counter that is a `List<String>`, and a heap type cannot be a static.
   `diag.capture(backend)` runs at the end of a hosted run; a freestanding project
   does not import the module.
4. **`core.kp` no longer imports `std/fmt`.** Its one use was `fmt.int` in a
   duplicate-key panic message; `str.from_i64` is the same text and is in the
   freestanding `std/str` subset.

### What stage 4 found

- **A keyable user type with a `String` field could not link freestanding.** The
  compiler emits a derived `kelp_hash_<T>`/`kelp_eq_<T>` pair for every keyable
  type in the program, whether or not anything uses it as a `Map` key, and the
  generated equality compares a `String` field through `kelp_map_key_eq`, which
  has no freestanding body. Polyp's own types hit it first (`core.Event`,
  `core.Key`, `core.Seg`, `app.Msg`, `app.Todo`, `Option<String>`). The fix is
  in the Polyp source, with the language's own escape hatch: the types declare a
  real `hash`/`eq` pair, which makes the compiler skip the derived one, and
  `soft_backend.find_text` writes into a caller's `String` instead of returning
  an `Option<String>`. The pairs are hand-written with `str.len`/`str.byte`, so
  `Map` still works. The freestanding compiler half (emit a body
  for `kelp_map_key_eq`, or emit the derived pair only for a type a `Map` really
  keys) is recorded as a gap, not fixed here.
- **Two language shapes the code works around**, both already in the gap list: a
  borrow of a temporary cannot be an argument
  (`emit(step_line(...).as_str())` is refused; bind it first), and a trait
  method's implementation must spell its parameters exactly as the trait does,
  unused name included.
- **`fn` types have unnamed parameters.** `fun (line: str)` is a parse error; a
  function type is `fun (str)`.

## See also

- [Polyp on a framebuffer](/libraries/polyp-soft): the rasterizer, the soft
  backend and the five-function `Platform` contract
- [Polyp](/libraries/polyp): the backend-neutral core and the GTK backend
- [Freestanding mode](/language/freestanding): `[target]`, the admitted `std`
  subset and the linker script
- [Kernel 0](/language/kernel): the other QEMU boots these two projects are built
  from
