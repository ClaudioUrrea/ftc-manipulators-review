"""RS2 auditoria: dos conjuntos complementarios de Scopus, cribados con las mismas reglas de rs2_screen.py (no entran al corpus principal).
 (a) S08sup: SF01 con el bloque de manipulador sustituido por los terminos que la cadena no cubre ("multi joint robot*", "multijoint robot*",
     "robotic system*", "robot system*", "multi link robot*", "n link robot*") AND NOT bloque original. Mide cuanto se pierde por la cadena.
 (b) S01e: SF01 sin LANGUAGE(english) AND NOT LANGUAGE(english). Lista de registros no ingleses en alcance (EX-LANG) para el suplemento.
Uso: python3 -I rs2_supplementary.py <CODEBOOK_FAME.csv> <carpeta_DATOS> <dir_scripts>"""
import csv, glob, json, os, re, sys, collections
csv.field_size_limit(10**9)
CBP, D, SD = sys.argv[1:4]
src = open(os.path.join(SD, 'rs2_screen.py'), encoding='utf-8').read().split("if __name__ == '__main__':")[0]
sys.argv = ['x', CBP, D]; exec(src)
corp = list(csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8')))
nt = lambda t: re.sub(r'[^a-z0-9]+', ' ', t.lower()).strip()
c_doi = {r['doi'] for r in corp if r['doi']}; c_t = {nt(r['title']) for r in corp}
def load(pat, force_english=False):
    out = []
    for r in csv.DictReader(open(glob.glob(os.path.join(D, pat))[0], encoding='utf-8-sig')):
        rec = dict(doi=r['DOI'].lower(), title=r['Title'], abstract=r['Abstract'].replace('[No abstract available]', ''), author_kw=r['Author Keywords'], index_kw='',
                   doctype=r['Document Type'], language='English' if force_english else r['Language of Original Document'], authors=r['Authors'], year=r['Year'],
                   journal=r['Source title'], lang_orig=r['Language of Original Document'], eid=r['EID'], cited_by=r['Cited by'], note='')
        dec, rule, _ = screen(rec); rec.update(decision=dec, rule=rule, layer=layer(rec), in_corpus=int(rec['doi'] in c_doi or nt(rec['title']) in c_t))
        out.append(rec)
    return out
cols = ['eid', 'doi', 'year', 'title', 'journal', 'lang_orig', 'doctype', 'layer', 'decision', 'rule', 'in_corpus', 'cited_by']
res = {}
for name, pat, fe in (('S08sup', 'S08sup_*.csv', False), ('S01e', 'S01e_*.csv', True)):
    rows = load(pat, fe)
    with open(os.path.join(D, 'SCREEN_%s_RS2.csv' % name), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    y = lambda r: '2016' <= r['year'] <= '2026'
    res[name] = dict(n=len(rows), ya_en_corpus=sum(r['in_corpus'] for r in rows), decision=collections.Counter(r['decision'] for r in rows),
                     include_primary=sum(r['decision'] == 'INCLUDE' and r['layer'] == 'P' for r in rows),
                     include_primary_2016_2026=sum(r['decision'] == 'INCLUDE' and r['layer'] == 'P' and y(r) for r in rows),
                     include_reviews=sum(r['decision'] == 'INCLUDE' and r['layer'] == 'R' for r in rows),
                     idioma=collections.Counter(r['lang_orig'] for r in rows).most_common(5))
main = json.load(open(os.path.join(D, 'CONTEOS_screen_RS2.json')))
res['S08sup']['incremento_relativo_include_primary'] = round(res['S08sup']['include_primary'] / main['include_primary'], 3)
json.dump(res, open(os.path.join(D, 'CONTEOS_supplementary_RS2.json'), 'w'), indent=1, ensure_ascii=False); print(json.dumps(res, ensure_ascii=False))
