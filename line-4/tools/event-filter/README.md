# Event Filter

Build `eth_getLogs` parameters from an event ABI and indexed values, using only
Python's standard library and this line's sibling tools. It encodes scalar
topics and hashes string, bytes, supported arrays and tuples using Solidity's
special indexed-event encoding. This fills the other side of Event Lens:
prepare a topic from a known value before searching for it.

From the repository root, Python 3.10+, no installation:

```sh
python3 -B line-4/tools/event-filter/event_filter.py --demo
```

Tried locally: exit 0; emits the known Transfer topic
`0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`,
the real ZTO emitter and two wildcard positions. The single historical block
`0x18fd343` comes from Transcript Inspector's retained totalSupply capture.
This is a proposed standard Transfer filter, not a verified deployed event ABI,
observed log or current balance. No network request is made.

The same filter from delivered files:

```sh
python3 -B line-4/tools/event-filter/event_filter.py --abi line-4/tools/event-lens/transfer-abi.json --event 'Transfer(address,address,uint256)' --spec line-4/tools/event-filter/zto-filter.json
```

To prepare a filter for your contract, supply your ABI, explicit emitter and
numeric block range. A spec contains exactly these four fields:

```json
{
  "emitter": "0xd782bdea4ef02a0bd391eb9089470c8080f0a68e",
  "fromBlock": "0x18fd343",
  "toBlock": "0x18fd343",
  "indexed": [null, null]
}
```

Each `indexed` item corresponds to one indexed input in ABI order, skipping
nonindexed inputs. Use `null` for any value, `{"value": ABI_VALUE}` for exact
matching, or `{"any": [ABI_VALUE, ...]}` for OR within that topic position.
Positions combine with AND. Array and tuple values are nested JSON arrays
inside the wrapper, so an array value cannot be confused with OR alternatives.
Wildcards remain in position. Nonindexed values cannot be filtered by topics.
Decimal integers may be JSON integers or exact decimal strings; bytes are
even-length `0x` hex; string values are UTF-8 text.

The output's `params` array is the parameter list for `eth_getLogs`; the outer
report is metadata, not a JSON-RPC envelope. A person may review and use those
parameters separately. This program has no network or sending capability.
No request ID, account, holder or recipient is invented.

`topic_value(parameter, value)` is the Python API. For example, the included
`label-abi.json` describes an explicitly synthetic string-indexed event. Its
`"abc"` value yields the known Keccak topic
`0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45`.
It has no deployed address; it is only an encoding fixture.

Encoding follows the [Solidity indexed-event specification](https://docs.soliditylang.org/en/latest/abi-spec.html#encoding-of-indexed-event-parameters):
top-level strings and bytes hash their raw contents; compound members are
padded to word boundaries and concatenated without lengths or offsets.
All arrays and tuples are hashed, including those occupying just one word.
This differs from both regular ABI encoding and general packed encoding.
Indexed encodings can be ambiguous. Tests demonstrate two different tuple
values with the same preimage, and thus the same topic. A match requires
reviewing ordinary log data; it cannot establish a unique source value.

Scope: scalar types, one-dimensional arrays of static scalars and nested tuples
supported by ABI Workbench. No nested arrays, tuple arrays, string/bytes arrays,
fixed point or function values. Anonymous events are explicitly refused because
they lack a signature topic. Event Lens can inspect those with an explicit ABI.
Overloads require a full signature; duplicate matching entries are refused.
The supplied ABI and emitter are not authenticated.

Bounds: 1 MiB per JSON input with duplicate-field refusal and resolved paths
inside the current workspace; inherited schema limits of 32 tuple levels,
4096 type nodes and 256 parameters. Arrays have at most 4096 items; OR has
1..32 alternatives. All encoded values across all alternatives share a 65536
byte preimage budget, charged before growing compound buffers. Blocks must be
canonical hex numeric quantities of at most 64 bits, with start <= end; no
moving tags. Numbers identify supplied heights, not canonical block hashes.
The path guard assumes trusted local files without concurrent replacement.
These limits are not precise CPU or memory guarantees.

Exit 0 produces a plan; exit 2 reports invalid input on stderr and no plan.
The tool reads only the explicit local inputs and sibling Python code. It does
not access environment values, keys or wallets, sign, pay, post or deploy.
Keep `event-lens` and `abi-workbench` beside this folder.

```sh
python3 -B -m unittest discover -s line-4/tools/event-filter -v
```

Local checks: 18 behavioral tests pass, covering independent scalar words,
known Keccak hashes, UTF-8 bytes, compound layouts, ambiguous preimages, topic
positions, OR semantics, malformed input, schema refusal, aggregate budgets,
overloads, CLI output/errors and the ZTO-first filter demonstration.
