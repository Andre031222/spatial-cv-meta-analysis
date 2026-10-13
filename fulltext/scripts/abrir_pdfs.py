"""Speed up manual full-text retrieval.

Opens, in YOUR normal browser (default browser, your own session/institutional access), the direct
PDF links of the next N records still missing a PDF, then watches the downloads folder and imports
every new PDF automatically (matched by DOI/title -> fulltext/pdfs/Rxxxx.pdf).

Usage (from the project folder):
  .venv/bin/python fulltext/scripts/abrir_pdfs.py                # next 10, any publisher
  .venv/bin/python fulltext/scripts/abrir_pdfs.py -n 15 -p Elsevier
  .venv/bin/python fulltext/scripts/abrir_pdfs.py --watch-only    # only import what you download
Options: -n batch size · -p publisher (Elsevier, Wiley, IEEE, Taylor&Francis, ACS, Springer…)
         --only-include · --browser "Google Chrome" · --folder ~/Downloads
Press Ctrl+C to stop watching. Records whose link was already opened are remembered
(fulltext/opened_links.txt) so the next run continues with new ones.
"""
import argparse, json, os, subprocess, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF_DIR = os.path.join(ROOT, 'fulltext', 'pdfs')
OPENED = os.path.join(ROOT, 'fulltext', 'opened_links.txt')
IMPORTER = os.path.join(ROOT, 'fulltext', 'scripts', 'import_downloads.py')
PY = os.path.join(ROOT, '.venv', 'bin', 'python')


def direct_url(o):
    doi, res = o['doi'], o.get('resolved', '')
    pub = o.get('pub', '')
    if pub == 'Elsevier' and 'pii/' in res:
        return f"https://www.sciencedirect.com/science/article/pii/{res.rsplit('/', 1)[-1]}/pdfft?isDTMRedir=true&download=true"
    if pub.startswith('Wiley'):
        return f'https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}?download=true'
    if pub == 'Taylor&Francis':
        return f'https://www.tandfonline.com/doi/pdf/{doi}?download=true'
    if pub == 'ACS':
        return f'https://pubs.acs.org/doi/pdf/{doi}?download=true'
    if pub.startswith('Springer'):
        return f'https://link.springer.com/content/pdf/{doi}.pdf'
    if pub == 'IEEE' and '/document/' in res:
        num = res.rstrip('/').rsplit('/', 1)[-1]
        return f'https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={num}'
    if pub == 'PeerJ' and 'peerj.com/articles/' in res:
        return res.rstrip('/') + '.pdf'
    if pub == 'IOP':
        return f'https://iopscience.iop.org/article/{doi}/pdf'
    return f'https://doi.org/{doi}' if doi else None


def run_import(folder):
    out = subprocess.run([PY, '-I', IMPORTER, ROOT, folder], capture_output=True, text=True).stdout.strip()
    lines = [l for l in out.splitlines() if '<-' in l]
    for l in lines:
        print('  ✓', l)
    return len(lines), out.splitlines()[-1] if out else ''


ap = argparse.ArgumentParser()
ap.add_argument('-n', type=int, default=10)
ap.add_argument('-p', '--publisher', default=None)
ap.add_argument('--only-include', action='store_true')
ap.add_argument('--browser', default=None, help='e.g. "Google Chrome" or "Brave Browser"; default = system default')
ap.add_argument('--folder', default='~/Downloads')
ap.add_argument('--watch-only', action='store_true')
a = ap.parse_args()
folder = os.path.expanduser(a.folder)

if not a.watch_only:
    targets = json.load(open(os.path.join(ROOT, 'fulltext', 'missing_targets.json')))
    opened = set(open(OPENED).read().split()) if os.path.exists(OPENED) else set()
    todo = [o for o in targets
            if not os.path.exists(os.path.join(PDF_DIR, o['record_id'] + '.pdf'))
            and o['record_id'] not in opened
            and (not a.publisher or o.get('pub', '').lower().startswith(a.publisher.lower()))
            and (not a.only_include or o.get('decision') == 'include')]
    todo.sort(key=lambda o: (o.get('decision') != 'include', str(o.get('is_oa')) != 'True', o['record_id']))
    batch = todo[:a.n]
    if not batch:
        print('Nothing left to open for this filter.'); sys.exit()
    print(f'Opening {len(batch)} of {len(todo)} remaining…')
    with open(OPENED, 'a') as f:
        for o in batch:
            url = direct_url(o)
            if not url:
                continue
            cmd = ['open', '-a', a.browser, url] if a.browser else ['open', url]
            subprocess.run(cmd)
            print(f"  → {o['record_id']}  {o.get('pub', '')}  {url}")
            f.write(o['record_id'] + '\n')
            time.sleep(2)  # gentle pacing, like a person opening tabs

print(f'\nWatching {folder} — save the PDFs there (any name). Ctrl+C to stop.')
try:
    while True:
        n, summary = run_import(folder)
        if n:
            print('  ', summary)
        time.sleep(5)
except KeyboardInterrupt:
    print('\nStopped.', run_import(folder)[1])
