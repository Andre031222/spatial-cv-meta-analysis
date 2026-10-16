import csv, re, sys, collections

csv.field_size_limit(10**9)
root, files = sys.argv[1], sys.argv[2:]
SHEET = root + '/screening/screening_title_abstract.csv'
norm = lambda t: re.sub(r'[^a-z0-9]', '', (t or '').lower())

def read_plain(path):
    recs, cur, tag = [], {}, None
    for line in open(path, encoding='utf-8-sig', errors='replace'):
        line = line.rstrip('\n')
        if line.startswith('ER'):
            recs.append(cur); cur, tag = {}, None; continue
        if len(line) >= 2 and line[:2].strip() and line[2:3] == ' ':
            tag = line[:2]; cur[tag] = line[3:]
        elif tag and line.startswith('   '):
            sep = '; ' if tag in ('AU', 'AF', 'DE', 'ID') else ' '
            cur[tag] += sep + line.strip()
    return recs

def read_tab(path):
    return list(csv.DictReader(open(path, encoding='utf-8-sig', errors='replace'), delimiter='\t'))

rows = list(csv.DictReader(open(SHEET, encoding='utf-8')))
fields = list(rows[0].keys())
seen_doi = {r['DOI'].strip().lower() for r in rows if r['DOI'].strip()}
seen_t = {norm(r['Title']) for r in rows}

wos = []
for f in files:
    head = open(f, encoding='utf-8-sig', errors='replace').read(200)
    wos += read_tab(f) if '\t' in head.splitlines()[0] else read_plain(f)
print('WoS records read:', len(wos), collections.Counter(r.get('DT', '?') for r in wos).most_common(5))

SP = re.compile(r'spatial(ly)? (block|cross|k-fold|leave|validation|partition|hold)|leave-(location|one-site|one-field|one-region|one-cluster|one-group)-out|target-oriented|nndm|area of applicability|buffered', re.I)
RN = re.compile(r'random (cross|k-fold|split|partition|sampling|cv)|non-?spatial|conventional cross|standard cross|over-?optimis|overly optimistic|overestimat|inflat', re.I)
REV = re.compile(r'\breview\b|meta-analys', re.I)

new, dup, n = [], 0, len(rows)
for r in wos:
    doi, title = (r.get('DI') or '').strip().lower(), r.get('TI', '')
    if (doi and doi in seen_doi) or norm(title) in seen_t:
        dup += 1; continue
    if 'Article' not in r.get('DT', 'Article') or 'Review' in r.get('DT', ''):
        continue
    seen_doi.add(doi); seen_t.add(norm(title)); n += 1
    txt = title + ' ' + r.get('AB', '') + ' ' + r.get('DE', '')
    pri = 'X_check_review' if REV.search(title) else 'A_both' if SP.search(txt) and RN.search(txt) else 'B_spatial_only' if SP.search(txt) else 'C_low'
    o = {k: '' for k in fields}
    o.update({'priority': pri, 'record_id': f'R{n:04d}', 'Title': title, 'Year': r.get('PY', ''),
              'Source title': r.get('SO', ''), 'DOI': r.get('DI', ''), 'Abstract': r.get('AB', ''),
              'Author Keywords': r.get('DE', ''), 'Cited by': r.get('TC', ''), 'EID': r.get('UT', ''),
              'in_v1': 'False', 'source_query': 'wos'})
    new.append(o)

with open(SHEET, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows + new)
print('duplicates vs Scopus:', dup, '| new unique originals:', len(new), collections.Counter(o['priority'] for o in new))
print('sheet total now:', len(rows) + len(new))
