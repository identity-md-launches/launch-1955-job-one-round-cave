#!/usr/bin/env python3
"""Prepare event topic filters from ABI values offline; never sends requests."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'event-lens' / 'event_lens.py'
loader = importlib.util.spec_from_file_location('filter_event_lens', SOURCE)
events = importlib.util.module_from_spec(loader)
loader.loader.exec_module(events)
abi = events.abi
MAX_PREIMAGE_BYTES = 65536
MAX_ALTERNATIVES = 32
NOTICE = ('Prepared offline; nothing sent. Supplied ABI and emitter are not authenticated. '
          'Indexed hashes do not prove a unique original value. Recheck returned log data '
          'and emitter; no inclusion, finality, completeness or token movement is verified.')


def charge(budget, size):
    if budget[0] + size > MAX_PREIMAGE_BYTES:
        raise ValueError('indexed values exceed the aggregate 65536-byte preimage budget')
    budget[0] += size


def _preimage(param, value, budget, nested=False):
    """Solidity indexed-event encoding, not abi.encode or abi.encodePacked."""
    t = abi._canonical(param)  # Public entry points admit the whole schema first.
    if param['type'] == 'tuple':
        components = param['components']
        if not isinstance(value, list) or len(value) != len(components):
            raise ValueError('indexed tuple requires one JSON array item per component')
        out = bytearray()
        for p, v in zip(components, value):
            out.extend(_preimage(p, v, budget, True))
        return bytes(out)
    parts = abi.array_parts(t)
    if parts:
        base, count = parts
        if not isinstance(value, list) or len(value) > abi.MAX_ARRAY_ITEMS:
            raise ValueError('indexed array must be a JSON array of at most 4096 items')
        if count is not None and len(value) != count:
            raise ValueError(f'{t} requires exactly {count} items')
        out = bytearray()
        for item in value:
            out.extend(_preimage({'type': base}, item, budget, True))
        return bytes(out)  # No length word, including dynamic arrays.
    if t in ('string', 'bytes'):
        if not isinstance(value, str):
            raise ValueError(f'indexed {t} value must be a string')
        # Refuse oversized text before UTF-8/hex allocation.
        if len(value) > 2 + 2 * MAX_PREIMAGE_BYTES:
            raise ValueError('indexed value exceeds the preimage budget')
        if t == 'string':
            raw = value.encode('utf-8')
        else:
            if not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value):
                raise ValueError('indexed bytes must be even-length 0x hex')
            raw = bytes.fromhex(value[2:])
        padding = (-len(raw)) % 32 if nested else 0
        charge(budget, len(raw) + padding)
        return raw + b'\0' * padding
    charge(budget, 32)
    return abi.encode_value(param, value)


def topic_value(param, value, budget=None):
    """Return one 32-byte topic plus encoding metadata for a supplied ABI value."""
    t = abi.canonical(param)
    budget = [0] if budget is None else budget
    raw = _preimage(param, value, budget)
    hashed = param['type'] == 'tuple' or '[' in t or t in ('bytes', 'string')
    topic = abi.keccak256(raw) if hashed else raw
    return {'topic': '0x' + topic.hex(),
            'encoding': 'indexed_hash' if hashed else 'topic_word',
            'preimage_bytes': len(raw)}


def emitter_address(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', value):
        raise ValueError('emitter must be a 20-byte 0x address')
    return value.lower()


def block_number(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,15})', value):
        raise ValueError('blocks must be canonical 0x quantities of at most 64 bits; no tags')
    return int(value, 16)


def prepare(entries, reference, spec):
    if not isinstance(spec, dict) or set(spec) != {'emitter', 'fromBlock', 'toBlock', 'indexed'}:
        raise ValueError('spec requires exactly emitter, fromBlock, toBlock and indexed')
    emitter = emitter_address(spec['emitter'])
    start, end = block_number(spec['fromBlock']), block_number(spec['toBlock'])
    if start > end:
        raise ValueError('fromBlock must not exceed toBlock')
    entry = events.select_event(entries, reference)
    signature, anonymous = events.event_schema(entry)
    if anonymous:
        raise ValueError('anonymous events have no signature topic; use Event Lens on explicit logs')
    indexed = [(i, p) for i, p in enumerate(entry.get('inputs', [])) if p['indexed']]
    constraints = spec['indexed']
    if not isinstance(constraints, list) or len(constraints) != len(indexed):
        raise ValueError('indexed requires exactly one constraint per indexed parameter, in ABI order')
    topics = ['0x' + abi.keccak256(signature.encode('ascii')).hex()]
    rows, budget = [], [0]
    for (position, param), constraint in zip(indexed, constraints):
        row = {'position': position, 'name': param.get('name') or f'arg{position}',
               'type': abi.canonical(param), 'topic_position': len(topics)}
        if constraint is None:
            topics.append(None)
            row['mode'] = 'wildcard'
        else:
            if not isinstance(constraint, dict) or len(constraint) != 1:
                raise ValueError('constraint must be null, {"value": ABI_VALUE} or {"any": [ABI_VALUE, ...]}')
            if 'value' in constraint:
                encoded = [topic_value(param, constraint['value'], budget)]
                topics.append(encoded[0]['topic'])
                row['mode'] = 'value'
            elif 'any' in constraint:
                choices = constraint['any']
                if not isinstance(choices, list) or not 1 <= len(choices) <= MAX_ALTERNATIVES:
                    raise ValueError('any requires 1..32 alternatives')
                encoded = [topic_value(param, v, budget) for v in choices]
                topics.append([e['topic'] for e in encoded])
                row['mode'] = 'any'
            else:
                raise ValueError('unknown indexed constraint key')
            row['alternatives'] = encoded
        rows.append(row)
    # Keep null positions: removing them would move later constraints.
    log_filter = {'address': emitter, 'fromBlock': hex(start), 'toBlock': hex(end), 'topics': topics}
    return {'schema': 'event-filter/v1', 'signature': signature,
            'method': 'eth_getLogs', 'params': [log_filter], 'indexed': rows,
            'preimage_bytes_total': budget[0], 'notice': NOTICE}


def demo():
    # Real ZTO target and a retained historical block, without claiming a log exists.
    result = prepare([events.TRANSFER], 'Transfer(address,address,uint256)',
                     {'emitter': events.ZTO, 'fromBlock': '0x18fd343',
                      'toBlock': '0x18fd343', 'indexed': [None, None]})
    result['fixture'] = ('Proposed ZTO Transfer filter at the retained totalSupply capture block. '
                         'Standard event ABI assumption; no log queried or observed.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--abi')
    parser.add_argument('--event')
    parser.add_argument('--spec')
    args = parser.parse_args()
    try:
        if args.demo:
            if any((args.abi, args.event, args.spec)):
                raise ValueError('--demo cannot be combined with other arguments')
            result = demo()
        else:
            if not all((args.abi, args.event, args.spec)):
                raise ValueError('provide --abi, --event and --spec, or --demo')
            result = prepare(events.read_json(args.abi), args.event, events.read_json(args.spec))
    except (ValueError, OSError, RecursionError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
