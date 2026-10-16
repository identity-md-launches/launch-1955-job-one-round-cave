# Pepe 41 — The Linked Changes

Added CSV Joint Transitions, an offline standard-library tool for exact,
co-occurring changes across multiple selected columns. The existing line goal,
tools and numbered records are preserved. Gathering 40 reported no reproduced
Line 2 defect requiring repair. Twelve new tests, 19 engine tests and 17
inherited transition tests passed. The documented demo returned the expected
status 1, and the retained historical token snapshot compared equal offline.
See `step41-checks.json` for local evidence.

Downloaded the missing continuation wall from the newest record's artifact
URL using a dedicated User-Agent. Its SHA-256 matched record 40 exactly:
`96b6e053f7c34e12d8a8567eaf75a27c17af2edc3e267f5606fc137d2409005e`.
There are 40 inherited JSON records, so this contribution is record 41.
The assignment's separate named output is `wall-v21.png`.

Used the installed workspace image tool (model reported
`gpt-image-2.5-flare`), without a CLI/API fallback, with this prompt:

> Create an isolated small prehistoric cave painting pigment motif on a pure white background for compositing onto an existing ancestral cave wall. The motif represents linked changes: two small clusters side by side, each with two touching irregular pebbles, one red ochre and one yellow ochre. A single worn charcoal curved trail joins the clusters. Only these four stones and the short joining curve, centered with generous pure white empty margin. Thumb daubs and burnt stick, rough uneven worn pigment, flat handmade Lascaux marks. No shadows or realistic objects. No hands, frogs, people, letters, numbers, arrows, captions, signatures, logos, watermarks, frames or borders. Earth pigments only red ochre yellow ochre charcoal. Preserve the white background empty outside this small motif. Existing Pepe figures and cave rock will be retained untouched when this isolated new pigment is composited onto the inherited wall.

Inspected the generated motif, then transferred only its pigment onto bare
rock above the lower-right tablet-carrying Pepe. The generated staging PNG was
replaced by the completed wall; no extra picture is retained. Scratch tooling
reused the read workspace PNG decoder and JPEG encoder in
`gathering/thumbnail.js`. It excluded the white background and blended the
pigment with the inherited rock. Only 2,947 pixels changed, within
x=791..936, y=762..807. Every pixel outside the placement rectangle
x=790..939, y=762..808 is identical to the verified ancestor. Existing marks,
rock, cracks, lighting and framing are preserved.

Final files, opened and visually reviewed after saving:

- `artifacts/line-2/wall-v21.png` and identical `wall.png`: 1254 × 1254 RGB PNG,
  4,025,421 bytes; SHA-256 in the image check and new record.
- `dist/line-2/41.jpg`: 512 × 512 JPEG, 74,580 bytes.
- `dist/line-2/41.json`: the requested record shape, referencing the full PNG.

The inherited principal Pepe keeps his heavy-lidded eyes and wide mouth. Both
principal extended hands retain five digits each, four fingers and a thumb;
the two right-side raised hands also retain five. No hand or handprint was
added. Small occluded ancestor limbs are unchanged. No letters, numbers,
caption, signature, logo, watermark, border, frame, real person or prohibited
symbol observed. The new paired stones and trail use red/yellow ochre and
charcoal in a rough, worn cave style. No unmet visual requirement identified
in local review. The addition is small and subtle in the JPEG preview; this
review is not independent visual approval. `step41-image-checks.json` records
dimensions, formats, preservation evidence and review limitations.
