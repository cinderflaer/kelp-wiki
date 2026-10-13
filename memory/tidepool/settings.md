---
title: "Tidepool: settings in `[tidepool]`"
description: "Empty placeholder for a Tidepool design area. Tidepool is in design."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: settings in `[tidepool]`

On `main`, `kelpc` reads a `[tidepool]` section in `coral.toml`. Each line in it must be
`key = <whole number>`, except `trigger_rule`, which takes a double-quoted name. An unknown
key is refused by name. `heap_max` under `[tidepool]` is refused with a pointer to
`[target]`. A section header that starts with `tid` in any case, or is `[gc]`, is refused
by name with a 'did you mean [tidepool]' message. Other unknown section headers are still
skipped without a message.

The memory keys on `main` are `[target] heap_max`, a whole number of MiB from 1 to 65536
with a default of 256, which caps the collector's heap in a hosted build, and the
`[tidepool]` keys below. A zero cap is refused.

`[tidepool]` has four keys on `main`:

- `start_low_mib`: a whole number of MiB, at least 1. Default 1.
- `start_high_mib`: a whole number of MiB, at least 1 and no more than `[target] heap_max`.
  Default 4.
- `headroom_pct`: a whole number from 0 to 1000. Default 10.
- `trigger_rule`: a double-quoted name, one of `"two-size"` (default), `"last-size"` or
  `"gogc-style"`.

There is no `heap_min` key. The 8 MiB floor is fixed. Any other key is refused by name.
