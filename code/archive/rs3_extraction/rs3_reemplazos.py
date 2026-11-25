"""RS3: aplica la regla de reserva de L3-P (enmienda v1.6) a las exclusiones a texto completo.
Lee REEMPLAZOS_L3P.csv (excluido -> reemplazo), agrega al CSV de extraccion una fila pendiente por reemplazo con los datos
bibliograficos de CORPUS_RS2.csv y marca replaced_by en la ficha del excluido. No lee SCREEN_RS2.csv.
Uso: python3 -I rs3_reemplazos.py <carpeta_DATOS> <carpeta_RS3>"""
import csv, json, os, sys
csv.field_size_limit(10**9)
D, O = sys.argv[1:3]
path = os.path.join(O, 'EXTRACCION_L3_S5.csv')
rows = list(csv.DictReader(open(path, encoding='utf-8'))); cols = list(rows[0].keys()); have = {r['rid'] for r in rows}
rep = list(csv.DictReader(open(os.path.join(O, 'REEMPLAZOS_L3P.csv'), encoding='utf-8')))
need = {r['replacement'] for r in rep if r['replacement']}
corpus = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8')) if r['rid'] in need}
added = 0
for r in rep:
    ex, nw = r['excluded'], r['replacement']
    fj = os.path.join(O, 'extracciones', ex + '.json')
    d = json.load(open(fj, encoding='utf-8')); d['replaced_by'] = nw or 'none (no reserve record for this cell)'
    json.dump(d, open(fj, 'w', encoding='utf-8'), ensure_ascii=False)
    if not nw or nw in have: continue
    c = corpus[nw]; row = {k: '' for k in cols}
    row.update(rid=nw, sample='L3-P', selection='replacement_of:' + ex, doi=c['doi'], url='https://doi.org/' + c['doi'] if c['doi'] else '',
               year=c['year'], journal=c['journal'], first_author=c['authors'].split(';')[0].strip(), title=c['title'], OWN='0', status='pending')
    rows.append(row); have.add(nw); added += 1
with open(path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
print(added, 'reemplazos agregados;', len(rows), 'filas')
