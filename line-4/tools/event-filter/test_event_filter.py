import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import event_filter as f


def p(t, **extra):
    return {'type': t, 'indexed': True, **extra}


def event(*params, **extra):
    return dict(type='event', name='E', inputs=list(params), **extra)


def spec(*indexed):
    return dict(emitter=f.events.ZTO, fromBlock='0x18fd343', toBlock='0x18fd343', indexed=list(indexed))


def word(n):
    return (n % (1 << 256)).to_bytes(32, 'big')


class EventFilterTests(unittest.TestCase):
    def test_zto_demo_known_topic(self):
        out = f.demo()
        self.assertEqual(out['params'][0], dict(address=f.events.ZTO,
            fromBlock='0x18fd343', toBlock='0x18fd343', topics=[
            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef', None, None]))
        self.assertIn('no log queried', out['fixture'])

    def test_scalar_words_independent(self):
        for typ, value, raw in [('int8', -3, word(-3)), ('uint', 7, word(7)),
                ('bool', True, word(1)), ('bytes2', '0x1234', b'\x12\x34'+b'\0'*30),
                ('address', f.events.ZTO, b'\0'*12+bytes.fromhex(f.events.ZTO[2:]))]:
            with self.subTest(typ=typ):
                out = f.topic_value(p(typ), value)
                self.assertEqual(out['topic'], '0x'+raw.hex())
                self.assertEqual(out['encoding'], 'topic_word')

    def test_known_keccak_abc_string_and_bytes(self):
        expected = '0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45'
        for typ, value in [('string', 'abc'), ('bytes', '0x616263')]:
            out = f.topic_value(p(typ), value)
            self.assertEqual(out['topic'], expected)
            self.assertEqual(out['preimage_bytes'], 3)
        self.assertEqual(f.topic_value(p('string'), '')['topic'],
            '0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')

    def test_utf8_preimage(self):
        self.assertEqual(f._preimage(p('string'), 'é🐸', [0]), bytes.fromhex('c3a9f09f90b8'))

    def test_scalar_arrays_have_no_length_word(self):
        for typ in ['uint8[]', 'uint8[2]']:
            param = p(typ)
            raw = word(2) + word(7)
            self.assertEqual(f._preimage(param, [2, 7], [0]), raw)
            self.assertEqual(f.topic_value(param, [2,7])['topic'], '0x'+f.abi.keccak256(raw).hex())
        self.assertEqual(f._preimage(p('int8[]'), [-1], [0]), b'\xff'*32)
        self.assertEqual(f._preimage(p('bytes2[1]'), ['0x1234'], [0]), b'\x12\x34'+b'\0'*30)

    def test_single_word_arrays_and_tuples_are_hashed(self):
        for param in [p('uint8[1]'), p('tuple', components=[{'type':'uint8'}])]:
            out = f.topic_value(param, [7])
            self.assertEqual(out['encoding'], 'indexed_hash')
            self.assertNotEqual(out['topic'], '0x'+word(7).hex())

    def test_tuple_nested_padding_without_offsets_or_lengths(self):
        param = p('tuple', components=[{'type':'string'}, {'type':'tuple', 'components':[
            {'type':'bytes'}, {'type':'int8'}]}, {'type':'uint8[]'}])
        raw = b'abc'+b'\0'*29 + b'\x12'+b'\0'*31 + word(-2) + word(3)+word(4)
        self.assertEqual(f._preimage(param, ['abc', ['0x12', -2], [3,4]], [0]), raw)
        self.assertEqual(f.topic_value(param, ['abc', ['0x12', -2], [3,4]])['preimage_bytes'], 160)

    def test_ambiguous_tuple_preimages_are_not_unique_proof(self):
        param = p('tuple', components=[{'type':'uint8[]'}, {'type':'uint8[]'}])
        self.assertEqual(f.topic_value(param, [[1],[2,3]])['topic'],
                         f.topic_value(param, [[1,2],[3]])['topic'])
        self.assertIn('do not prove a unique', f.NOTICE)

    def test_constraint_positions_skip_nonindexed_and_keep_nulls(self):
        e = event(p('uint8', indexed=False), p('string', name='label'), p('uint8'))
        out = f.prepare([e], 'E', spec(None, {'value': 4}))
        self.assertEqual([r['position'] for r in out['indexed']], [1,2])
        self.assertEqual([r['topic_position'] for r in out['indexed']], [1,2])
        self.assertIsNone(out['params'][0]['topics'][1])
        self.assertEqual(out['params'][0]['topics'][2], '0x'+word(4).hex())

    def test_any_is_or_and_array_values_are_unambiguous(self):
        out = f.prepare([event(p('uint8[]'))], 'E', spec({'any': [[1,2], []]}))
        self.assertEqual(len(out['params'][0]['topics'][1]), 2)
        self.assertEqual(out['indexed'][0]['alternatives'][1]['preimage_bytes'], 0)
        out = f.prepare([event(p('uint8[]'))], 'E', spec({'value': [1,2]}))
        self.assertIsInstance(out['params'][0]['topics'][1], str)

    def test_overload_aliases_and_duplicates(self):
        a, b = event(p('uint')), event(p('bool'))
        out = f.prepare([a,b], 'E(uint)', spec({'value': 1}))
        self.assertEqual(out['signature'], 'E(uint256)')
        for entries, ref in [([a,b],'E'), ([a,a],'E(uint256)')]:
            with self.assertRaises(ValueError):
                f.prepare(entries, ref, spec(None))

    def test_refuse_anonymous_and_bad_schemas(self):
        for e in [event(p('uint'), anonymous=True), event(p('bytes[]')),
                  event(p('uint', indexed=1)), event(*(p('uint') for _ in range(4)))]:
            with self.assertRaises(ValueError):
                f.prepare([e], 'E', spec(None))

    def test_bad_values_refused_even_inside_or(self):
        for typ, value in [('uint8',256), ('int8',-129), ('bool',1), ('address','0x12'),
                ('bytes2','0x123'), ('bytes','0xzz'), ('string',3), ('uint8[]',[True]),
                ('uint8[2]',[1]), ('uint8[]',[1]*4097)]:
            with self.subTest(typ=typ), self.assertRaises(ValueError):
                f.prepare([event(p(typ))], 'E', spec({'any':[value]}))
        with self.assertRaises(ValueError):
            f.topic_value(p('tuple', components=[{'type':'uint'}]), [])

    def test_bad_constraints(self):
        for constraint in [{}, {'hash':'0x12'}, {'value':1,'any':[1]}, [],
                           {'any':[]}, {'any':[1]*33}, {'any':None}, {'any':[None]}]:
            with self.subTest(constraint=constraint), self.assertRaises(ValueError):
                f.prepare([event(p('uint'))], 'E', spec(constraint))
        for constraints in [[], [None,None], None, {}]:
            s = spec()
            s['indexed'] = constraints
            with self.assertRaises(ValueError):
                f.prepare([event(p('uint'))], 'E', s)

    def test_block_and_emitter_validation(self):
        for key, value in [('fromBlock','latest'), ('fromBlock','0x00'), ('toBlock','0x'),
                           ('fromBlock',True), ('toBlock','0x10000000000000000'),
                           ('emitter','0x12'), ('emitter',None), ('toBlock','0x1')]:
            s = spec(None)
            s[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                f.prepare([event(p('uint'))], 'E', s)
        for s in [None, {}, dict(spec(), extra=True)]:
            with self.assertRaises(ValueError):
                f.prepare([event()], 'E', s)

    def test_budget_exact_and_aggregate_or(self):
        with patch.object(f, 'MAX_PREIMAGE_BYTES', 64):
            self.assertEqual(f.topic_value(p('bytes'), '0x'+'ab'*64)['preimage_bytes'], 64)
            for param, value in [(p('bytes'), '0x'+'ab'*65), (p('string'), 'é'*33),
                                 (p('uint8[]'),[1,2,3])]:
                with self.assertRaises(ValueError):
                    f.topic_value(param, value)
            with self.assertRaises(ValueError):
                f.prepare([event(p('uint8'))], 'E', spec({'any':[1,2,3]}))
            with self.assertRaises(ValueError):
                f.prepare([event(p('uint8'),p('uint8'),p('uint8'))], 'E',
                          spec({'value':1},{'value':2},{'value':3}))

    def test_no_indexed_parameters(self):
        out = f.prepare([event(p('uint', indexed=False))], 'E', spec())
        self.assertEqual(len(out['params'][0]['topics']), 1)

    def test_reader_cli_and_error_contract(self):
        with tempfile.TemporaryDirectory(dir='test/scratch') as tmp:
            root = Path(tmp)
            a, s = root/'abi.json', root/'spec.json'
            a.write_text(json.dumps([event(p('string'))]))
            s.write_text(json.dumps(spec({'value':'abc'})))
            args = ['event-filter','--abi',str(a),'--event','E(string)','--spec',str(s)]
            out, err = io.StringIO(), io.StringIO()
            with patch('sys.argv', args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(f.main(), 0)
            self.assertEqual(json.loads(out.getvalue())['indexed'][0]['alternatives'][0]['preimage_bytes'], 3)
            for raw in ['{}', '{"indexed":[],"indexed":[]}', 'x', '{"bad":"\\ud800"}']:
                s.write_text(raw)
                out, err = io.StringIO(), io.StringIO()
                with patch('sys.argv',args), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    self.assertEqual(f.main(), 2)
                self.assertEqual(out.getvalue(), '')
                self.assertNotIn('Traceback', err.getvalue())
        with self.assertRaises(ValueError):
            f.events.read_json(Path.cwd().parent/'not-opened.json')
        with patch('sys.argv',['event-filter','--demo','--event','E']), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(f.main(), 2)


if __name__ == '__main__':
    unittest.main()
