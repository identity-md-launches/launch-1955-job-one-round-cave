"""Behavioral integration checks for correlated source-origin changes."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import joint_transitions as joint
import origin_csv as origin
import reconcile


class JointReviewTests(unittest.TestCase):
    def setUp(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='test/scratch')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, name, text):
        p = self.root / name
        p.write_text(text, encoding='utf-8')
        return p

    def test_identical_marginals_keep_different_correlations(self):
        before = self.save('b.csv', 'id,status,reason\n1,a,x\n2,a,x\n')
        after = self.save('a.csv', 'id,status,reason\n1,b,y\n2,c,z\n')
        other = self.save('c.csv', 'id,status,reason\n1,b,z\n2,c,y\n')
        a = joint.joint_transitions(before, after, ['id'], ['status','reason'])
        b = joint.joint_transitions(before, other, ['id'], ['status','reason'])
        self.assertNotEqual(a['transitions'], b['transitions'])
        self.assertEqual(a['selected']['changed_rows'], 2)

    def test_duplicate_keys_never_pair(self):
        before = self.save('b.csv','id,status,reason\n1,a,x\n1,a,x\n')
        after = self.save('a.csv','id,status,reason\n1,b,y\n')
        r = joint.joint_transitions(before,after,['id'],['status','reason'],True)
        self.assertEqual(r['transitions'], [])
        self.assertFalse(r['complete'])
        self.assertEqual(r['unpaired_records'], {'before':2,'after':1})

    def test_unrelated_changes_keep_global_difference(self):
        before=self.save('b.csv','id,status,reason,note\n1,a,x,old\n2,a,x,removed\n')
        after=self.save('a.csv','id,status,reason,note\n1,a,x,new\n3,a,x,added\n')
        r=joint.joint_transitions(before,after,['id'],['status','reason'])
        self.assertFalse(r['equal'])
        self.assertEqual(r['selected']['changed_rows'],0)
        self.assertEqual((r['summary']['added'],r['summary']['removed'],r['summary']['changed']),(1,1,1))

    def snapshots(self):
        source=self.root/'src';source.mkdir()
        (source/'app.py').write_text('raise RuntimeError("never execute")\nfrom impl import run\n')
        impl=source/'impl.py';impl.write_text('other=1\n')
        before,_=origin.snapshot(source)
        impl.write_text('def run(): pass\n')
        after,_=origin.snapshot(source)
        return self.save('b.csv',before),self.save('a.csv',after)

    def test_real_source_edit_groups_status_and_reason_with_trace(self):
        before,after=self.snapshots()
        r=origin.compare(before,after)
        g=r['joint_transitions']['transitions'][0]
        self.assertEqual(g['before']['status'],'unresolved')
        self.assertEqual(g['after']['status'],'resolved')
        self.assertNotEqual(g['before']['reason'],g['after']['reason'])
        self.assertEqual(g['records'],[{'key':{'path':'app.py','line':'2','site_index':'0'},'before_record':2,'after_record':2}])
        self.assertEqual(r['joint_transitions']['summary'],r['comparison']['summary'])

    def test_comparison_uses_exactly_two_captures_even_after_replacement(self):
        before,after=self.snapshots()
        original=reconcile.load_table
        calls=[]
        def replace(path,keys):
            result=original(path,keys);calls.append(str(path))
            Path(path).write_text('invalid replacement\n')
            return result
        with patch.object(reconcile,'load_table',side_effect=replace):
            r=origin.compare(before,after)
        self.assertEqual(len(calls),2)
        self.assertEqual(r['comparison']['summary']['changed'],1)
        self.assertEqual(r['joint_transitions']['selected']['changed_rows'],1)

    def test_literal_tuples_and_multiline_record_locations(self):
        before=self.save('b.csv','id,status,reason\n1,"a|b","x\ny"\n2,a,"b|x\ny"\n')
        after=self.save('a.csv','id,status,reason\n2,z,q\n1,z,q\n')
        r=joint.joint_transitions(before,after,['id'],['status','reason'],True)
        self.assertEqual(len(r['transitions']),2)
        records=[g['records'][0] for g in r['transitions']]
        self.assertIn({'key':{'id':'1'},'before_record':2,'after_record':3},records)

    def test_invalid_selected_columns_refused(self):
        p=self.save('a.csv','id,status\n1,a\n')
        for columns in ([],['id'],['status','status'],['missing']):
            with self.assertRaises(ValueError):
                joint.joint_transitions(p,p,['id'],columns)


if __name__=='__main__':
    unittest.main()
