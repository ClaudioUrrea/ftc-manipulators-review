"""RS3 paso 1: L3-P (muestra intencional, protocolo v1.5 s.8) y lista L3 unificada (L3-R + L3-P).
Pool: INCLUDE, capa P, 2016-2026, sin NO-ABS ni RETRACTED; fuera L3-R y fuera los registros de la hoja de codificacion ciega
(para que la tabla de extraccion no muestre codigos de esos registros antes de RS3-H). Citas por anio = cited_by / (2027 - anio).
Orden: (1) en cada celda F x A no vacia (etiquetas multiples -> todas las parejas), el registro con mas citas por anio
(si ya fue elegido, la celda queda cubierta); (2) todos los elegibles de la revista objetivo (Sensors); (3) siguientes por citas por anio hasta 60.
Desempate: rid. Los registros L3-R que estan en la hoja ciega se apartan en NO_ABRIR_hasta_codificar_RS3-H (se extraen despues de RS3-H).
Uso: python3 -I rs3_l3p.py <carpeta_DATOS> <carpeta_RS2> <carpeta_RS3>"""
import csv, os, re, sys, itertools, json
csv.field_size_limit(10**9)
D, R2, O = sys.argv[1:4]; TARGET = 'SENSORS'; N_P = 60
norm = lambda t: re.sub(r'[^a-z0-9]', '', t.lower())
scr = list(csv.DictReader(open(os.path.join(D, 'SCREEN_RS2.csv'), encoding='utf-8')))
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8'))}
l3r = list(csv.DictReader(open(os.path.join(R2, 'L3-R_muestra_probabilistica.csv'), encoding='utf-8')))
blind_t = {norm(r['title']) for r in csv.DictReader(open(os.path.join(R2, 'MUESTRA_CIEGA_60_para_codificar.csv'), encoding='utf-8'))}
l3r_ids = {r['rid'] for r in l3r}
cpy = lambda r: int(r['cited_by'] or 0) / (2027 - int(r['year']))
pool = [r for r in scr if r['decision'] == 'INCLUDE' and r['layer'] == 'P' and '2016' <= r['year'] <= '2026'
        and 'NO-ABS' not in r['flags'] and 'RETRACTED' not in r['flags'] and r['rid'] not in l3r_ids and norm(r['title']) not in blind_t]
rank = sorted(pool, key=lambda r: (-cpy(r), r['rid']))
cells = {}
for r in rank:
    for f, a in itertools.product(r['F'].split(';'), r['A'].split(';')):
        cells.setdefault((f, a), r)            # primero en el orden = mas citas por anio
sel, why = [], {}
def add(r, w):
    if r['rid'] in why: why[r['rid']] += ';' + w
    else: sel.append(r); why[r['rid']] = w
for (f, a), r in sorted(cells.items()): add(r, f'cell:{f}x{a}')
for r in rank:
    if r['journal'].upper() == TARGET: add(r, 'target_journal')
for r in rank:
    if len(sel) >= N_P: break
    if r['rid'] not in why: add(r, 'fill_cites_per_year')
hold = [r for r in l3r if norm(r['title']) in blind_t]
hold_ids = {r['rid'] for r in hold}
cols = ['rid', 'sample', 'selection', 'doi', 'url', 'year', 'journal', 'title', 'cited_by', 'cites_per_year', 'F_abs', 'A_abs', 'M_abs', 'E_bin_abs', 'OWN', 'N_stratum', 'n_stratum', 'weight']
def row(r, sample, selection, N='', n=''):
    s = next(x for x in scr if x['rid'] == r['rid'])
    w = round(int(N) / int(n), 4) if N else ''
    return dict(rid=s['rid'], sample=sample, selection=selection, doi=s['doi'], url=('https://doi.org/' + s['doi']) if s['doi'] else '',
                year=s['year'], journal=s['journal'], title=s['title'], cited_by=s['cited_by'], cites_per_year=round(cpy(s), 2),
                F_abs=s['F'], A_abs=s['A'], M_abs=s['M'], E_bin_abs=s['E_bin'], OWN=int('OWN' in s['tags']), N_stratum=N, n_stratum=n, weight=w)
with open(os.path.join(O, 'L3-P_muestra_intencional.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader()
    for r in sel: w.writerow(row(r, 'L3-P', why[r['rid']]))
with open(os.path.join(O, 'L3_LISTA_120.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cols); w.writeheader()
    for r in l3r: w.writerow(row(r, 'L3-R', 'random_stratified_seed20261116', r['N_estrato'], r['n_estrato']))
    for r in sel: w.writerow(row(r, 'L3-P', why[r['rid']]))
with open(os.path.join(O, 'NO_ABRIR_hasta_codificar_RS3-H', 'HOLD_L3R_en_hoja_ciega.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['rid']); [w.writerow([r['rid']]) for r in hold]
# Reserva (enmienda v1.6): reemplazo determinista de exclusiones a texto completo en L3-P. Una seleccion por celda se reemplaza por el
# siguiente registro del orden que tenga esa celda; una de relleno, por el siguiente no elegido; la revista objetivo no se reemplaza.
with open(os.path.join(O, 'L3-P_reserva.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['rank', 'rid', 'cites_per_year', 'cells', 'journal', 'year', 'title'])
    for i, r in enumerate(rank, 1):
        if r['rid'] in why: continue
        w.writerow([i, r['rid'], round(cpy(r), 2), ';'.join(f + 'x' + a for f, a in itertools.product(r['F'].split(';'), r['A'].split(';'))), r['journal'], r['year'], r['title']])
info = dict(pool_L3P=len(pool), cells_nonempty=len(cells), cells_distinct_records=len({r['rid'] for r in cells.values()}),
            target_journal_eligible=sum(r['journal'].upper() == TARGET for r in pool), L3P_n=len(sel),
            by_reason={k: sum(why[r['rid']].split(';')[0].startswith(k) for r in sel) for k in ('cell', 'target', 'fill')},
            L3P_OWN=sum('OWN' in r['tags'] for r in sel), L3R_held_until_RS3H=len(hold), L3_total=len(l3r) + len(sel),
            L3P_E_bin={b: sum(r['E_bin'] == b for r in sel) for b in ('E0-E2', 'E3', 'E4')})
json.dump(info, open(os.path.join(O, 'L3P_info.json'), 'w'), indent=1); print(info)
