import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('joint_tool', Path(__file__).with_name('joint.py'))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class JointTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def write(self, name, rows):
        path = self.root / name
        with path.open('w', encoding='utf-8', newline='') as stream:
            csv.writer(stream).writerows(rows)
        return path

    def compare(self, b, a, columns=('status', 'owner'), keys=('id',), trace=False):
        return tool.joint_transitions(self.write('b.csv', b), self.write('a.csv', a),
                                      keys, columns, trace)

    def test_joint_groups_preserve_correlations_and_counts(self):
        h = ['id', 'status', 'owner']
        r = self.compare([h, ['private1','pending','a'], ['private2','pending','a'], ['private3','pending','b']],
                         [h, ['private1','ready','b'], ['private2','ready','b'], ['private3','ready','a']])
        self.assertEqual(r['transitions'], [
            {'before':{'status':'pending','owner':'a'}, 'after':{'status':'ready','owner':'b'}, 'rows':2},
            {'before':{'status':'pending','owner':'b'}, 'after':{'status':'ready','owner':'a'}, 'rows':1}])
        self.assertEqual(r['selected']['changed_rows'], 3)
        self.assertNotIn('private', json.dumps(r))

    def test_unchanged_tuple_components_are_retained(self):
        h = ['id','status','owner']
        r = self.compare([h,['1','old','same']], [h,['1','new','same']])
        self.assertEqual(r['transitions'][0]['before']['owner'], 'same')
        self.assertEqual(r['transitions'][0]['after']['owner'], 'same')

    def test_same_marginals_can_have_different_joint_groups(self):
        h = ['id','status','owner']
        before = [h,['1','old','a'],['2','old','a']]
        first = self.compare(before, [h,['1','new','a'],['2','old','b']])
        second = self.compare(before, [h,['1','new','b'],['2','old','a']])
        self.assertEqual(first['selected']['changed_rows'], 2)
        self.assertEqual(second['selected']['changed_rows'], 1)
        self.assertNotEqual(first['transitions'], second['transitions'])

    def test_unrelated_edits_schema_add_remove_keep_global_verdict(self):
        r = self.compare([['id','v','other'],['a','same','x'],['gone','x','x']],
                         [['id','v','other','new'],['a','same','y','z'],['added','z','z','z']], ('v',))
        self.assertEqual(r['transitions'], [])
        self.assertEqual(r['selected'], {'uniquely_matched_rows':1,'changed_rows':0,'unchanged_rows':1})
        self.assertEqual((r['summary']['added'],r['summary']['removed'],r['summary']['changed']), (1,1,1))
        self.assertEqual(r['schema']['added_columns'], ['new'])
        self.assertFalse(r['equal'])

    def test_duplicate_keys_never_pair_even_if_copies_equal(self):
        h = ['id','v']
        r = self.compare([h,['dup','a'],['dup','a'],['ok','a']],
                         [h,['dup','b'],['ok','b'],['ok','b']], ('v',), trace=True)
        self.assertFalse(r['complete'])
        self.assertEqual(r['transitions'], [])
        self.assertEqual(r['unpaired_records'], {'before':3,'after':3})
        self.assertEqual(r['selected']['uniquely_matched_rows'], 0)

    def test_composite_trace_reorder_multiline_and_literal_values(self):
        r = self.compare([['id','part','v','w'],['b','1','01','a\nb'],['a','2','','a\nb']],
                         [['w','v','part','id'],['a\nb ','1','2','a'],['a\nb ','1','1','b']],
                         ('v','w'), ('id','part'), True)
        self.assertEqual(r['transitions'][0]['before'], {'v':'','w':'a\nb'})
        self.assertEqual(r['transitions'][0]['records'], [
            {'key':{'id':'a','part':'2'},'before_record':3,'after_record':2}])
        self.assertEqual(r['transitions'][1]['records'][0]['after_record'], 3)

    def test_empty_key_is_literal_and_header_only_equal(self):
        r = self.compare([['id','v'],['','']], [['id','v'],['','x']], ('v',))
        self.assertTrue(r['complete'])
        self.assertEqual(r['transitions'][0]['before'], {'v':''})
        empty = self.compare([['id','v']], [['v','id']], ('v',))
        self.assertTrue(empty['equal'])
        self.assertEqual(empty['transitions'], [])

    def test_tie_sort_follows_selected_column_order(self):
        h = ['id','v','w']
        b, a = [h,['1','b','a'],['2','a','z']], [h,['1','x','x'],['2','x','x']]
        r = self.compare(b, a, ('w','v'))
        self.assertEqual(r['columns'], ['w','v'])
        self.assertEqual(r['transitions'][0]['before'], {'w':'a','v':'b'})

    def test_invalid_options(self):
        b = self.write('b.csv', [['id','v'],['x','old']])
        for keys, cols in [((),('v',)), (('id','id'),('v',)), (('id',),()),
                           (('id',),('v','v')), (('id',),('id',)), (('id',),('missing',))]:
            with self.subTest(keys=keys, columns=cols), self.assertRaises(ValueError):
                tool.joint_transitions(b,b,keys,cols)

    def test_capture_once_per_side_without_late_reopen(self):
        b = self.write('b.csv', [['id','v'],['x','old']])
        a = self.write('a.csv', [['id','v'],['x','new']])
        original = tool.engine.load_table
        def replace(path, keys):
            table = original(path, keys)
            path.write_text('id,other\nx,replaced\n', encoding='utf-8')
            return table
        with patch.object(tool.engine,'load_table',side_effect=replace) as read:
            r = tool.joint_transitions(b,a,('id',),('v',),True)
        self.assertEqual(read.call_count, 2)
        self.assertEqual(r['transitions'][0]['before'], {'v':'old'})
        self.assertEqual(r['transitions'][0]['after'], {'v':'new'})

    def test_cli_statuses_escaped_controls_and_no_partial_error(self):
        b = self.write('b.csv', [['id','v'],['\x1bkey','old']])
        a = self.write('a.csv', [['id','v'],['\x1bkey','\x1bvalue']])
        bad = self.write('bad.csv', [['id','v'],['short']])
        for candidate, status in [(b,0),(a,1),(bad,2),(self.root/'absent',2)]:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = tool.main([str(b),str(candidate),'--key','id','--column','v','--include-records'])
            self.assertEqual(code,status)
            self.assertNotIn('\x1b', out.getvalue()+err.getvalue())
            if status == 2:
                self.assertEqual(out.getvalue(), '')
                self.assertIn('error', json.loads(err.getvalue()))
            else:
                r = json.loads(out.getvalue())
                self.assertEqual(r['equal'], status == 0)

    def test_trace_counts_and_default_compatibility(self):
        h = ['id','v']
        b, a = [h,['b','a'],['a','a']], [h,['a','b'],['b','b']]
        traced = self.compare(b,a,('v',),trace=True)
        group = traced['transitions'][0]
        self.assertEqual(group['rows'], len(group['records']))
        self.assertEqual([m['key']['id'] for m in group['records']], ['a','b'])
        del group['records']
        self.assertEqual(traced, self.compare(b,a,('v',)))


if __name__ == '__main__':
    unittest.main()
