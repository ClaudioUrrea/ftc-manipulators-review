"""RS3 paso 5: incorpora las fichas de extraccion (extracciones/<rid>.json, una por estudio) a EXTRACCION_L3_S5.csv y calcula R_score.
Las fichas son la fuente; el CSV se regenera. Uso: python3 -I rs3_s5_merge.py <carpeta_RS3>"""
import csv, json, os, sys, glob
O = sys.argv[1]; path = os.path.join(O, 'EXTRACCION_L3_S5.csv')
rows = list(csv.DictReader(open(path, encoding='utf-8'))); cols = list(rows[0].keys()); by = {r['rid']: r for r in rows}
n = 0
for fn in sorted(glob.glob(os.path.join(O, 'extracciones', '*.json'))):
    d = json.load(open(fn, encoding='utf-8')); rid = d['rid']
    assert rid in by, f'{rid} no esta en L3'; bad = set(d) - set(cols); assert not bad, f'{rid}: campos desconocidos {bad}'
    by[rid].update({k: str(v) for k, v in d.items()})
    R = [by[rid][f'R{i}'] for i in range(1, 11)]
    if all(x in ('0', '1') for x in R): by[rid]['R_score'] = str(sum(map(int, R)))
    n += 1
with open(path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
print(n, 'fichas;', sum(r['status'] == 'done' for r in rows), 'extraidas de', len(rows))
