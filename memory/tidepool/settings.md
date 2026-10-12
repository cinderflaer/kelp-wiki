---
title: "Tidepool: settings in `[tidepool]`"
description: "Empty placeholder for a Tidepool design area. Tidepool is in design."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: settings in `[tidepool]`

Not on `main`. `kelpc` reads no `[tidepool]` section on `main`. An unknown manifest section
is ignored without a message, so a `[tidepool]` section has no effect on `main` and is not
reported.

The only memory key on `main` is `[target] heap_max`, in MiB, from 1 to 65536, with a
default of 256. It caps the collector's heap in a hosted build.

The design plans three keys in `[tidepool]`: `headroom_pct`, `heap_min` and `trigger_rule`.
The candidate rules for `trigger_rule` are `two-size`, `last-size` and `gogc-style`. The
defaults are still being measured on the Tidepool branch, and none of these keys is final.
