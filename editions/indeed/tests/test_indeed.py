from test_career import c, fixtures
import unittest,tempfile,copy
from pathlib import Path
class IndeedTests(unittest.TestCase):
    def form(self):
        return {'url':'https://ca.indeed.com/viewjob?jk=fixture','job_id':'j1','fields':[{'id':'q1','label':'Describe task A experience','kind':'qualification','fact_id':'f1','confirmed':True}]}
    def test_plan(self):
        p,j,s=fixtures(); r=c.indeed_plan(p,j,s,self.form()); self.assertEqual(r['actions'][0]['value'],p['facts'][0]['statement']); self.assertEqual(r['status'],'offline_plan_not_executed')
    def test_manual(self):
        for kind in ['contact','sensitive','legal','screening','upload','unknown']:
            p,j,s=fixtures(); f=self.form(); f['fields'][0]['kind']=kind
            self.assertIsNone(c.indeed_plan(p,j,s,f)['actions'][0]['value'])
    def test_unconfirmed_mapping(self):
        p,j,s=fixtures(); f=self.form(); f['fields'][0]['confirmed']=False
        self.assertIsNone(c.indeed_plan(p,j,s,f)['actions'][0]['value'])
    def test_external_hosts(self):
        for url in ['https://indeed.com.evil.example','http://indeed.com','https://external.example','https://user@indeed.com','https://indeed.com:444']:
            p,j,s=fixtures(); f=self.form(); f['url']=url
            with self.assertRaises(c.Invalid): c.indeed_plan(p,j,s,f)
    def test_wrong_job(self):
        p,j,s=fixtures(); f=self.form(); f['job_id']='other'
        with self.assertRaises(c.Invalid): c.indeed_plan(p,j,s,f)
    def test_pdf(self):
        from pypdf import PdfReader
        p,j,s=fixtures()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'resume.pdf'; c.resume_pdf(p,j,s,path)
            self.assertIn(p['facts'][0]['statement'],PdfReader(path).pages[0].extract_text())
            with self.assertRaises(FileExistsError): c.resume_pdf(p,j,s,path)
    def test_unicode_fail_closed(self):
        p,j,s=fixtures(); p['facts'][0]['statement']='技能'
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(c.Invalid): c.resume_pdf(p,j,s,Path(d)/'resume.pdf')
