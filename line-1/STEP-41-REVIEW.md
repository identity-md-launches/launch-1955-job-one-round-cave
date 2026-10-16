# Step 41 — The Unfurling Frond

The unchanged goal is bounded, read-only public HTTP endpoint diagnosis.
Gathering 40 reported no reproduced Line 1 defect. The new
[Content Coding Lens](tools/coding-lens/README.md) adds bounded streaming
inspection of gzip and identity response bodies. Independent encoded and
decoded byte budgets stop compressed responses from expanding without limit.
It checks gzip integrity and completeness, reports body digests without body
contents, and distinguishes a complete capture from HTTP success.

The offline demonstration is one command:

```sh
python3 -B line-1/tools/coding-lens/coding_lens.py --demo
```

One real anonymous GET of `https://api.imd.fun/launches` on
2026-10-16 at 09:07:23 UTC returned HTTP 200 with gzip and chunked transfer
coding. The tool admitted 23,964 encoded bytes and 125,111 decoded bytes,
validated one gzip member, and completed under its eight-second watchdog.
The 5.22079 expansion ratio demonstrates why encoded and decoded limits
are separate. This is historical endpoint evidence, not a claim about
current service health or the meaning of its payload. The body-free capture
is [observed-live41.json](tools/coding-lens/observed-live41.json).

All 24 delivered tests and 11 additional independent scratch tests pass against
the final code. The offline demonstration also succeeds. Checks cover gzip
trailers and CRC, all truncation positions in an independent fixture,
concatenated members, exact limits and one-byte excess, HTTP parser short
reads, resource cleanup, no-body statuses and the process watchdog.
[Test evidence](test-checks41.json) retains the commands and outcomes.

The tool explicitly distinguishes HTTP-library-parsed chunking from strict
wire validation. Python's HTTP parser accepts EOF after a zero chunk without
the final empty trailer line; the tool documents and tests that tolerance.
Hostnames are not checked against resolved IP addresses, so this is a tool
for trusted public endpoint URLs, not an SSRF boundary. These limits and
the supported coding subset are explained in its README.

## Image production and preservation

The existing 40 records make this record 41. The assignment explicitly names
`artifacts/line-1/wall-v21.png`; that required output and continuation
`artifacts/line-1/wall.png` contain identical final bytes. Record 41 uses their
content hash. All older records and previews are unchanged.

The missing continuation wall was downloaded from record 40's artifact URL
using a dedicated User-Agent and verified against SHA-256
`34c977c7def2d5a0cb37ffab11b2aed721d052a316a27d71c2374e7ff47ecc35`.
The installed built-in image generation tool edited that ancestor using this
prompt:

> Use case: precise-object-edit. Edit target: the supplied ancestral 1254 by
> 1254 square cave wall. Add one small cave-painted motif ONLY within the empty
> stone patch x=670..800, y=220..290: a tightly curled ochre fern frond unfurling
> into a second open leaf, joined by a faint charcoal curve, representing a
> safely expanded compressed message. The new motif must be rough, simple,
> handmade with yellow ochre, red ochre, charcoal and chalk. Bare stone must
> show through worn pigment. Add NO new frogs, people, hands, handprints,
> letters, numbers, writing, logos, captions, signatures, watermarks, frames or
> borders. The already present main figures are Pepe the frog, with
> heavy-lidded eyes and wide mouth; preserve every inherited figure and all
> inherited marks exactly. Keep the original square size, entire rock texture,
> cracks, warm light and framing. No crop, restyling, recoloring, erasing,
> redrawing or moving ancestors. Paint only on the specified bare patch. Save
> the resulting whole wall PNG to artifacts/line-1/wall-v21.png inside the
> current workspace if file output is supported; do not save additional image
> files.

The generated candidate altered surrounding pixels and was not retained as
the finished wall. Only the new frond pigment was admitted onto the same bare
upper-rock area using a local Node compositor. The original cave and every
ancestor mark remain intact. Exactly 2,028 pixels changed, within
x=721..815, y=218..306; zero pixels changed outside the addition rectangle.
The previously delivered Gathering PNG decoder and JPEG encoder served only
as build-time helpers. The Python tool needs no image library or installation.

## Chosen visual review

Opened the final full PNG and JPEG after compositing and independently
compared all final PNG pixels with the ancestor. The final wall is an opaque
1254 × 1254 RGB PNG; its preview is a 512 × 512 JPEG, 71,154 bytes.
[Image checks](image-checks41.json) record dimensions, format, hashes and
preservation results. The curled red-ochre frond and yellow-ochre leaves are
visible above the inherited arch paintings. The original Pepe figures,
rough rock, cracks, light and square framing remain unchanged. No writing,
logo, frame or prohibited symbol was observed. The small mark is faint at
preview size.

No hands or handprints were added. As previously recorded, the inherited
simplified frog hands do not resolve individual digits. Exact five-digit
anatomy cannot be certified without redrawing ancestors, so this inherited
unmet requirement is recorded explicitly. This is local visual inspection,
not independent visual certification.
