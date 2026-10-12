---
title: "Tidepool: the idea"
description: "Empty placeholder for a Tidepool design area. Tidepool is in design."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the idea

Tidepool is the planned memory design for Kelp. It is not on `main`, and nothing here is
final.

- Most values go into a shared pool. Tidepool clears the pool when it fills, and nothing
  in the program reaches a value that the pool has cleared.
- A named block frees the values it owns when the block ends. The compiler writes each
  free. A value that could outlive its block is refused.
- One limit, `heap_max`, covers the shared pool and the block memory together.
- The first clearing is sized from two guesses. Later clearings follow the measured live
  size plus a headroom percentage.

Today `main` has the collector without blocks. See [Tidepool](/memory/tidepool).
