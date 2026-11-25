"""RS2 paso 4: snowball y exhaustividad (protocolo s.6 y s.11). Fuente: OpenAlex (referencias y citantes); cribado con las MISMAS reglas de rs2_screen.py.
Backward: referenced_works de las revisiones semilla presentes en el corpus. Forward: citantes 2016-2026 en ingles (tope 600 por semilla).
Recall = snowball en alcance (INCLUDE) que ya estan en F01 OR SF01 / todos los snowball en alcance; IC de Wilson 95 %.
Uso: python3 -I rs2_snowball.py <CODEBOOK_FAME.csv> <carpeta_DATOS> <dir_scripts>"""
import csv, json, math, os, re, sys, time, urllib.parse, urllib.request
csv.field_size_limit(10**9)
CBP, D, SD = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(os.path.join(SD, 'rs2_screen.py'), encoding='utf-8').read().split("if __name__ == '__main__':")[0]
sys.argv = ['x', CBP, D]; exec(src)   # define screen(), code(), cb, R ...
API = 'https://api.openalex.org/'
SEL = 'id,doi,title,publication_year,type,language,abstract_inverted_index,authorships,primary_location,keywords,cited_by_count'
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'FAME-review-RS2'}), timeout=40) as r: return json.load(r)
        except Exception as e: time.sleep(2 * (i + 1)); err = e
    print('fallo', url[:120], err); return None
def abstract(w):
    ii = w.get('abstract_inverted_index') or {}
    pos = sorted((p, t) for t, ps in ii.items() for p in ps)
    return ' '.join(t for _, t in pos)
def nd(d): return re.sub(r'^https?://(dx\.)?doi\.org/', '', (d or '').lower())
def torec(w):
    st = ((w.get('primary_location') or {}).get('source') or {}).get('type', '')
    typ = {'article': 'Article', 'review': 'Review'}.get(w.get('type'), w.get('type') or '')
    if st == 'conference' and typ == 'Article': typ = 'Conference paper'
    return dict(rid=w['id'].split('/')[-1], doi=nd(w.get('doi')), title=w.get('title') or '', abstract=abstract(w), year=str(w.get('publication_year') or ''),
                author_kw='; '.join(k.get('display_name', '') for k in (w.get('keywords') or [])), index_kw='', doctype=typ,
                language='English' if w.get('language') in ('en', None) else w.get('language'), note='',
                authors='; '.join(a['author']['display_name'] for a in w.get('authorships', [])))
corp = list(csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8')))
c_doi = {r['doi'] for r in corp if r['doi']}; c_title = {re.sub(r'[^a-z0-9]+', ' ', r['title'].lower()).strip() for r in corp}
seeds = {'Visinsky1994': '10.1016/0951-8320(94)90132-5', 'Milecki2023': '10.3390/app13042675', 'Chen2023': '10.1109/taes.2022.3219800',
         'Khan2025': '10.1007/s10462-025-11327-2', 'Quamar2026': '10.1016/j.engappai.2026.116367', 'Zenteno2021': '10.3390/automation2010001'}
found = {}; log = []
for key, doi in seeds.items():
    w = get(API + 'works/doi:' + doi + '?select=id,referenced_works,cited_by_count')
    if not w: log.append((key, 'sin OpenAlex')); continue
    refs = [x.split('/')[-1] for x in w.get('referenced_works', [])]
    log.append((key, 'refs', len(refs), 'citantes', w.get('cited_by_count')))
    for i in range(0, len(refs), 50):
        d = get(API + 'works?per-page=50&select=' + SEL + '&filter=openalex:' + '|'.join(refs[i:i + 50]))
        for x in (d or {}).get('results', []): found.setdefault(x['id'], (x, 'backward', key))
    if key in ('Visinsky1994', 'Milecki2023', 'Chen2023', 'Khan2025', 'Quamar2026'):
        cur, n = '*', 0
        while cur and n < 600:
            d = get(API + 'works?per-page=200&select=' + SEL + '&filter=cites:' + w['id'].split('/')[-1] + ',publication_year:2016-2026,language:en&cursor=' + cur)
            if not d: break
            for x in d['results']: found.setdefault(x['id'], (x, 'forward', key)); n += 1
            cur = d['meta'].get('next_cursor')
out = []
for wid, (w, dirn, key) in found.items():
    r = torec(w)
    dec, rule, _ = screen(r)
    inc = r['doi'] in c_doi or re.sub(r'[^a-z0-9]+', ' ', r['title'].lower()).strip() in c_title
    out.append(dict(direction=dirn, seed=key, oa_id=r['rid'], doi=r['doi'], year=r['year'], title=r['title'][:140], decision=dec, rule=rule, in_corpus=int(inc), has_abstract=int(bool(r['abstract']))))
with open(os.path.join(D, 'SNOWBALL_RS2.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
def wilson(k, n, z=1.96):
    if not n: return (float('nan'),) * 3
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(p, 3), round((c - h) / d, 3), round((c + h) / d, 3)
res = dict(seeds_log=log, unique_snowball=len(out))
for lab, flt in (('todos_anos', lambda o: True), ('2016_2026', lambda o: '2016' <= o['year'] <= '2026')):
    for dirn in ('all', 'backward', 'forward'):
        sub = [o for o in out if flt(o) and (dirn == 'all' or o['direction'] == dirn)]
        for tag, ok in (('INCLUDE', lambda o: o['decision'] == 'INCLUDE'), ('INCLUDE+UNCERTAIN', lambda o: o['decision'] != 'EXCLUDE')):
            s2 = [o for o in sub if ok(o) and o['has_abstract']]
            k = sum(o['in_corpus'] for o in s2)
            res[f'{lab}|{dirn}|{tag}'] = dict(n_in_scope=len(s2), in_corpus=k, recall_wilson=wilson(k, len(s2)))
json.dump(res, open(os.path.join(D, 'CONTEOS_snowball_RS2.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
