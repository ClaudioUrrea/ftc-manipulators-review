"""RS3-H: acuerdo entre la codificacion ciega del autor y las reglas (Supplementary File S10). Ejecutar SOLO despues de que el autor
entregue su hoja codificada y confirme por escrito que codifico sin herramientas y sin la clave.
Por dimension: acuerdo bruto, kappa de Cohen y AC1 de Gwet, con IC 95 % por bootstrap estratificado por decision de regla (2000 reps, semilla 20261120).
Inclusion: autor si/no frente a regla INCLUDE (y, como sensibilidad, INCLUDE o UNCERTAIN). Precision de INCLUDE, VPN de EXCLUDE y prevalencia en UNCERTAIN
con intervalo de Wilson; total en alcance estimado = sum N_h * p_h (N_h de SCREEN_RS2.csv). Codigos F, A, M (binario por codigo) y E (3 bins):
en los registros que el autor incluye y que tienen codigos de regla.
Uso: python3 -I rs3h_acuerdo.py <hoja_codificada.csv> <clave.csv> <SCREEN_RS2.csv> <carpeta_salida>"""
import csv, json, math, os, random, re, sys
H, K, S, O = sys.argv[1:5]
hum = {r['n']: r for r in csv.DictReader(open(H, encoding='utf-8-sig'))}
key = {r['n']: r for r in csv.DictReader(open(K, encoding='utf-8-sig'))}
N = {}
for r in csv.DictReader(open(S, encoding='utf-8')): N[r['decision']] = N.get(r['decision'], 0) + 1
yes = lambda v: v.strip().lower() in ('si', 'sí', 's', 'yes', 'y', '1', 'x', 'incluir')
codes = lambda v: set(re.findall(r'[FAM]\d', (v or '').upper()))
EBIN = {'sim': 'E0-E2', 'simulacion': 'E0-E2', 'simulación': 'E0-E2', 'banco': 'E3', 'fisico': 'E4', 'físico': 'E4', 'e0-e2': 'E0-E2', 'e3': 'E3', 'e4': 'E4'}
def kappa(a, b):
    n = len(a); cats = sorted(set(a) | set(b)); po = sum(x == y for x, y in zip(a, b)) / n
    pa = {c: a.count(c) / n for c in cats}; pb = {c: b.count(c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats); q = len(cats)
    k = (po - pe) / (1 - pe) if pe < 1 else float('nan')
    pi = {c: (pa[c] + pb[c]) / 2 for c in cats}; pe2 = sum(pi[c] * (1 - pi[c]) for c in cats) / (q - 1) if q > 1 else 0
    ac1 = (po - pe2) / (1 - pe2) if pe2 < 1 else float('nan')
    return po, k, ac1
def boot(pairs, strata, reps=2000, seed=20261120):
    rng = random.Random(seed); idx = {}
    for i, s in enumerate(strata): idx.setdefault(s, []).append(i)
    out = {'po': [], 'kappa': [], 'ac1': []}
    for _ in range(reps):
        sel = [rng.choice(v) for v in idx.values() for _ in v]; a = [pairs[i][0] for i in sel]; b = [pairs[i][1] for i in sel]
        po, k, ac1 = kappa(a, b)
        for n_, v in (('po', po), ('kappa', k), ('ac1', ac1)):
            if not math.isnan(v): out[n_].append(v)
    ci = lambda v: [round(sorted(v)[int(.025 * len(v))], 3), round(sorted(v)[int(.975 * len(v)) - 1], 3)] if v else [None, None]
    return {k: ci(v) for k, v in out.items()}
def wilson(x, n, z=1.96):
    if n == 0: return [None, None, None]
    p = x / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(p, 3), round(c - h, 3), round(c + h, 3)]
def report(name, pairs, strata):
    a = [p[0] for p in pairs]; b = [p[1] for p in pairs]; po, k, ac1 = kappa(a, b)
    return dict(dimension=name, n=len(pairs), prevalence_author=round(sum(x in (1, 'E4', 'E3') for x in a) / len(a), 3) if pairs else None,
                agreement=round(po, 3), kappa=round(k, 3), ac1=round(ac1, 3), ci95=boot(pairs, strata), kappa_below_0_60=k < 0.60)
ns = sorted(key, key=int); assert set(ns) == set(hum), 'la hoja y la clave no tienen los mismos n'
res = []
inc = [(int(yes(hum[n]['INCLUIR_si_no'])), int(key[n]['decision_regla'] == 'INCLUDE')) for n in ns]; st = [key[n]['decision_regla'] for n in ns]
res.append(report('inclusion (rule INCLUDE)', inc, st))
res.append(report('inclusion (rule INCLUDE or UNCERTAIN)', [(int(yes(hum[n]['INCLUIR_si_no'])), int(key[n]['decision_regla'] != 'EXCLUDE')) for n in ns], st))
strat = {}
for d in ('INCLUDE', 'UNCERTAIN', 'EXCLUDE'):
    m = [n for n in ns if key[n]['decision_regla'] == d]; x = sum(yes(hum[n]['INCLUIR_si_no']) for n in m); strat[d] = dict(n=len(m), author_include=x, p_wilson=wilson(x, len(m)), N_h=N.get(d, 0))
est = sum(v['N_h'] * v['p_wilson'][0] for v in strat.values() if v['p_wilson'][0] is not None)
both = [n for n in ns if yes(hum[n]['INCLUIR_si_no']) and key[n]['F']]
for dim, col in (('F', 'F(F0-F8)'), ('A', 'A(A1-A4)'), ('M', 'M(M1-M6)')):
    allc = sorted(set().union(*[codes(key[n][dim]) | codes(hum[n][col]) for n in both])) if both else []
    for c in allc: res.append(report(f'{dim}:{c}', [(int(c in codes(hum[n][col])), int(c in codes(key[n][dim]))) for n in both], [key[n]['decision_regla'] for n in both]))
eb = [n for n in both if hum[n]['E_bin(sim/banco/fisico)'].strip().lower() in EBIN]
if eb: res.append(report('E bin', [(EBIN[hum[n]['E_bin(sim/banco/fisico)'].strip().lower()], key[n]['E_bin']) for n in eb], [key[n]['decision_regla'] for n in eb]))
out = dict(by_dimension=res, by_rule_stratum=strat, precision_INCLUDE=strat['INCLUDE']['p_wilson'], npv_EXCLUDE=(None if strat['EXCLUDE']['p_wilson'][0] is None else [round(1 - strat['EXCLUDE']['p_wilson'][0], 3), round(1 - strat['EXCLUDE']['p_wilson'][2], 3), round(1 - strat['EXCLUDE']['p_wilson'][1], 3)]),
           est_in_scope_total=round(est, 1), n_coded=len(ns), n_codes_compared=len(both))
os.makedirs(O, exist_ok=True); json.dump(out, open(os.path.join(O, 'S10_agreement_results.json'), 'w'), indent=1)
with open(os.path.join(O, 'S10_agreement_table.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['dimension', 'n', 'agreement', 'kappa', 'kappa_ci95', 'ac1', 'ac1_ci95', 'kappa_below_0.60'])
    for r in res: w.writerow([r['dimension'], r['n'], r['agreement'], r['kappa'], r['ci95']['kappa'], r['ac1'], r['ci95']['ac1'], r['kappa_below_0_60']])
print(json.dumps({k: v for k, v in out.items() if k != 'by_dimension'}, indent=1)); print(len(res), 'dimensiones')
