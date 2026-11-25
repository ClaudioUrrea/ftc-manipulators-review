"""RS2 paso 1: lee los exports WoS (X01_F01*.bib) y Scopus (S01_SF01*.csv), normaliza y deduplica.
Regla (protocolo v1.4 s.7): DOI normalizado exacto; si no, titulo normalizado + apellido del 1er autor + anio (+-1). Se conserva WoS.
Uso: python3 -I rs2_build_corpus.py <carpeta_DATOS>   Salida: CORPUS_RS2.csv, CONTEOS_dedup_RS2.json"""
import csv, glob, html, json, os, re, sys, unicodedata
csv.field_size_limit(10**9)
D = sys.argv[1]

def clean(s):
    s = re.sub(r'\{\\?[\'"`^~=.]?\\?(\w)\}', r'\1', s or '')
    s = s.replace('\\&', '&').replace('\\_', '_').replace('\\%', '%').replace('\\$', '$')
    s = re.sub(r'[{}\\]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def ndoi(d):
    d = (d or '').strip().lower()
    d = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', d)
    d = html.unescape(d).replace('\\', '').replace('{', '').replace('}', '').replace(' ', '')
    return d

def parse_bib(path):
    t = open(path, encoding='utf-8-sig').read()
    out = []
    for m in re.finditer(r'^@(\w+)\{\s*([^,\s]+),', t, re.M):
        start = m.end()
        nxt = re.search(r'^@\w+\{', t[start:], re.M)
        body = t[start:start + nxt.start()] if nxt else t[start:]
        rec = {'_bibtype': m.group(1)}
        for f in re.finditer(r'^([A-Za-z-]+)\s*=\s*\{', body, re.M):
            i, depth = f.end(), 1
            j = i
            while j < len(body) and depth:
                c = body[j]
                if c == '{' and body[j-1] != '\\': depth += 1
                elif c == '}' and body[j-1] != '\\': depth -= 1
                j += 1
            rec[f.group(1)] = body[i:j-1]
        out.append(rec)
    return out

rows = []
files = sorted(glob.glob(os.path.join(D, 'X01_F01_WoS_*.bib')))
ids = set()
for p in files:
    for r in parse_bib(p):
        uid = r.get('Unique-ID', '')
        if uid in ids: continue
        ids.add(uid)
        typ = clean(r.get('Type', ''))
        title = clean(r.get('Title', ''))
        rows.append(dict(src='WOS', wos_id=uid, eid='', doi=ndoi(clean(r.get('DOI', ''))), title=title,
            authors=clean(r.get('Author', '')).replace(' and ', '; '), year=r.get('Year', ''),
            journal=clean(r.get('Journal', '') or r.get('Booktitle', '')), doctype=typ,
            language=clean(r.get('Language', '')), abstract=clean(r.get('Abstract', '')),
            author_kw=clean(r.get('Keywords', '')), index_kw=clean(r.get('Keywords-Plus', '')),
            cited_by=r.get('Times-Cited', ''), note=clean(r.get('Note', ''))))
n_wos = len(rows)
sc = list(csv.DictReader(open(glob.glob(os.path.join(D, 'S01_SF01_Scopus_*.csv'))[0], encoding='utf-8-sig')))
for r in sc:
    rows.append(dict(src='SCOPUS', wos_id='', eid=r['EID'], doi=ndoi(r['DOI']), title=clean(r['Title']),
        authors=r['Authors'].replace(', ', '; ') if False else r['Authors'], year=r['Year'],
        journal=r['Source title'], doctype=r['Document Type'] + ('; ' + r['Publication Stage'] if r['Publication Stage'] != 'Final' else ''),
        language=r['Language of Original Document'], abstract=clean(r['Abstract']).replace('[No abstract available]', ''),
        author_kw=r['Author Keywords'], index_kw=r['Index Keywords'], cited_by=r['Cited by'], note=''))

def surn(a):
    """tokens del primer autor sin iniciales (Scopus: 'Liu S.'; WoS: 'Liu, Sihan' o 'Duc Thien Tran')"""
    return {w for w in norm(a.split(';')[0]).split() if len(w) > 1}
def klass(r): return 'conf' if re.search(r'proceedings|conference', r['doctype'], re.I) and not re.search(r'^article', r['doctype'], re.I) else 'jour'
by_doi, by_t = {}, {}
for i, r in enumerate(rows[:n_wos]):
    if r['doi']: by_doi.setdefault(r['doi'], i)
    by_t.setdefault(norm(r['title']), []).append(i)
merged = dup_doi = dup_title = dup_title_noauthor = 0
for r in rows[n_wos:]:
    hit = by_doi.get(r['doi']) if r['doi'] else None
    how = 'doi'
    if hit is None:
        for i in by_t.get(norm(r['title']), []):
            w = rows[i]
            if w['src'] == 'BOTH': continue
            if w['doi'] and r['doi'] and w['doi'] != r['doi'] and not (klass(w) == klass(r) and w['year'] == r['year']): continue   # DOI distintos = registros distintos (congreso y revista), salvo misma clase y anio (variantes SICI del mismo DOI)
            try: ok = abs(int(w['year']) - int(r['year'])) <= 1
            except ValueError: ok = False
            if not ok: continue
            if surn(w['authors']) & surn(r['authors']): hit, how = i, 'title'; break
            # respaldo (auditoria 15-11): el campo de autor difiere por errata o formato; mismo titulo (>= 40 caracteres), anio +-1 y misma clase de documento
            if len(norm(r['title'])) >= 40 and klass(w) == klass(r): hit, how = i, 'title_noauthor'; break
    if hit is not None:
        w = rows[hit]; w['src'] = 'BOTH'; w['eid'] = r['eid']; r['_dup'] = True
        if how == 'doi': dup_doi += 1
        elif how == 'title': dup_title += 1
        else: dup_title_noauthor += 1
        if not w['doi'] and r['doi']: w['doi'] = r['doi']
        if not w['abstract'] and r['abstract']: w['abstract'] = r['abstract']
        merged += 1
corpus = [r for r in rows if not r.get('_dup')]
# duplicados internos (misma base) por DOI, o por titulo + autor + anio +-1 + misma clase sin DOI en conflicto
seen, tmp, internal = {}, [], 0
for r in corpus:
    if r['doi'] and r['doi'] in seen: internal += 1; continue
    if r['doi']: seen[r['doi']] = 1
    tmp.append(r)
final, bt = [], {}
for r in tmp:
    dup = None
    for w in bt.get(norm(r['title']), []):
        try: ok = abs(int(w['year']) - int(r['year'])) <= 1
        except ValueError: ok = False
        if ok and klass(w) == klass(r) and not (w['doi'] and r['doi']) and surn(w['authors']) & surn(r['authors']) and len(norm(r['title'])) >= 40:
            dup = w; break
    if dup is not None:
        internal += 1
        if not dup['doi'] and r['doi']: dup['doi'] = r['doi']
        if not dup['abstract'] and r['abstract']: dup['abstract'] = r['abstract']
        if {dup['src'], r['src']} == {'WOS', 'SCOPUS'}: dup['src'] = 'BOTH'; dup['eid'] = dup['eid'] or r['eid']
        continue
    bt.setdefault(norm(r['title']), []).append(r); final.append(r)
for k, r in enumerate(final, 1): r['rid'] = 'R%05d' % k
cols = ['rid', 'src', 'wos_id', 'eid', 'doi', 'title', 'authors', 'year', 'journal', 'doctype', 'language', 'abstract', 'author_kw', 'index_kw', 'cited_by', 'note']
with open(os.path.join(D, 'CORPUS_RS2.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader(); w.writerows(final)
cnt = dict(wos_records=n_wos, scopus_records=len(sc), identified=n_wos + len(sc), dup_removed_by_doi=dup_doi,
           dup_removed_by_title=dup_title, dup_removed_by_title_author_field_differs=dup_title_noauthor, dup_internal_or_residual=internal, unique=len(final),
           only_wos=sum(r['src'] == 'WOS' for r in final), only_scopus=sum(r['src'] == 'SCOPUS' for r in final),
           both=sum(r['src'] == 'BOTH' for r in final))
json.dump(cnt, open(os.path.join(D, 'CONTEOS_dedup_RS2.json'), 'w'), indent=1)
print(cnt)
