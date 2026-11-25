"""RS2 auditoria: recall con juicio manual de alcance sobre las perdidas (JUICIO_MANUAL_perdidas.csv, hecho por lectura de titulo y resumen).
Numerador sin cambio (registros snowball INCLUDE por regla que estan en el corpus); denominador = numerador + perdidas juzgadas en alcance.
Uso: python3 -I rs2_recall_manual.py <carpeta_DATOS> <carpeta_RS2>"""
import csv, json, math, os, sys
D, O = sys.argv[1:3]
J = list(csv.DictReader(open(os.path.join(O, 'JUICIO_MANUAL_perdidas.csv'), encoding='utf-8')))
L = list(csv.DictReader(open(os.path.join(D, 'PERDIDAS_RECALL_RS2.csv'), encoding='utf-8')))
for r in L:
    m = [j for j in J if (r['title'] or '').lower().startswith(j['clave_titulo'].lower())]
    assert len(m) == 1, r['title']
    r['juicio_manual'], r['causa'] = m[0]['juicio'], m[0]['causa']
with open(os.path.join(D, 'PERDIDAS_RECALL_RS2.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, list(L[0].keys())); w.writeheader(); w.writerows(L)
S = [r for r in csv.DictReader(open(os.path.join(D, 'SNOWBALL_RS2.csv'), encoding='utf-8')) if r['decision'] == 'INCLUDE' and r['has_abstract'] == '1']
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round(p, 3), round((c - h) / d, 3), round((c + h) / d, 3)]
res = {}
for lab, f in (('todos_anos', lambda y: True), ('2016_2026', lambda y: '2016' <= y <= '2026')):
    k = sum(1 for r in S if r['in_corpus'] == '1' and f(r['year'])); raw = sum(1 for r in S if f(r['year']))
    lost = [r for r in L if f(r['year']) and r['juicio_manual'] == 'en alcance']
    by = {}
    for r in lost: c = r['causa'].split(':')[0].split(' (')[0]; by[c] = by.get(c, 0) + 1
    res[lab] = dict(recall_reglas=[k, raw] + wilson(k, raw), perdidas_revisadas=raw - k, perdidas_en_alcance=len(lost), por_causa=by,
                    recall_juicio_manual=[k, k + len(lost)] + wilson(k, k + len(lost)),
                    recall_solo_cadena=[k, k + by.get('cadena', 0)] + wilson(k, k + by.get('cadena', 0)))
json.dump(res, open(os.path.join(D, 'CONTEOS_recall_manual_RS2.json'), 'w'), indent=1, ensure_ascii=False); print(json.dumps(res, ensure_ascii=False, indent=1))
