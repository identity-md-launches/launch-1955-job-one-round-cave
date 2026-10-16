#!/usr/bin/env python3
"""Explain co-occurring exact CSV value changes across selected columns."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

source = Path(__file__).resolve().parents[1] / 'csv-reconcile' / 'reconcile.py'
spec = importlib.util.spec_from_file_location('csv_joint_engine', source)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def joint_transitions(before, after, keys, columns, include_records=False):
    """Group complete selected tuples; never infer pairings for duplicate keys."""
    keys, columns = list(keys), list(columns)
    if not keys or len(set(keys)) != len(keys):
        raise engine.InputError('provide distinct key columns')
    if (not columns or len(set(columns)) != len(columns)
            or set(keys) & set(columns)):
        raise engine.InputError('select distinct non-key columns')
    bt = engine.load_table(before, keys)
    at = engine.load_table(after, keys)
    if not set(columns) <= set(bt[0]) & set(at[0]):
        raise engine.InputError('selected columns must exist in both inputs')
    comparison = engine.reconcile_tables(bt, at, keys)
    bg, ag = bt[1], at[1]
    groups = {}
    matched = changed = 0
    for key in sorted(bg.keys() & ag.keys()):
        b, a = bg[key], ag[key]
        if len(b) != 1 or len(a) != 1:
            continue
        matched += 1
        old = tuple(b[0]['values'][c] for c in columns)
        new = tuple(a[0]['values'][c] for c in columns)
        if old == new:
            continue
        changed += 1
        pair = (old, new)
        if pair not in groups:
            groups[pair] = {'before': dict(zip(columns, old)),
                            'after': dict(zip(columns, new)), 'rows': 0}
            if include_records:
                groups[pair]['records'] = []
        group = groups[pair]
        group['rows'] += 1
        if include_records:
            group['records'].append({'key': dict(zip(keys, key)),
                                     'before_record': b[0]['record'],
                                     'after_record': a[0]['record']})
    ordered = sorted(groups, key=lambda pair: (-groups[pair]['rows'], pair))
    return {'format': 'csv-joint-transitions/v1',
            'keys': keys, 'columns': columns,
            'equal': comparison['equal'], 'complete': comparison['complete'],
            'schema': comparison['schema'], 'summary': comparison['summary'],
            'selected': {'uniquely_matched_rows': matched,
                         'changed_rows': changed,
                         'unchanged_rows': matched - changed},
            'unpaired_records': {
                side: sum(len(g[side]) for g in comparison['ambiguous'])
                for side in ('before', 'after')},
            'transitions': [groups[pair] for pair in ordered]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--key', action='append', required=True)
    parser.add_argument('--column', action='append', required=True,
                        help='include this column in the joint tuple; repeat for more')
    parser.add_argument('--include-records', action='store_true',
                        help='include every participating key and logical record location')
    args = parser.parse_args(argv)
    try:
        result = joint_transitions(args.before, args.after, args.key,
                                   args.column, args.include_records)
    except (OSError, ValueError):
        print(json.dumps({'error': 'Check workspace-local UTF-8 CSVs, distinct keys and common non-key columns.'}),
              file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result['equal'] else 1


if __name__ == '__main__':
    sys.exit(main())
