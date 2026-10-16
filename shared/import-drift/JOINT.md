# Joint Origin Review

Review status **and reason** changes as one tuple in static Python import
origin evidence. Separate per-column totals can hide whether two changes
happened to the same import. This joins Line 2's CSV Joint Transitions to
Line 3's source-only origin snapshots. Python 3.10+ standard library only;
keep this folder together. No installation or network is required.

One command using retained scans of the actual shared worker:

```sh
python3 -B shared/import-drift/origin_csv.py compare shared/import-drift/observed-origins40.csv shared/import-drift/observed-origins41.csv
```

Tried: exit **1**, three added import sites, 40 unchanged sites, no status/reason
transitions. Additions remain visible even though there are zero transitions.
These saved inputs are real source observations; equality or a lack of joint
changes does not establish that the source is safe or executes successfully.
`gathering/origin-delta41.json` retains the complete exact comparison.

`origin_csv.py compare` retains its previous comparison and single-column
status report. Its additional `joint_transitions` field groups complete
`status,reason` tuples, retaining unchanged components and every participating
key and logical CSV record location. Validation and both projections use the
same two bounded captures. Neither file is reopened for the joint projection.
Each uniquely matched row contributes to at most one group. Duplicate keys
cannot establish pairings; the general joint tool reports them as ambiguous.
Origin CSV's stricter schema refuses duplicate coordinate keys outright.

The general-purpose interface is also available:

```sh
python3 -B shared/import-drift/joint_transitions.py line-2/tools/csv-joint-transitions/demo-before.csv line-2/tools/csv-joint-transitions/demo-after.csv --key id --column status --column owner --include-records
```

This explicitly synthetic migration example returns **1** and groups two rows
moving together from pending/alpha to ready/beta, plus one moving from
pending/beta to ready/alpha. It preserves the unrelated note edit, addition and
removal in the global comparison. It does not represent chain data.

Input and exit contracts come from the reused CSV tool: workspace-local UTF-8,
16 MiB and 100,000 data rows per input, exact strings, unique nonempty headers,
consistent widths; 0 globally equal, 1 differences or ambiguity, 2 invalid
input. Coordinates (`path,line,site_index`) are source locations, not semantic
identities: inserting a line can appear as additions/removals. Static tracing
cannot resolve arbitrary dynamic code, runtime rebinding, caches or loaders.
The snapshots are sequential, not atomic; finish producer writes first.
Output includes selected values and, for origin review, full coordinates.

Checks:

```sh
python3 -B -m unittest discover -s shared/import-drift -p test_joint_review.py -v
```

Seven new tests pass: different correlations with identical marginal values,
duplicate ambiguity, global unrelated edits, real temporary source edits with
execution traps, replacement after capture, literal/multiline trace locations,
and invalid selections. All existing shared checks also pass (139 in total).
The temporary source edit test observes unresolved → resolved and its coupled
reason change without executing the project. The replacement test verifies
exactly two reads and consistent global and joint summaries.

Provenance: `joint_transitions.py` derives from
`line-2/tools/csv-joint-transitions/joint.py`, changing its sibling engine loader
and extracting a trusted-table API. That internal API accepts only tables
returned by `reconcile.load_table` using the same keys; it is not an arbitrary
JSON validation interface. `origin_csv.py` uses that API after validating its
captured tables. No line files were changed.
