# CSV Joint Transitions

Group co-occurring exact value changes across several columns of two keyed CSV
datasets. This helps a worker review migrations such as status **and** owner
changes together: separate per-column counts cannot reveal whether those edits
affected the same records. Python 3.9+ standard library only. Keep the sibling
`csv-reconcile/` directory with this tool; its bounded reader and comparison
engine are reused without modification. No installation or network is needed.

From the repository root, one command shows it working:

```sh
python3 -B line-2/tools/csv-joint-transitions/joint.py line-2/tools/csv-joint-transitions/demo-before.csv line-2/tools/csv-joint-transitions/demo-after.csv --key id --column status --column owner --include-records
```

When tried, it returned **1**, grouping two `pending/alpha` → `ready/beta`
records (keys `1`, `2`) and one `pending/beta` → `ready/alpha` record (key `3`).
The full comparison reported four changed rows, one addition and one removal.
The fourth changed row only edited `note`, so it did not enter the selected
transitions. The demonstration is synthetic; it is not a token or chain claim.

Repeat `--key` for composite identity and `--column` for the tuple's columns,
in the desired order. Every group contains complete `before` and `after`
objects for those columns, including components that stayed unchanged.
At least one selected component must change to enter a group. Exact tuple
identity determines groups; no concatenated separators or normalization are
used. Empty strings, case, whitespace, leading zeros and multiline values
remain literal. Groups sort by descending row count, then literal old and new
tuples in selected-column order. A record enters at most one joint group.

Only keys present exactly once on **both** sides contribute. Duplicate groups
never acquire inferred identities, even if their rows are identical. Additions,
removals and key edits do not create transitions. `unpaired_records` counts
occurrences in ambiguous groups on each side; additions and removals are
separately counted in the global `summary`. `selected` partitions uniquely
matched rows into changed and unchanged selected tuples. The complete global
schema and summary still cover all columns. Zero selected changes does not
establish equality. `complete` means absence of duplicate-key ambiguity; it
does not establish matching schemas or meaningful real-world identity.

The default JSON includes selected cell values and column names, without key
values or record locations. This is not anonymization. `--include-records`
adds **every** participating key and its before/after logical CSV record
numbers, sorted by literal composite key. It discloses keys as well as selected
cell values, with no sampling or truncation. The header is record 1; multiline
quoted records each count once. These are not physical line numbers.

Exit **0** means global equality, **1** means any global difference or ambiguity,
and **2** means invalid options or input. JSON is written to stdout only after
both captures and all validation succeed. Input failures emit a generic JSON
error on stderr with no partial report. JSON escapes Unicode and control
characters; argparse option errors can echo arguments. Inputs are never changed.

Inputs must be UTF-8 CSVs inside the current working directory, with unique
nonempty headers, consistent widths, at most 16 MiB and 100,000 data records
per side. Keys and selected columns must exist on both sides, be distinct in
their own lists, and not overlap. The two source files are each read once;
headers, comparison, grouping and traces share those captures. These are
sequential captures, not an atomic snapshot of a producer. Finish writing both
files before invoking the tool. The same path passed twice is read once per
side. Tables and full comparison are held in memory. There is no fuzzy matching,
network, transaction, payment or output-file write in this tool.

Checks:

```sh
python3 -B -m unittest discover -s line-2/tools/csv-joint-transitions -v
```

All **12 behavioral tests passed**: joint correlations, identical marginal
counts with different joint changes, unchanged components, global schema and
unrelated edits, additions/removals, duplicate refusal, composite keys,
multiline/reordered records, literal values and empty keys, ordering, invalid
options, capture consistency, statuses, complete traces and escaped controls.
The inherited engine's 19 tests and CSV Transitions' 17 tests also passed from
byte-identical scratch copies. An offline self-comparison of the retained real
ZTO-first/IMD-second six-row snapshot returned 0 with the full
`chain_id,token_address,field` key and `raw_value,block_number` tuple. That trial
establishes equality of saved inputs only; no current chain observation was made.
