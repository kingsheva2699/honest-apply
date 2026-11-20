import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('career',ROOT/'scripts/career.py')
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

def fixtures():
    p={'schema_version':1,'facts':[{'id':'f1','statement':'Performed task A in a training exercise.','source':'Synthetic test statement','confirmed':True,'category':'skill'}],'preferences':[]}
    j={'id':'j1','company':'Synthetic employer','title':'Synthetic role','source':'Synthetic fixture, not a real opening','checked_at':'2026-01-01T00:00:00Z','requirements':[{'id':'r1','text':'Task A familiarity','kind':'required','status':'supported','fact_ids':['f1'],'rationale':'Synthetic mapping for test only','reviewed':True}],'preference_matches':[]}
    s={'job_id':'j1','user_selected':True,'reviewed_issues':[],'resume_fact_ids':['f1'],'letter_fact_ids':['f1']}
    return p,j,s

class CareerTests(unittest.TestCase):
    def test_setup_doc_contains_data_not_workflow(self):
        p,j,s=fixtures(); out=c.setup_doc(p)
        self.assertIn(p['facts'][0]['statement'],out)
        self.assertNotIn('python',out); self.assertNotIn('SKILL.md',out)
        self.assertNotIn('submit',out.lower())
    def test_setup_doc_preserves_unknown(self):
        p,j,s=fixtures(); p['facts'][0]['confirmed']=False
        out=c.setup_doc(p)
        self.assertIn('No confirmed facts recorded.',out)
        self.assertIn(p['facts'][0]['statement'],out.split('## Unconfirmed')[1])
    def test_setup_cli_export(self):
        with tempfile.TemporaryDirectory() as d:
            p,j,s=fixtures(); base=Path(d); (base/'p.json').write_text(json.dumps(p))
            r=subprocess.run([sys.executable,str(ROOT/'scripts/career.py'),'setup-doc','--profile',str(base/'p.json'),'--out',str(base/'setup')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads((base/'setup/my-career-data.json').read_text()),p)
            self.assertEqual(len(list((base/'setup').iterdir())),2)
    def test_supported(self):
        p,j,s=fixtures(); self.assertEqual(c.assess(p,j)['status'],'ready_for_user_review')
    def test_missing_is_unknown(self):
        p,j,s=fixtures(); j['requirements'][0].update(status='unknown',fact_ids=[])
        self.assertEqual(c.assess(p,j)['required_unknowns'],['r1'])
    def test_missing_not_gap(self):
        p,j,s=fixtures(); j['requirements'][0].update(status='gap',fact_ids=[])
        with self.assertRaises(c.Invalid): c.assess(p,j)
    def test_false_confirmation(self):
        p,j,s=fixtures(); p['facts'][0]['confirmed']=False
        self.assertEqual(c.assess(p,j)['required_unknowns'],['r1'])
        with self.assertRaises(c.Invalid): c.prepare(p,j,s)
    def test_string_confirmation_rejected(self):
        p,j,s=fixtures(); p['facts'][0]['confirmed']='true'
        with self.assertRaises(c.Invalid): c.assess(p,j)
    def test_unreviewed_mapping(self):
        p,j,s=fixtures(); j['requirements'][0]['reviewed']=False
        self.assertEqual(c.assess(p,j)['required_unknowns'],['r1'])
    def test_missing_reference(self):
        p,j,s=fixtures(); j['requirements'][0]['fact_ids']=['absent']
        with self.assertRaises(c.Invalid): c.assess(p,j)
    def test_duplicate_ids(self):
        p,j,s=fixtures(); p['facts'].append(copy.deepcopy(p['facts'][0]))
        with self.assertRaises(c.Invalid): c.assess(p,j)
    def test_extra_demographics_field(self):
        p,j,s=fixtures(); p['religion']='not permitted'
        with self.assertRaises(c.Invalid): c.assess(p,j)
    def test_unknowns_block_until_review(self):
        p,j,s=fixtures(); j['requirements'][0].update(status='unknown',fact_ids=[])
        with self.assertRaises(c.Invalid): c.prepare(p,j,s)
        s['reviewed_issues']=['r1']; self.assertEqual(c.prepare(p,j,s)['manifest']['status'],'draft_only')
    def test_required_gap_not_rejection(self):
        p,j,s=fixtures(); j['requirements'][0]['status']='gap'; s['reviewed_issues']=['r1']
        self.assertEqual(c.prepare(p,j,s)['fit']['status'],'required_gap')
    def test_no_role_selection(self):
        p,j,s=fixtures(); s['user_selected']=False
        with self.assertRaises(c.Invalid): c.prepare(p,j,s)
    def test_wrong_job(self):
        p,j,s=fixtures(); s['job_id']='other'
        with self.assertRaises(c.Invalid): c.prepare(p,j,s)
    def test_exact_output_and_html_escape(self):
        p,j,s=fixtures(); p['facts'][0]['statement']='<script>alert(1)</script>'
        r=c.prepare(p,j,s)
        self.assertNotIn('<script>',r['draft_html']); self.assertIn('&lt;script&gt;',r['draft_html'])
        self.assertIn(p['facts'][0]['statement'],r['letter'])
    def test_stale_inputs_recomputed(self):
        p,j,s=fixtures(); first=c.prepare(p,j,s)['manifest']['input_sha256']
        p['facts'][0]['statement']='Changed synthetic assertion.'
        self.assertNotEqual(c.prepare(p,j,s)['manifest']['input_sha256'],first)
    def test_preference_unknown_and_conflict(self):
        p,j,s=fixtures(); p['preferences']=[{'id':'p1','statement':'User preference placeholder','source':'Synthetic','confirmed':True}]
        self.assertEqual(c.assess(p,j)['unassessed_preferences'],['p1'])
        j['preference_matches']=[{'preference_id':'p1','status':'conflict','posting_quote':'Synthetic mismatch','reviewed':True}]
        with self.assertRaises(c.Invalid): c.prepare(p,j,s)
    def test_cli_empty_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)/'profile.json'; command=[sys.executable,str(ROOT/'scripts/career.py'),'init',str(dst)]
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertEqual(json.loads(dst.read_text())['facts'],[])
            before=dst.read_bytes(); self.assertEqual(subprocess.run(command,capture_output=True).returncode,2)
            self.assertEqual(before,dst.read_bytes())
    def test_isolated_script_and_cli_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); standalone=base/'standalone.py'; standalone.write_bytes((ROOT/'scripts/career.py').read_bytes())
            p,j,s=fixtures()
            for name,value in [('p',p),('j',j),('s',s)]: (base/(name+'.json')).write_text(json.dumps(value))
            result=subprocess.run([sys.executable,str(standalone),'prepare','--profile',str(base/'p.json'),'--job',str(base/'j.json'),'--selection',str(base/'s.json'),'--out',str(base/'draft')],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((base/'draft/application-draft.html').exists())
            self.assertEqual(len(list((base/'draft').iterdir())),4)



class PublicSafetyTests(unittest.TestCase):
    def test_exact_quantity_is_not_rewritten(self):
        p,j,s=fixtures()
        p['facts'][0]['statement']='Scheduled 60 synthetic appointments.'
        result=c.prepare(p,j,s)
        self.assertIn('Scheduled 60 synthetic appointments.',result['letter'])
        self.assertNotIn('600',result['draft_html'])

    def test_free_text_override_is_rejected(self):
        p,j,s=fixtures()
        s['resume_text']='Scheduled 600 synthetic appointments.'
        with self.assertRaises(c.Invalid):
            c.prepare(p,j,s)

if __name__=='__main__': unittest.main()
