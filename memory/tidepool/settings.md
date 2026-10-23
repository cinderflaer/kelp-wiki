---
title: "Tidepool: settings in `[tidepool]`"
description: "The coral.toml keys that size the shared heap: [target] heap_max, and the four [tidepool] keys with their defaults, ranges and refusals. Each refusal is the message the compiler prints."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: settings in `[tidepool]`

A hosted program sizes its heap in `coral.toml`. Two places hold the settings:
`[target] heap_max` sets the cap, and the `[tidepool]` section tunes when the
collector clears the pool. The compiler reads both when it builds the program, and
refuses a value it cannot use, by name. Nothing is read at run time.

## The cap: `[target] heap_max`

`heap_max` is a whole number of MiB from 1 to 65536. The default is 256
(`DEFAULT_HEAP_MAX_MIB` and `HEAP_MAX_MIB_RANGE` in `kelpc/src/managed.rs`). A value
outside the range is refused:

```text
error: coral.toml value for '[target] heap_max' must be between 1 and 65536 MiB, found 0
```

The fixture for a zero cap is `project_tidepoolheapmaxzero` in
`kelpc/tests/golden/index.tsv`. A quoted value (`heap_max = "64"`) is refused by
`project_tidepoolheapmaxquoted`.

## The `[tidepool]` keys

`[tidepool]` has four keys. Each line takes `key = <whole number>`, except
`trigger_rule`, which takes a double-quoted name (`kelpc/src/resolve/manifest.rs`).

| Key | Range | Default | What it sets |
| --- | --- | --- | --- |
| `start_low_mib` | at least 1 | 1 | the lower of the two guesses for the first clearing |
| `start_high_mib` | at least 1, and no more than `heap_max` | 4 | the higher guess for the first clearing |
| `headroom_pct` | 0 to 1000 | 10 | the percentage added to each trigger |
| `trigger_rule` | `"two-size"`, `"last-size"` or `"gogc-style"` | `"two-size"` | which live size sets the later triggers |

The start pair must not be reversed: `start_high_mib` below `start_low_mib` is
refused by name (`kelpc/src/resolve/manifest.rs`, commit `d167b1ee`, and the test
`tidepool_start_high_below_start_low_is_refused_by_name` in `kelpc/src/resolve/tests.rs`).

There is no `heap_min` key. The 8 MiB floor on later triggers is fixed
(`DEFAULT_HEAP_MIN` in `kelpc/gc/src/state.rs`). The four keys reach the collector as
the arguments of `kelp_gc_init`, in bytes, through `kelpc/src/codegen_llvm.rs` and
`kelpc/src/codegen_llvm/frame.rs`.

### An example

The fixture `kelpc/tests/managed/tidepool_start` sets a 64 MiB cap and its own start
pair and headroom:

```toml
name = "tidepoolstart"
version = "0.1.0"
entry = "src/main.kp"

[target]
mode = "hosted"
heap_max = 64

[tidepool]
headroom_pct = 50
start_low_mib = 2
start_high_mib = 8
```

The unit test `tidepool_section_reaches_the_collector_init` in `kelpc/src/gc_descr.rs`
checks this project's call. The collector receives the start pair and the headroom
in bytes and percent, and the cap in bytes:

```text
call void @kelp_gc_init(i64 8388608, i64 67108864, i64 2097152, i64 8388608, i64 50, i64 0)
```

The arguments are heap_min, heap_max, start_low, start_high, headroom_pct and the
trigger rule code (0 is `two-size`). The fixture `kelpc/tests/managed/tidepool_rule`
sets `trigger_rule = "last-size"`, and its test
`tidepool_trigger_rule_reaches_the_collector_init` checks the code 1.

## Refusals

Each refusal below is printed by the project named in its row, in
`kelpc/tests/golden/index.tsv`. The message is the one the compiler prints.

| Project | Message |
| --- | --- |
| `tidepoolkeytypo` | `unknown key 'headrom_pct' in coral.toml's [tidepool] section; its keys are 'headroom_pct', 'start_low_mib', 'start_high_mib' and 'trigger_rule'` |
| `tidepoolheapmaxblock` | `coral.toml's [tidepool] key 'heap_max' belongs in [target]; move it there` |
| `tidepoolheadroomrange` | `coral.toml's [tidepool] key 'headroom_pct' must be from 0 to 1000, found '1001'` |
| `tidepoolstringvalue` | `coral.toml's [tidepool] key 'headroom_pct' must be a whole number, found '"20"'` |
| `tidepoolduplicate` | `'headroom_pct' appears more than once in coral.toml's [tidepool] section` |
| `tidepoolstarthighover` | `coral.toml's [tidepool] key 'start_high_mib' must not exceed [target] heap_max (8 MiB), found '9'` |
| `tidepoolstartlowzero` | `coral.toml's [tidepool] key 'start_low_mib' must be at least 1, found '0'` |
| `tidepoolrulename` | `coral.toml's [tidepool] key 'trigger_rule' names no rule 'mean'; its rules are 'two-size', 'last-size' and 'gogc-style'` |
| `tidepoolheapmax65537` | `coral.toml value for '[target] heap_max' must be between 1 and 65536 MiB, found 65537` |
| `tidepoolheapmaxquoted` | `coral.toml value for '[target] heap_max' must be a whole number of MiB between 1 and 65536, found '"64"'` |

Section headers are refused as well. A header that contains `tidepool` in any case,
or that starts with `tid`, is refused unless it is exactly `[tidepool]`. The `[gc]`
name is refused too, and so is the double-bracket `[[tidepool]]`, which is an array
of tables. Each refusal names the header and suggests `[tidepool]`:

| Project | Message |
| --- | --- |
| `tidepoolmisspelled` | `unknown section '[TIDEPOOL]' in coral.toml; did you mean '[tidepool]'?` |
| `tidepoolsectionname` | `unknown section '[target.tidepool]' in coral.toml; did you mean '[tidepool]'?` |
| `tidepoolstaleheader` | `unknown section '[gc]' in coral.toml; did you mean '[tidepool]'?` |
| `tidepoolarraytable` | `unknown section '[[tidepool]]' in coral.toml; did you mean '[tidepool]'?` |

Other unknown section headers are skipped without a message.

A `[tidepool]` section in a freestanding project is refused as well, because a
freestanding build has no shared pool (`kelpc/src/resolve/manifest.rs`).

## Related

- [The budget](/memory/tidepool/budget): what the cap and the triggers do at run time.
- [Tooling and release](/memory/tidepool/tooling-release): the environment variables the collector reads.
- [Tidepool memory design](/memory/tidepool): the index.
- [Freestanding](/language/freestanding): the build mode that has no `[tidepool]`.
