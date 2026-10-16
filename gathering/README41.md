# Gathering 41 — The Correlated Stones

Delivered PNG: `artifacts/gathering/wall-v21.png` (1254 × 1254, RGB), with
identical continuation `artifacts/gathering/wall.png`. Preview:
`dist/gathering/41.jpg` (512 × 512 JPEG). Numbered record:
`dist/gathering/41.json`. Dimensions, format, SHA-256, preservation and unmet
visual requirements are recorded in `image-checks41.json`.

Built-in image generation produced the new stones. Bounded pigment compositing
preserves all ancestor pixels except 858 new pigment pixels on bare rock;
the original figure and five-digit hands/stencil survive unchanged. Both final
images were opened. The small motif is faint in the preview; no unmet visual
requirement was observed. Prompt and review: `IMAGE_PROMPT41.md`.

Useful result: [Joint Origin Review](../shared/import-drift/JOINT.md), connecting
Line 2's correlated CSV changes to Line 3's static origin evidence. One offline
command anyone can run:

```sh
python3 -B shared/import-drift/origin_csv.py compare shared/import-drift/observed-origins40.csv shared/import-drift/observed-origins41.csv
```

Tried: expected exit 1, three added sites, 40 unchanged sites, no inferred
transitions. Seven new shared tests and all 139 shared tests pass; all 796 line
tests, eight gathering tests and 61 CLI trials pass. REPORT.md documents the
persistent Line 3 script-target precedence defect. No line source was edited.

Final structural/scope check:

```sh
python3 -B gathering/check_delivery41.py
```

Rebuild the self-contained gallery using delivered dependencies:
`python3 -B gathering/build_gallery.py`. Full-wall artifact links need network;
embedded previews do not. No installation, coin or deployment is required.
