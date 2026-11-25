"""RS2 paso 5: L3-R (60, 20 por bin E donde haya) y muestra ciega de validacion (60, 20 por resultado de regla), semilla 20261116.
Conjunto de desarrollo excluido de la muestra ciega: known items Actuators + 200 primeros registros por fecha de publicacion (anio, luego rid; lectura literal del protocolo s.7).
Uso: python3 -I rs2_sample.py <carpeta_05> <carpeta_DATOS> <carpeta_RS2>"""
import csv, json, os, random, sys
csv.field_size_limit(10**9)
P, D, O = sys.argv[1:4]; SEED = 20261116
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8'))}
scr = list(csv.DictReader(open(os.path.join(D, 'SCREEN_RS2.csv'), encoding='utf-8')))
known = {r['doi'].lower() for r in csv.DictReader(open(os.path.join(P, 'KNOWN_ITEMS_ACTUATORS.csv'), encoding='utf-8'))}
first200 = {r['rid'] for r in sorted(scr, key=lambda r: (r['year'] or '9999', r['rid']))[:200]}
insp = {r['rid'] for r in csv.DictReader(open(os.path.join(D, 'DEV_inspeccionados_auditoria.csv'), encoding='utf-8'))}   # titulos vistos en la auditoria de reglas
dev = {r['rid'] for r in scr if r['doi'] in known} | first200 | insp
rng = random.Random(SEED)
# L3-R: estudios primarios (capa P) INCLUDE 2016-2026 con resumen. 20 por bin E; si un bin no alcanza, se toman todos y el deficit se reparte
# por igual entre los demas (el sobrante, al bin mas grande). Muestreo estratificado con probabilidades conocidas (n_h / N_h).
pool = sorted([r for r in scr if r['decision'] == 'INCLUDE' and r['layer'] == 'P' and '2016' <= r['year'] <= '2026' and 'NO-ABS' not in r['flags'] and 'RETRACTED' not in r['flags']], key=lambda r: r['rid'])
bins = ('E0-E2', 'E3', 'E4'); cand = {b: [r for r in pool if r['E_bin'] == b] for b in bins}; avail = {b: len(cand[b]) for b in bins}
alloc = {b: min(20, avail[b]) for b in bins}
while sum(alloc.values()) < 60:
    room = sorted([b for b in bins if alloc[b] < avail[b]], key=lambda b: (alloc[b], -avail[b]))
    if not room: break
    alloc[room[0]] += 1
l3r = []
for b in bins: l3r += rng.sample(cand[b], alloc[b])
with open(os.path.join(O, 'L3-R_muestra_probabilistica.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['rid', 'doi', 'year', 'title', 'E_bin_abstract', 'F', 'A', 'M', 'OWN', 'N_estrato', 'n_estrato'])
    for r in l3r: w.writerow([r['rid'], r['doi'], r['year'], r['title'], r['E_bin'], r['F'], r['A'], r['M'], int('OWN' in r['tags']), avail[r['E_bin']], alloc[r['E_bin']]])
blind = []
for dec in ('INCLUDE', 'UNCERTAIN', 'EXCLUDE'):
    cand = sorted([r for r in scr if r['decision'] == dec and r['rid'] not in dev and corp[r['rid']]['abstract']], key=lambda r: r['rid'])
    blind += rng.sample(cand, 20)
rng.shuffle(blind)
with open(os.path.join(O, 'MUESTRA_CIEGA_60_para_codificar.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['n', 'title', 'year', 'abstract', 'author_keywords', 'index_keywords', 'INCLUIR_si_no', 'F(F0-F8)', 'A(A1-A4)', 'M(M1-M6)', 'E_bin(sim/banco/fisico)'])
    for i, r in enumerate(blind, 1):
        c = corp[r['rid']]; w.writerow([i, c['title'], c['year'], c['abstract'], c['author_kw'], c['index_kw'], '', '', '', '', ''])
with open(os.path.join(O, 'NO_ABRIR_clave_muestra_ciega', 'CLAVE_muestra_ciega_NO_ABRIR_hasta_codificar.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['n', 'rid', 'doi', 'decision_regla', 'regla', 'F', 'A', 'M', 'E_bin'])
    for i, r in enumerate(blind, 1): w.writerow([i, r['rid'], r['doi'], r['decision'], r['rule'], r['F'], r['A'], r['M'], r['E_bin']])
info = dict(seed=SEED, pool_L3R=len(pool), avail_por_bin=avail, asignacion=alloc, L3R_n=len(l3r), dev_set_n=len(dev), blind_n=len(blind),
            L3R_OWN=sum('OWN' in r['tags'] for r in l3r), blind_OWN=sum('OWN' in r['tags'] for r in blind))
json.dump(info, open(os.path.join(O, 'MUESTRAS_info.json'), 'w'), indent=1); print(info)
