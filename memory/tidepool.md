---
title: "Tidepool memory design"
description: "Index of the Tidepool memory design pages. Tidepool is in design, and its pages are empty placeholders."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool memory design

Tidepool is the planned memory design for Kelp. It puts blocks beside a shared pool.
It is in design, and nothing on these pages is final.

The collector on `main` is the base mark-region collector. None of the Tidepool
pieces are on `main` yet: no blocks, no shared pool, no high-water index, and no
growable root table.

## Pages

- [The idea](/memory/tidepool/idea)
- [The boundary](/memory/tidepool/boundary)
- [Blocks at runtime](/memory/tidepool/blocks)
- [The budget](/memory/tidepool/budget)
- [Settings in `[tidepool]`](/memory/tidepool/settings)
- [Safety rules](/memory/tidepool/safety-rules)
- [The allocation path](/memory/tidepool/allocation-path)
- [Safety tests](/memory/tidepool/safety-tests)
- [Build order](/memory/tidepool/build-order)
- [Performance claims and how they are measured](/memory/tidepool/performance-claims)
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view)
- [Test plan](/memory/tidepool/test-plan)
- [Tooling and release](/memory/tidepool/tooling-release)
- [Failure and recovery](/memory/tidepool/failure-recovery)

Most of these pages are empty until the design is settled.
