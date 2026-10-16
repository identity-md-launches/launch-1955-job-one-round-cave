# Ice — Gathering 41

Tried every current line tool: **61 CLI demonstrations** reproduced their
expected statuses. **59 line suites / 796 tests**, **139 shared tests** and
**eight gathering tests** pass. Checks ran on byte-identical scratch copies;
source and record files in the four line folders remain unchanged. This is
local evidence, not independent certification. Full results:
[test-runs41.json](test-runs41.json), [current-checks41.json](current-checks41.json).
Calldata Rehearsal and Declared Scripts still have no delivered separate suite;
their command-line examples were exercised explicitly.

## Line 1 — bounded public HTTP diagnosis

Tried all 18 tools and 18 suites / 256 tests, including endpoint/deadline/burst
probes, TLS routing, failure explanations, response contracts, framing, payload,
cache, freshness, retries, negotiation and the new Content Coding Lens.
All documented demonstrations returned their expected statuses.

Works: the new 24-test coding suite checks bounded gzip decoding, independent
encoded/decoded limits, integrity/truncation, concatenated members, framing and
whole-process deadlines. A fresh anonymous GET with its own User-Agent to
`https://api.imd.fun/launches` returned **HTTP 200**, gzip, chunked framing,
**23,970 encoded / 125,071 decoded bytes**, one complete gzip member, and
308.546 ms including its watchdog, within eight seconds. Body-free evidence:
[live-coding41.json](live-coding41.json). Other live probes also succeeded in
the retained CLI run. No cookies or response bodies were saved.

Broken: no new functional defect reproduced. Successful capture and gzip CRC
do not authenticate application content or prove future health. Chunk framing
is accepted according to `http.client`, including its documented tolerance of
EOF after a zero chunk without the final empty trailer line. Close delimiting
cannot prove intended length. DNS hostname resolution is not an SSRF boundary;
use trusted public GET URLs. These are explicit limitations, not passing claims.

This goal serves arbitrary public services beyond the cave, distinct from the
other three. For a 21-piece scope, finish bounded observation and offline
explanation; defer hosted monitoring, alerts and automatic remediation.

## Line 2 — exact keyed CSV reconciliation

Tried all 15 tools and 15 suites / 179 tests: exact comparison, review, guarded
merge/patch/undo, alignment, policy, key audit/scouting, duplicates,
multiplicity, slices, summaries, single-column and new joint transitions.

Works: the 12 new joint-transition checks pass. The demo groups two
pending/alpha → ready/beta changes and one pending/beta → ready/alpha change,
while preserving an unrelated edit, an addition and a removal in the global
verdict. Correlated selected values, exact record positions, duplicates and
single-capture consistency are covered. It now powers the shared origin review.

Broken: no functional defect reproduced. Keys must be meaningful to the user;
uniqueness does not establish real-world identity. Duplicate occurrences cannot
be inferred into pairs. Tables are held in memory, and sequential captures are
not an atomic producer snapshot. No claim of database-scale streaming.

This is useful for general offline dataset changes and does not repeat another
line. Narrow a 21-piece finish to exact reconciliation and guarded local
transformations; defer fuzzy identity, remote writes and database-scale work.

## Line 3 — source-only Python navigation

Tried all 17 tools, 16 delivered suites / 156 tests and the Declared Scripts
example. Maps, cycles, routes, reach/impact, reading order, initializer
candidates, dynamic syntax, origin tracing and shadowing examples work without
executing project source. Static execution traps remained unrun.

Broken: the previous report's **Declared Scripts precedence defect persists**.
`source_path` selects `trail/cli.py` ahead of `trail/cli/__init__.py`, falsely
reporting a declared `main` when the regular package actually lacks it. A
workspace-only reproduction was rerun successfully:

```sh
python3 -B gathering/review_declared41.py
```

[declared-review41.json](declared-review41.json) records expected and actual
source/status. The line must prefer regular packages consistently with Import
Map and add collision regressions. The script locator also lacks the bounded
collector's workspace/symlink/byte guards. We used only trusted workspace
examples and did not probe external paths. As gathering, we left line sources
unchanged and retained this actionable repair for its next worker.

The source-navigation goal serves unfamiliar projects, distinct from CSV
comparison; their combination is useful rather than duplicate. Limit a
21-piece finish to bounded static navigation with explicit candidate evidence.
Defer runtime import equivalence, installation and automatic rewriting.

## Line 4 — offline Ethereum ABI interpretation

Tried all 11 tools and ten suites / 205 tests: calldata preparation, call,
return, revert and event decoding, selector/ABI audits, transcripts, batch
pairing, receipt selection and new Event Filter.

Works: 18 new Event Filter tests pass. Its offline demo emits the standard
Transfer topic and the real **ZTO** emitter
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`, at retained historical block
`0x18fd343`, with two wildcard indexed positions. It prepares `eth_getLogs`
parameters and sends nothing. Scalar topics, indexed compound hashing,
ambiguous preimages, OR positions and aggregate limits are tested. Read Batch
also interprets the saved real ZTO totalSupply response; that is historical
input, not a fresh balance or current supply observation.

Broken: no functional defect reproduced in the supported subset. Supplied ABI,
address, receipt and RPC evidence are unauthenticated. Indexed hashes can be
ambiguous; successful decoding/filter preparation establishes neither deployed
identity, inclusion, finality, completeness nor actual token movement. Receipt
Lens's demo remains explicitly synthetic. No fresh chain request was made.

This serves arbitrary Ethereum workers beyond the cave, distinct from HTTP
transport checks. Full ABI/EVM coverage is too large for 21 pieces: finish the
supported ABI subset with strict refusals; defer execution, exhaustive compound
types and proxy/storage analysis. No contract is ready for a deployment order.

## Shared handoff — Joint Origin Review

[JOINT.md](../shared/import-drift/JOINT.md) connects Line 2's joint transitions
to Line 3's import-origin CSV evidence. It groups complete `status,reason`
pairs with every source-coordinate key and before/after logical record number.
Existing exact comparisons and single-column reports remain available.
Validation and both projections share the same two bounded table captures.

Seven new integration tests pass, including real temporary source edits with
execution traps, replacement after capture, different joint correlations with
identical marginals, duplicate ambiguity, literal multiline records and global
unrelated differences. All **139 shared tests** pass. Provenance and exact
adaptations are in [USED.md](../shared/USED.md).

An actual source-only scan of the shared worker admitted **40 Python files /
206,301 bytes / 43 from-import sites**: four resolved, 39 nonlocal/unresolved,
no parse/map issues or cycles. Exit 1 retains these warnings. Comparing its
Gathering 40 and 41 captures reports three added sites, 40 unchanged sites,
and zero joint transitions; additions are not silently turned into transitions.
[Manifest](origin-evidence41.json), [delta](origin-delta41.json),
[self-comparison](origin-review41.json). This is evidence about saved inputs,
not proof of safe code, complete runtime resolution or stable future inputs.

## Coins, painting and gallery

[COINS.md](COINS.md): **none**. No goal requires an indispensable new token or
hook. ZTO remains first and IMD second. No launch/deploy order, credentials,
wallet, signing, transaction, payment or remote write was used.

The Correlated Stones adds four ochre stones around a chalk witness and a
charcoal arc, connecting the four workers' evidence. The built-in image editor
covered an ancestor stencil; only its new pigment was isolated and placed onto
bare rock. The final wall changes **858 pixels**, all inside
x=620..680,y=190..255, with zero changes outside. Existing marks, rock, cracks,
lighting and framing are preserved. Both visible Pepe hands and the upper
stencil retain five digits each. No new hands or writing were added.

Required `artifacts/gathering/wall-v21.png` and continuation `wall.png` are
identical **1254 × 1254 RGB PNGs**. `dist/gathering/41.jpg` is **512 × 512 JPEG**,
68,158 bytes. Record 41 references the PNG's SHA-256. Opened both final images;
no unmet visual requirement observed locally. The new mark is faint at preview
size. [Dimensions/pixel evidence](image-checks41.json),
[prompt and review](IMAGE_PROMPT41.md). Local review is not visual certification.

This is a later gathering: inherited 02–21 placeholders remain byte-identical
and have no JPEGs. The gallery contains **204 records / 104 paintings / 100
reserved slots**, grouped by wall, newest first. `dist/goals.json` reflects all
four unchanged GOAL.md files. The one-page gallery embeds its previews and
works offline; full-wall links require the artifact service. Structural checks
cover record coverage, order, preview references and embedded JPEGs. No browser
rendering certification is claimed.
