# LichtBlick app check: merged layout import (2026-11-04)

**No data loaded** (layout check only; no SIMULATION or REPLAY data in this image).

`merged_layout_no_data_unavailable.png`: LichtBlick **1.30.0** Linux build (from the SHA-256-verified
`.deb` pinned in `MAIN/dependency-lock.json`), run under WSLg with software WebGL. The merged
`lichtblick_layout.json` was imported through **View → Import layout from file…** (the file picker was
supplied programmatically over the DevTools protocol; the import itself is LichtBlick's own code).

What it shows: the layout imports without errors in the real app, the Operator/Details tabs and all
Operator panels render, and with no input every indicator shows its grey **UNAVAILABLE** fallback and the
camera says "Image and calibration topics do not exist". Captured at 1200×800.

Not shown here: live or replay data in the app. Opening an MCAP through the same automated route did not
load (cause not found); the screenshots with data are to be taken by hand (see `pdr/shot_list.md`).
