#!/usr/bin/env python3
"""Offline, evidence-indexed career preparation. Standard library only; never submits."""
import argparse
import hashlib
import html
import json
from pathlib import Path

class Invalid(ValueError):
    pass

def obj(value, allowed, required, label):
    if not isinstance(value, dict): raise Invalid(f'{label}: expected object')
    if set(value) - set(allowed): raise Invalid(f'{label}: unexpected fields {sorted(set(value)-set(allowed))}')
    if set(required) - set(value): raise Invalid(f'{label}: missing fields {sorted(set(required)-set(value))}')

def text(value, label):
    if not isinstance(value, str) or not value.strip(): raise Invalid(f'{label}: expected nonempty string')
    return value

def array(value, label):
    if not isinstance(value, list): raise Invalid(f'{label}: expected array')
    return value

def records(items, label):
    result = {}
    for item in array(items, label):
        if not isinstance(item, dict): raise Invalid(f'{label}: expected record')
        ident = text(item.get('id'), label+'.id')
        if ident in result: raise Invalid(f'{label}: duplicate id {ident}')
        result[ident] = item
    return result

def profile(p):
    obj(p, ['schema_version','facts','preferences'], ['schema_version','facts','preferences'], 'profile')
    if p['schema_version'] != 1: raise Invalid('profile: unsupported schema version')
    facts = records(p['facts'], 'facts')
    for ident, f in facts.items():
        obj(f, ['id','statement','source','confirmed','category'], ['id','statement','source','confirmed','category'], 'fact '+ident)
        for key in ['statement','source']: text(f[key], 'fact.'+key)
        if f['category'] not in ['experience','skill','education','credential','project']: raise Invalid('fact: invalid category')
        if type(f['confirmed']) is not bool: raise Invalid('fact.confirmed: expected boolean')
    prefs = records(p['preferences'], 'preferences')
    for pref in prefs.values():
        obj(pref, ['id','statement','source','confirmed'], ['id','statement','source','confirmed'], 'preference')
        text(pref['statement'],'preference.statement'); text(pref['source'],'preference.source')
        if type(pref['confirmed']) is not bool: raise Invalid('preference.confirmed: expected boolean')
    return facts

def job(j):
    keys = ['id','company','title','source','checked_at','requirements','preference_matches']
    obj(j, keys, keys, 'job')
    for k in ['id','company','title','source','checked_at']: text(j[k], 'job.'+k)
    reqs = records(j['requirements'], 'requirements')
    if not reqs: raise Invalid('job: at least one reviewed requirement is required')
    for r in reqs.values():
        obj(r, ['id','text','kind','status','fact_ids','rationale','reviewed'], ['id','text','kind','status','fact_ids','rationale','reviewed'], 'requirement')
        text(r['text'],'requirement.text'); text(r['rationale'],'requirement.rationale')
        if r['kind'] not in ['required','preferred']: raise Invalid('requirement: invalid kind')
        if r['status'] not in ['supported','gap','unknown']: raise Invalid('requirement: invalid status')
        if type(r['reviewed']) is not bool: raise Invalid('requirement.reviewed: expected boolean')
        array(r['fact_ids'],'requirement.fact_ids')
    array(j['preference_matches'],'preference_matches')
    return reqs

def assess(p,j):
    facts = profile(p); reqs = job(j)
    prefs = {x['id']: x for x in p['preferences']}
    results = []
    for r in reqs.values():
        ids = r['fact_ids']
        if any(not isinstance(i,str) or i not in facts for i in ids): raise Invalid('requirement: unknown fact ID')
        status = r['status']
        if status in ['supported','gap'] and not ids: raise Invalid('supported/gap needs explicit evidence; missing evidence is unknown')
        if not r['reviewed'] or any(not facts[i]['confirmed'] for i in ids): status = 'unknown'
        results.append({**r, 'effective_status':status, 'evidence':[facts[i]['statement'] for i in ids]})
    preference_results = []
    for m in j['preference_matches']:
        obj(m,['preference_id','status','posting_quote','reviewed'],['preference_id','status','posting_quote','reviewed'],'preference match')
        if m['preference_id'] not in prefs: raise Invalid('unknown preference ID')
        if m['status'] not in ['match','conflict','unknown']: raise Invalid('invalid preference status')
        if type(m['reviewed']) is not bool: raise Invalid('preference reviewed must be boolean')
        if m['status'] != 'unknown': text(m['posting_quote'],'posting_quote')
        status = m['status'] if m['reviewed'] and prefs[m['preference_id']]['confirmed'] else 'unknown'
        preference_results.append({**m,'effective_status':status})
    required = [r for r in results if r['kind']=='required']
    gaps = [r['id'] for r in required if r['effective_status']=='gap']
    unknowns = [r['id'] for r in required if r['effective_status']=='unknown']
    conflicts = [m['preference_id'] for m in preference_results if m['effective_status']=='conflict']
    state = 'required_gap' if gaps else 'needs_clarification' if unknowns or conflicts else 'ready_for_user_review'
    return {'job_id':j['id'],'company':j['company'],'title':j['title'],'status':state,
            'requirements':results,'required_gaps':gaps,'required_unknowns':unknowns,
            'preferences':preference_results,'preference_conflicts':conflicts,
            'unassessed_preferences':[i for i in prefs if i not in {m['preference_id'] for m in preference_results}],
            'limits':'Evidence mapping is human-reviewed, not a verified qualification, hiring probability or automatic eligibility decision.'}

def prepare(p,j,selection):
    report = assess(p,j); facts = profile(p)
    obj(selection,['job_id','user_selected','reviewed_issues','resume_fact_ids','letter_fact_ids'],['job_id','user_selected','reviewed_issues','resume_fact_ids','letter_fact_ids'],'selection')
    if selection['job_id'] != j['id']: raise Invalid('selection refers to a different job')
    if selection['user_selected'] is not True: raise Invalid('user must select role before preparation')
    array(selection['reviewed_issues'],'reviewed_issues')
    issues = report['required_gaps']+report['required_unknowns']+report['preference_conflicts']
    if any(x not in selection['reviewed_issues'] for x in issues): raise Invalid('review gaps/unknowns/conflicts with the user first')
    for field in ['resume_fact_ids','letter_fact_ids']:
        ids = array(selection[field],field)
        if not ids: raise Invalid(field+': select at least one confirmed fact')
        if len(set(ids)) != len(ids): raise Invalid('duplicate selected facts')
        for i in ids:
            if i not in facts or not facts[i]['confirmed']: raise Invalid('draft references missing/unconfirmed fact')
    lines = [facts[i]['statement'] for i in selection['resume_fact_ids']]
    letter = 'Application for '+j['title']+' at '+j['company']+'\n\nRelevant experience and qualifications:\n\n'+'\n\n'.join(facts[i]['statement'] for i in selection['letter_fact_ids'])
    rendered = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Application draft</title><style>body{max-width:760px;margin:3em auto;font:17px/1.6 system-ui;color:#172133;padding:1em}li{margin:.8em 0}aside{padding:1em;background:#fff4d4}</style><h1>Application draft</h1><p>'+html.escape(j['title']+' · '+j['company'])+'</p><aside>Local draft. Add contact details privately, review every statement and the fit report before sharing. No submission has occurred.</aside><h2>Selected evidence</h2><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in lines)+'</ul><h2>Cover-letter starter</h2>'+''.join('<p>'+html.escape(s)+'</p>' for s in letter.split('\n\n'))+'</html>'
    digest = hashlib.sha256(json.dumps({'profile':p,'job':j,'selection':selection},sort_keys=True).encode()).hexdigest()
    return {'fit':report,'draft_html':rendered,'letter':letter,'manifest':{'input_sha256':digest,'fact_ids':selection['resume_fact_ids'],'status':'draft_only','approval':'Not granted by this manifest. User must review final destination, files and answers before any submission.'}}

def setup_doc(p):
    """Export user-owned data only, never bundled workflow instructions."""
    profile(p)
    lines = ['# My career setup', '', '## Confirmed facts', '']
    for f in p['facts']:
        if f['confirmed']:
            lines += [f"- [{f['id']}] {f['statement']}", f"  Source: {f['source']}"]
    if not any(f['confirmed'] for f in p['facts']): lines += ['No confirmed facts recorded.']
    lines += ['', '## Confirmed preferences', '']
    for pref in p['preferences']:
        if pref['confirmed']: lines += [f"- [{pref['id']}] {pref['statement']}", f"  Source: {pref['source']}"]
    if not any(x['confirmed'] for x in p['preferences']): lines += ['No confirmed preferences recorded.']
    lines += ['', '## Unconfirmed information and open questions', '']
    pending = [x for x in p['facts']+p['preferences'] if not x['confirmed']]
    for x in pending: lines += [f"- [{x['id']}] {x['statement']}", f"  Source: {x['source']}"]
    if not pending: lines += ['No pending entries recorded. Missing information has not been assumed.']
    return '\n'.join(lines)+'\n'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def resume_pdf(p, j, selection, destination):
    """Render only selected confirmed facts. No invented identity or external calls."""
    prepare(p,j,selection)
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
    fontdir=Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('ResumeVera',str(fontdir/'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('ResumeVeraBold',str(fontdir/'VeraBd.ttf')))
    facts = profile(p)
    styles = getSampleStyleSheet()
    for key in ['BodyText','Title','Heading1','Heading2']: styles[key].fontName='ResumeVera' if key=='BodyText' else 'ResumeVeraBold'
    styles['BodyText'].fontSize=10
    styles['BodyText'].leading=15
    styles['Heading1'].alignment=TA_LEFT
    story=[Paragraph('Resume',styles['Title']),Paragraph(html.escape(j['title']),styles['Heading2']),Spacer(1,12)]
    for category in ['experience','skill','education','credential','project']:
        entries=[facts[i]['statement'] for i in selection['resume_fact_ids'] if facts[i]['category']==category]
        if entries:
            story.append(Paragraph(category.title(),styles['Heading2']))
            for entry in entries:
                # Fail closed for glyphs not reliably supported by built-in PDF fonts.
                try: entry.encode('cp1252')
                except UnicodeEncodeError: raise Invalid('PDF text needs a Unicode font; no silent replacement permitted')
                story += [Paragraph(html.escape(entry).replace('\n','<br/>'),styles['BodyText']),Spacer(1,9)]
    try: j['title'].encode('cp1252')
    except UnicodeEncodeError: raise Invalid('PDF title needs a Unicode font')
    stream=BytesIO()
    SimpleDocTemplate(stream, pagesize=(612,792), leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=48).build(story)
    with Path(destination).open('xb') as f: f.write(stream.getvalue())

def indeed_plan(p,j,selection,form):
    """Offline plan only. A confirmed mapping is not consent to transmit it."""
    from urllib.parse import urlparse
    result=prepare(p,j,selection)
    obj(form,['url','job_id','fields'],['url','job_id','fields'],'form')
    u=urlparse(text(form['url'],'url'))
    if u.scheme!='https' or u.hostname not in ['indeed.com','www.indeed.com','ca.indeed.com'] or u.username or u.password or u.port not in [None,443]:
        raise Invalid('Not an allowed Indeed HTTPS origin; external ATS requires a separate product')
    if form['job_id']!=j['id']: raise Invalid('form job mismatch')
    facts=profile(p); fields=records(form['fields'],'fields'); actions=[]
    for f in fields.values():
        obj(f,['id','label','kind','fact_id','confirmed'],['id','label','kind','fact_id','confirmed'],'field')
        text(f['label'],'field label')
        if type(f['confirmed']) is not bool: raise Invalid('field confirmation must be boolean')
        if f['kind'] not in ['qualification','contact','sensitive','legal','screening','upload','unknown']: raise Invalid('field kind')
        if f['fact_id'] is not None and f['fact_id'] not in facts: raise Invalid('unknown field fact')
        can_copy=f['kind']=='qualification' and f['confirmed'] and f['fact_id'] in selection['resume_fact_ids'] and facts[f['fact_id']]['confirmed']
        actions.append({'field_id':f['id'],'label':f['label'],'action':'propose_exact_copy' if can_copy else 'manual_user_answer','value':facts[f['fact_id']]['statement'] if can_copy else None})
    return {'product':'honest-apply-indeed','status':'offline_plan_not_executed','url':form['url'],'job_id':j['id'],'input_sha256':result['manifest']['input_sha256'],'actions':actions,'external_action_approval_required':True,'submission':'manual_only','limits':'No live DOM adapter. Review each field label and value on the current page; mapping flags are not authenticated approval. No clicks, uploads, navigation or transmissions occurred.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command',required=True)
    init = sub.add_parser('init'); init.add_argument('destination')
    setup = sub.add_parser('setup-doc'); setup.add_argument('--profile',required=True); setup.add_argument('--out',required=True)
    for command in ['assess','prepare','resume-pdf','indeed-plan']:
        a = sub.add_parser(command); a.add_argument('--profile',required=True); a.add_argument('--job',required=True)
        if command in ['prepare','resume-pdf','indeed-plan']: a.add_argument('--selection',required=True)
        a.add_argument('--out',required=True)
        if command=='indeed-plan': a.add_argument('--form',required=True)
    args = ap.parse_args()
    try:
        if args.command=='init':
            with Path(args.destination).open('x',encoding='utf-8') as f: json.dump({'schema_version':1,'facts':[],'preferences':[]},f,indent=2)
        elif args.command=='setup-doc':
            p = load(args.profile); document = setup_doc(p)
            out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
            (out/'my-career-setup.md').write_text(document,encoding='utf-8')
            (out/'my-career-data.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
        elif args.command=='resume-pdf':
            resume_pdf(load(args.profile),load(args.job),load(args.selection),args.out)
        elif args.command=='indeed-plan':
            result=indeed_plan(load(args.profile),load(args.job),load(args.selection),load(args.form))
            with Path(args.out).open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
        elif args.command=='assess':
            result = assess(load(args.profile),load(args.job))
            with Path(args.out).open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
        else:
            result = prepare(load(args.profile),load(args.job),load(args.selection))
            out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
            for name,key in [('application-draft.html','draft_html'),('cover-letter-starter.txt','letter')]: (out/name).write_text(result[key],encoding='utf-8')
            for name,key in [('fit-review.json','fit'),('review-manifest.json','manifest')]: (out/name).write_text(json.dumps(result[key],indent=2),encoding='utf-8')
    except (Invalid,ValueError,OSError,TypeError,KeyError) as e:
        ap.exit(2,f'Blocked: {e}\n')
if __name__=='__main__': main()
