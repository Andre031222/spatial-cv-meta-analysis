import csv, json, os, sys, time, urllib.parse, urllib.request

csv.field_size_limit(10**9)
root = sys.argv[1]
out_dir = os.path.join(root, 'fulltext', 'pdfs')
log_path = os.path.join(root, 'fulltext', 'fulltext_log.csv')
os.makedirs(out_dir, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (systematic-review OA retrieval; academic use)'}

recs = [r for r in csv.DictReader(open(os.path.join(root, 'screening', 'screening_title_abstract.csv'), encoding='utf-8'))
        if r['ta_decision'] in ('include', 'maybe')]
done = {}
if os.path.exists(log_path):
    done = {r['record_id']: r for r in csv.DictReader(open(log_path, encoding='utf-8'))}

def get(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)

rows = []
for i, r in enumerate(recs, 1):
    rid, doi = r['record_id'], r['DOI'].strip()
    pdf = os.path.join(out_dir, rid + '.pdf')
    if rid in done and done[rid]['got_pdf'] == 'yes' and os.path.exists(pdf):
        rows.append(done[rid]); continue
    row = {'record_id': rid, 'DOI': doi, 'ta_decision': r['ta_decision'], 'is_oa': '', 'oa_status': '',
           'pdf_url': '', 'got_pdf': 'no', 'source': '', 'note': ''}
    try:
        w = json.load(get('https://api.openalex.org/works/doi:' + urllib.parse.quote(doi)))
        oa = w.get('open_access') or {}
        row['is_oa'], row['oa_status'] = str(oa.get('is_oa')), oa.get('oa_status', '')
        urls = []
        for loc in [w.get('best_oa_location')] + (w.get('locations') or []):
            if loc and loc.get('is_oa') and loc.get('pdf_url') and loc['pdf_url'] not in urls:
                urls.append(loc['pdf_url'])
        for u in urls:
            try:
                data = get(u).read()
                if data[:5] == b'%PDF-':
                    open(pdf, 'wb').write(data)
                    row.update(got_pdf='yes', pdf_url=u, source=urllib.parse.urlparse(u).netloc)
                    break
                row['note'] = 'not a PDF at ' + urllib.parse.urlparse(u).netloc
            except Exception as e:
                row['note'] = f'{type(e).__name__} at {urllib.parse.urlparse(u).netloc}'
        if not urls:
            row['note'] = 'no OA pdf_url in OpenAlex'
    except Exception as e:
        row['note'] = 'OpenAlex lookup failed: ' + type(e).__name__
    rows.append(row)
    print(i, rid, row['got_pdf'], row['note'], flush=True)
    time.sleep(0.3)

with open(log_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
got = sum(r['got_pdf'] == 'yes' for r in rows)
print(f'DONE: {got}/{len(rows)} PDFs downloaded; log -> {log_path}')
