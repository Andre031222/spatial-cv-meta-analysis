import csv, os, re, sys, time, urllib.parse
import requests

csv.field_size_limit(10**9)
root = sys.argv[1]
PDF_DIR = os.path.join(root, 'fulltext', 'pdfs')
LOG = os.path.join(root, 'fulltext', 'fulltext_log.csv')
S = requests.Session()
S.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
    'Accept': 'application/pdf,text/html;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def fetch_pdf(url, referer=None):
    try:
        r = S.get(url, timeout=40, allow_redirects=True, headers={'Referer': referer or url})
        if r.status_code == 200 and r.content[:5] == b'%PDF-':
            return r.content, 'ok'
        if r.status_code == 200 and 'html' in r.headers.get('Content-Type', ''):
            m = re.search(r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)', r.text)
            if m and m.group(1) != url:
                r2 = S.get(urllib.parse.urljoin(r.url, m.group(1)), timeout=40, headers={'Referer': r.url})
                if r2.status_code == 200 and r2.content[:5] == b'%PDF-':
                    return r2.content, 'ok_via_meta'
        return None, f'HTTP {r.status_code}'
    except Exception as e:
        return None, type(e).__name__

def candidates(doi, title):
    out = []
    q = urllib.parse.quote(doi)
    try:
        w = S.get('https://api.openalex.org/works/doi:' + q, timeout=30).json()
        for loc in [w.get('best_oa_location')] + (w.get('locations') or []):
            if loc and loc.get('is_oa'):
                for k in ('pdf_url', 'landing_page_url'):
                    if loc.get(k):
                        out.append(('openalex_' + k, loc[k]))
    except Exception:
        pass
    try:
        s2 = S.get(f'https://api.semanticscholar.org/graph/v1/paper/DOI:{q}?fields=openAccessPdf,externalIds', timeout=30).json()
        if (s2.get('openAccessPdf') or {}).get('url'):
            out.append(('semanticscholar', s2['openAccessPdf']['url']))
        ext = s2.get('externalIds') or {}
        if ext.get('ArXiv'):
            out.append(('arxiv', 'https://arxiv.org/pdf/' + ext['ArXiv']))
        if ext.get('PubMedCentral'):
            out.append(('europepmc', f"https://europepmc.org/articles/PMC{ext['PubMedCentral']}?pdf=render"))
    except Exception:
        pass
    d = doi.lower()
    if d.startswith('10.3390/'):
        out.append(('pattern_mdpi', f'https://www.mdpi.com/{doi}/pdf'))
    if d.startswith('10.3389/'):
        out.append(('pattern_frontiers', f'https://www.frontiersin.org/articles/{doi}/pdf'))
    if d.startswith('10.1371/'):
        out.append(('pattern_plos', f'https://journals.plos.org/plosone/article/file?id={doi}&type=printable'))
    if d.startswith(('10.1007/', '10.1186/', '10.1140/')):
        out.append(('pattern_springer', f'https://link.springer.com/content/pdf/{doi}.pdf'))
    if d.startswith('10.1038/'):
        out.append(('pattern_nature', f'https://www.nature.com/articles/{doi.split("/", 1)[1]}.pdf'))
    if d.startswith('10.5194/'):
        out.append(('pattern_copernicus', f'https://doi.org/{doi}'))
    if d.startswith(('10.1002/', '10.1111/', '10.1029/')):
        out.append(('pattern_wiley', f'https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}'))
    if d.startswith('10.1080/'):
        out.append(('pattern_tandf', f'https://www.tandfonline.com/doi/pdf/{doi}'))
    out.append(('doi_landing', f'https://doi.org/{doi}'))
    seen, uniq = set(), []
    for s, u in out:
        if u not in seen:
            seen.add(u); uniq.append((s, u))
    return uniq

log = list(csv.DictReader(open(LOG, encoding='utf-8')))
fields = list(log[0].keys())
for extra in ('tried_v2', 'host'):
    if extra not in fields:
        fields.append(extra)
recs = {r['record_id']: r for r in csv.DictReader(open(os.path.join(root, 'screening', 'screening_title_abstract.csv'), encoding='utf-8'))}

got = 0
for i, row in enumerate(log, 1):
    pdf = os.path.join(PDF_DIR, row['record_id'] + '.pdf')
    if row['got_pdf'] == 'yes' and os.path.exists(pdf):
        continue
    doi = row['DOI'].strip()
    if not doi:
        continue
    tried = []
    for src, url in candidates(doi, recs[row['record_id']]['Title']):
        data, status = fetch_pdf(url)
        tried.append(f'{src}:{status}')
        if data:
            open(pdf, 'wb').write(data)
            row.update(got_pdf='yes', pdf_url=url, source=src)
            got += 1
            break
        time.sleep(0.5)
    row['tried_v2'] = '; '.join(tried)[:500]
    row['host'] = urllib.parse.urlparse(requests.utils.requote_uri('https://doi.org/' + doi)).netloc
    print(i, row['record_id'], row['got_pdf'], row['source'] if row['got_pdf'] == 'yes' else tried[-1], flush=True)

with open(LOG, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for r in log:
        w.writerow({k: r.get(k, '') for k in fields})

miss = [r for r in log if r['got_pdf'] != 'yes']
with open(os.path.join(root, 'fulltext', 'missing_by_host.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['record_id', 'DOI', 'doi_prefix', 'is_oa', 'ta_decision', 'doi_url'])
    for r in sorted(miss, key=lambda r: r['DOI'].split('/')[0]):
        w.writerow([r['record_id'], r['DOI'], r['DOI'].split('/')[0], r['is_oa'], r['ta_decision'], 'https://doi.org/' + r['DOI']])
print(f'DONE v2: +{got} new PDFs; total {sum(r["got_pdf"] == "yes" for r in log)}/{len(log)}; missing {len(miss)}')
