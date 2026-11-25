"""RS3 paso 2b: estimacion de registros en alcance en S08sup (INCLUDE, capa P) a partir del juicio de 40 resumenes.
Proporcion con intervalo de Wilson 95 %; total = N * p (cota inferior IN; cota superior IN + UNCLEAR). Relativo a los INCLUDE primarios del corpus.
Uso: python3 -I rs3_s08sup_estimate.py <carpeta_DATOS> <carpeta_RS3>"""
import csv, json, math, os, sys
D, O = sys.argv[1:3]
def wilson(x, n, z=1.96):
    p = x / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(p, 3), round(c - h, 3), round(c + h, 3)
smp = {r['k']: r for r in csv.DictReader(open(os.path.join(O, 'S08sup_MUESTRA_40.csv'), encoding='utf-8'))}
jud = list(csv.DictReader(open(os.path.join(O, 'S08sup_JUICIO_40.csv'), encoding='utf-8')))
sup = json.load(open(os.path.join(D, 'CONTEOS_supplementary_RS2.json')))['S08sup']; scr = json.load(open(os.path.join(D, 'CONTEOS_screen_RS2.json')))
res = {}
for lab, yr, N, base in (('todos_anos', ('0', '9999'), sup['include_primary'], scr['include_primary']),
                         ('2016_2026', ('2016', '2026'), sup['include_primary_2016_2026'], scr['include_primary_2016_2026'])):
    js = [j for j in jud if yr[0] <= smp[j['k']]['year'] <= yr[1]]; n = len(js)
    x_in = sum(j['juicio'] == 'IN' for j in js); x_up = x_in + sum(j['juicio'] == 'UNCLEAR' for j in js)
    p, lo, hi = wilson(x_in, n); pu, lou, hiu = wilson(x_up, n)
    res[lab] = dict(N_include_primary_S08sup=N, n_read=n, IN=x_in, IN_plus_UNCLEAR=x_up, p_IN_wilson=[p, lo, hi], p_upper_wilson=[pu, lou, hiu],
                    est_in_scope=[round(N * p, 1), round(N * lo, 1), round(N * hi, 1)], est_upper=round(N * pu, 1),
                    pct_of_main_include_primary=[round(100 * N * p / base, 1), round(100 * N * lo / base, 1), round(100 * N * hi / base, 1)],
                    pct_upper=round(100 * N * hiu / base, 1), main_include_primary=base)
json.dump(res, open(os.path.join(O, 'CONTEOS_S08sup_estimacion_RS3.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
