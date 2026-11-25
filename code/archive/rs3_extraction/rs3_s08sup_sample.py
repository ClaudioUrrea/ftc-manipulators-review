"""RS3 paso 2: muestra aleatoria (semilla 20261117) de 40 registros INCLUDE de capa P del conjunto complementario S08sup,
para estimar cuantos estan en alcance (lectura de titulo y resumen; juicio en S08sup_JUICIO_40.csv).
Uso: python3 -I rs3_s08sup_sample.py <carpeta_DATOS> <carpeta_RS3>"""
import csv, os, random, sys
csv.field_size_limit(10**9)
D, O = sys.argv[1:3]
scr = [r for r in csv.DictReader(open(os.path.join(D, 'SCREEN_S08sup_RS2.csv'), encoding='utf-8')) if r['decision'] == 'INCLUDE' and r['layer'] == 'P']
raw = {r['EID']: r for r in csv.DictReader(open(os.path.join(D, 'S08sup_SF08sup_Scopus_terminos-perdidos_2026-11-15.csv'), encoding='utf-8-sig'))}
smp = random.Random(20261117).sample(sorted(scr, key=lambda r: r['eid']), 40)
with open(os.path.join(O, 'S08sup_MUESTRA_40.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['k', 'eid', 'doi', 'year', 'title', 'abstract', 'author_kw'])
    for k, r in enumerate(smp, 1): w.writerow([k, r['eid'], r['doi'], r['year'], r['title'], raw[r['eid']]['Abstract'], raw[r['eid']]['Author Keywords']])
print(len(scr), len(smp))
