import csv, glob, json, collections
csv.field_size_limit(10**9)
S = json.load(open('qc/qc_sample.json'))
ft = {r['record_id']: r for r in csv.DictReader(open('fulltext/fulltext_decisions.csv', encoding='utf-8'))}
ex = list(csv.DictReader(open('extraction/extraction_template.csv', encoding='utf-8')))
qc = [r for f in sorted(glob.glob('qc/qc_part*.csv')) for r in csv.DictReader(open(f, encoding='utf-8'))]
qd = {}
for r in qc:
    qd.setdefault(r['record_id'], r['qc_decision'].strip().lower())
ids = S['include'] + S['exclude']
a = [(ft[i]['ft_decision'], qd.get(i, 'missing')) for i in ids]
agree = sum(x == y for x, y in a); n = len(a)
p1 = collections.Counter(x for x, _ in a); p2 = collections.Counter(y for _, y in a)
pe = sum(p1[k] * p2[k] for k in set(p1) | set(p2)) / n**2
kappa = (agree / n - pe) / (1 - pe)
dis = [(i, x, y) for i, (x, y) in zip(ids, a) if x != y]
def f(v):
    try: return float(v)
    except: return None
vals = []
for r in qc:
    if r['qc_decision'].strip().lower() != 'include' or not r['metric']: continue
    vr, vs = f(r['value_random']), f(r['value_spatial'])
    if vr is None or vs is None: continue
    if vr > 1.5 and r['metric'].upper() in ('R2', 'AUC', 'ACCURACY', 'OA', 'F1', 'KAPPA'): vr, vs = vr / 100, vs / 100
    cand = [e for e in ex if e['record_id'] == r['record_id'] and e['metric'].lower()[:3] == r['metric'].lower()[:3]]
    tol = lambda a, b: abs(a - b) <= max(0.02, 0.05 * abs(b))
    ok = any(f(e['value_random']) is not None and f(e['value_spatial']) is not None and tol(vr, f(e['value_random'])) and tol(vs, f(e['value_spatial'])) for e in cand)
    vals.append((r['record_id'], r['metric'], vr, vs, ok, len(cand)))
vm = sum(v[4] for v in vals)
out = {'n_records': n, 'decision_agreement': agree / n, 'cohen_kappa': kappa, 'decision_disagreements': dis,
       'value_pairs_checked': len(vals), 'value_pairs_matching': vm, 'value_agreement': vm / len(vals) if vals else None,
       'value_mismatches': [v for v in vals if not v[4]]}
json.dump(out, open('qc/qc_agreement.json', 'w'), indent=1, default=str)
print(f"Eligibility: {agree}/{n} agree ({100*agree/n:.0f}%), Cohen's kappa = {kappa:.2f}")
print('Disagreements:', dis)
print(f"Values: {vm}/{len(vals)} QC pairs match a first-reviewer row (±max(0.02, 5%)) = {100*vm/len(vals):.0f}%")
for v in out['value_mismatches']: print('  mismatch', v)
