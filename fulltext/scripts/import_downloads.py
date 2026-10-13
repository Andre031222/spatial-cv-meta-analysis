"""Import PDFs saved manually (any filename) into fulltext/pdfs/Rxxxx.pdf.

Scans a folder (default ~/Downloads) for PDFs, reads the first pages, and matches each file to a
full-text candidate by DOI (preferred) or by normalised title. Matched files are moved and renamed;
fulltext/fulltext_log.csv is updated (source = manual). Unmatched PDFs are left untouched.

Usage: .venv/bin/python -I fulltext/scripts/import_downloads.py <project_root> [folder]
"""
import csv, os, re, shutil, sys
import pymupdf

csv.field_size_limit(10**9)
root = sys.argv[1]
folder = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else '~/Downloads')
pdf_dir = os.path.join(root, 'fulltext', 'pdfs')
log_path = os.path.join(root, 'fulltext', 'fulltext_log.csv')
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())

cands = {r['record_id']: r for r in csv.DictReader(open(os.path.join(root, 'screening', 'screening_title_abstract.csv'), encoding='utf-8'))
         if r['ta_decision'] in ('include', 'maybe') and not os.path.exists(os.path.join(pdf_dir, r['record_id'] + '.pdf'))}
by_doi = {r['DOI'].lower(): rid for rid, r in cands.items() if r['DOI']}
by_title = {norm(r['Title'])[:60]: rid for rid, r in cands.items() if len(norm(r['Title'])) > 30}

moved = []
for f in sorted(os.listdir(folder)):
    path = os.path.join(folder, f)
    if not f.lower().endswith('.pdf') or not os.path.isfile(path):
        continue
    try:
        if open(path, 'rb').read(5) != b'%PDF-':
            continue
        doc = pymupdf.open(path)
        text = ' '.join(doc[i].get_text() for i in range(min(2, len(doc))))
    except Exception:
        continue
    rid = None
    for d in re.findall(r'10\.\d{4,9}/[^\s"<>]+', text):
        d = d.rstrip('.,;)').lower()
        if d in by_doi:
            rid = by_doi[d]; break
    if not rid:
        t = norm(text)
        rid = next((r for k, r in by_title.items() if k in t), None)
    if rid and rid in cands:
        shutil.move(path, os.path.join(pdf_dir, rid + '.pdf'))
        moved.append((rid, f)); cands.pop(rid)

if moved and os.path.exists(log_path):
    log = list(csv.DictReader(open(log_path, encoding='utf-8')))
    fields = list(log[0].keys())
    ids = {m[0] for m in moved}
    for r in log:
        if r['record_id'] in ids:
            r['got_pdf'], r['source'] = 'yes', 'manual'
    w = csv.DictWriter(open(log_path, 'w', newline='', encoding='utf-8'), fieldnames=fields); w.writeheader(); w.writerows(log)

for rid, f in moved:
    print(f'{rid}  <-  {f}')
print(f'Imported {len(moved)} PDFs; still missing {len(cands)}; total in fulltext/pdfs: {len(os.listdir(pdf_dir))}')
