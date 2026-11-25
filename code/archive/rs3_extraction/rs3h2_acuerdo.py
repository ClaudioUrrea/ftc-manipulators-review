"""RS3-H ronda 2 (enmienda 1.8, fijado el 24-11-2026 antes de codificar): acuerdo entre la segunda codificacion ciega del autor y las reglas v1.8.
Ejecutar SOLO despues de que el autor entregue la hoja codificada y la declaracion escrita, y de congelar la hoja (SHA-256).
Primario: kappa de Cohen y AC1 de Gwet por codigo A (A1-A4, binario por codigo) en los registros que el autor incluye, con IC 95 % por bootstrap
estratificado por estrato A de regla (2000 replicas, semilla 20261125); estimaciones muestrales sin ponderar, con tamanos de estrato informados.
Secundario: F (por codigo), M (por codigo), E (3 bins); proporcion de registros INCLUDE de regla que el autor incluye (Wilson);
post hoc y rotulado: acuerdo de A en la ronda 1 recalculado con los codigos v1.8 de SCREEN_RS2.csv (la codificacion humana no cambia).
Regla de decision (protocolo s.7): si kappa A1 >= 0,60 y kappa A2 >= 0,60 -> cruce F x A de L1 con codigos v1.8 como primario; si no -> solo descriptivo.
Uso: python3 -I rs3h2_acuerdo.py <hoja_codificada.xlsx|csv> <clave_ronda2.csv> <hoja_ronda1_limpia.csv> <clave_ronda1.csv> <SCREEN_RS2.csv> <carpeta_salida>"""
import csv, json, math, os, random, re, sys
H, K, H1, K1, S, O = sys.argv[1:7]
COLS = ['n', 'INCLUIR_si_no', 'F(F0-F8)', 'A(A1-A4)', 'M(M1-M6)', 'E_bin(sim/banco/fisico)', 'nota']
def load_sheet(p):
    if p.lower().endswith('.xlsx'):
        from openpyxl import load_workbook
        ws = load_workbook(p, read_only=True, data_only=True).active; it = ws.iter_rows(values_only=True); hd = [str(h).strip() if h is not None else '' for h in next(it)]
        rows = [{hd[i]: ('' if v is None else str(v).strip()) for i, v in enumerate(r) if i < len(hd)} for r in it if r and r[0] not in (None, '')]
    else:
        rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
    for r in rows:
        r['n'] = str(int(float(r['n'])))
    return {r['n']: r for r in rows}
hum = load_sheet(H); key = {r['n']: r for r in csv.DictReader(open(K, encoding='utf-8-sig'))}
yes = lambda v: (v or '').strip().lower() in ('si', 'sí', 's', 'yes', 'y', '1', 'x', 'incluir')
codes = lambda v, p='FAM': set(re.findall(r'[%s]\d' % p, (v or '').upper()))
EBIN = {'sim': 'E0-E2', 'simulacion': 'E0-E2', 'simulación': 'E0-E2', 'banco': 'E3', 'fisico': 'E4', 'físico': 'E4'}
def kappa(a, b):
    n = len(a); cats = sorted(set(a) | set(b)); po = sum(x == y for x, y in zip(a, b)) / n
    pa = {c: a.count(c) / n for c in cats}; pb = {c: b.count(c) / n for c in cats}; pe = sum(pa[c] * pb[c] for c in cats); q = len(cats)
    k = (po - pe) / (1 - pe) if pe < 1 else float('nan')
    pi = {c: (pa[c] + pb[c]) / 2 for c in cats}; pe2 = sum(pi[c] * (1 - pi[c]) for c in cats) / (q - 1) if q > 1 else 0
    return po, k, ((po - pe2) / (1 - pe2) if pe2 < 1 else float('nan'))
def boot(pairs, strata, reps=2000, seed=20261125):
    rng = random.Random(seed); idx = {}
    for i, s in enumerate(strata): idx.setdefault(s, []).append(i)
    out = {'kappa': [], 'ac1': []}
    for _ in range(reps):
        sel = [rng.choice(v) for v in idx.values() for _ in v]; po, k, ac1 = kappa([pairs[i][0] for i in sel], [pairs[i][1] for i in sel])
        if not math.isnan(k): out['kappa'].append(k)
        if not math.isnan(ac1): out['ac1'].append(ac1)
    ci = lambda v: [round(sorted(v)[int(.025 * len(v))], 3), round(sorted(v)[int(.975 * len(v)) - 1], 3)] if v else [None, None]
    return {k: ci(v) for k, v in out.items()}
def report(name, pairs, strata):
    a = [p[0] for p in pairs]; b = [p[1] for p in pairs]; po, k, ac1 = kappa(a, b)
    return dict(dimension=name, n=len(pairs), positives_author=sum(x == 1 for x in a), positives_rule=sum(x == 1 for x in b),
                agreement=round(po, 3), kappa=None if math.isnan(k) else round(k, 3), ac1=None if math.isnan(ac1) else round(ac1, 3),
                ci95=boot(pairs, strata), kappa_below_0_60=(not math.isnan(k)) and k < 0.60)
def wilson(x, n, z=1.96):
    p = x / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(p, 3), round(c - h, 3), round(c + h, 3)]
ns = sorted(key, key=int); assert set(ns) == set(hum), 'la hoja y la clave no tienen los mismos n'
bad = [n for n in ns if {'A1', 'A2'} <= codes(hum[n]['A(A1-A4)'], 'A')]
inc = [n for n in ns if yes(hum[n]['INCLUIR_si_no'])]; st = [key[n]['estrato_A'] for n in inc]
res = []
for c in ('A1', 'A2', 'A3', 'A4'):
    res.append(report(f'A:{c} (primary)', [(int(c in codes(hum[n]['A(A1-A4)'], 'A')), int(c in codes(key[n]['A'], 'A'))) for n in inc], st))
for dim, col, p in (('F', 'F(F0-F8)', 'F'), ('M', 'M(M1-M6)', 'M')):
    for c in sorted(set().union(*[codes(key[n][dim], p) | codes(hum[n][col], p) for n in inc])):
        res.append(report(f'{dim}:{c}', [(int(c in codes(hum[n][col], p)), int(c in codes(key[n][dim], p))) for n in inc], st))
eb = [n for n in inc if hum[n]['E_bin(sim/banco/fisico)'].strip().lower() in EBIN]
if eb: res.append(report('E bin', [(EBIN[hum[n]['E_bin(sim/banco/fisico)'].strip().lower()], key[n]['E_bin']) for n in eb], [key[n]['estrato_A'] for n in eb]))
# post hoc: ronda 1 con codigos A v1.8
scr = {r['rid']: r for r in csv.DictReader(open(S, encoding='utf-8'))}
h1 = {r['n']: r for r in csv.DictReader(open(H1, encoding='utf-8-sig'))}; k1 = {r['n']: r for r in csv.DictReader(open(K1, encoding='utf-8-sig'))}
both1 = [n for n in k1 if yes(h1[n]['INCLUIR_si_no']) and k1[n]['F']]
post = [report(f'round1 A:{c} with v1.8 rules (post hoc)', [(int(c in codes(h1[n]['A(A1-A4)'], 'A')), int(c in codes(scr[k1[n]['rid']]['A'], 'A'))) for n in both1],
               [k1[n]['decision_regla'] for n in both1]) for c in ('A1', 'A2', 'A3', 'A4')]
kA = {r['dimension'].split()[0]: r['kappa'] for r in res[:2]}
decision = 'L1 F x A primary (v1.8 codes)' if all(v is not None and v >= 0.60 for v in kA.values()) else 'L1 F x A descriptive only; F x A statements rest on L3'
out = dict(n_coded=len(ns), n_included_by_author=len(inc), share_included=wilson(len(inc), len(ns)),
           strata_sample={s: sum(key[n]['estrato_A'] == s for n in ns) for s in ('A1', 'A2', 'A3', 'A4', 'A-NR')},
           author_A_empty=sum(1 for n in inc if not codes(hum[n]['A(A1-A4)'], 'A')), author_A1_A2_together=bad,
           by_dimension=res, round1_post_hoc=post, decision_rule=dict(kappa=kA, result=decision))
os.makedirs(O, exist_ok=True); json.dump(out, open(os.path.join(O, 'S10b_ronda2_agreement_results.json'), 'w'), indent=1, ensure_ascii=False)
with open(os.path.join(O, 'S10b_ronda2_agreement_table.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['dimension', 'n', 'agreement', 'kappa', 'kappa_ci95', 'ac1', 'ac1_ci95', 'kappa_below_0.60'])
    for r in res + post: w.writerow([r['dimension'], r['n'], r['agreement'], r['kappa'], r['ci95']['kappa'], r['ac1'], r['ci95']['ac1'], r['kappa_below_0_60']])
print(json.dumps({k: v for k, v in out.items() if k not in ('by_dimension', 'round1_post_hoc')}, ensure_ascii=False, indent=1))
