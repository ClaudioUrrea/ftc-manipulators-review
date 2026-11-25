"""RS3-H ronda 2 (enmienda 1.8 del protocolo, 24-11-2026): sorteo de la segunda muestra ciega de validacion.
Marco: estudios primarios (capa P) con decision de regla INCLUDE bajo v1.8, 2016-2026, con resumen, no retractados; se excluyen el conjunto
de desarrollo (known items Actuators, 200 primeros por fecha, titulos inspeccionados en la auditoria), la muestra de la ronda 1, todos los
registros de L3 (L3-R, L3-P y reemplazos; la reserva L3-P es un ranking de todo el marco y no se excluye) y los registros del autor (OWN).
Estratos: primer codigo A de regla (v1.8) o A-NR. Asignacion fija A1 15, A2 15, A3 10, A4 10, A-NR 10; deficit a A1 y luego a A2. Semilla 20261124.
Salidas: hoja para codificar (CSV y XLSX, sin index keywords) y clave en NO_ABRIR_clave_ronda2 (no abrir hasta entregar la hoja y la declaracion).
Uso: python3 -I rs3h2_muestra.py <carpeta_05> <carpeta_DATOS> <carpeta_RS2> <carpeta_RS3>"""
import csv, json, os, random, sys
csv.field_size_limit(10**9)
P5, DD, R2, R3 = sys.argv[1:5]; SEED = 20261124
ALLOC = {'A1': 15, 'A2': 15, 'A3': 10, 'A4': 10, 'A-NR': 10}
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(DD, 'CORPUS_RS2.csv'), encoding='utf-8'))}
scr = list(csv.DictReader(open(os.path.join(DD, 'SCREEN_RS2.csv'), encoding='utf-8')))
known = {r['doi'].lower() for r in csv.DictReader(open(os.path.join(P5, 'KNOWN_ITEMS_ACTUATORS.csv'), encoding='utf-8'))}
first200 = {r['rid'] for r in sorted(scr, key=lambda r: (r['year'] or '9999', r['rid']))[:200]}
insp = {r['rid'] for r in csv.DictReader(open(os.path.join(DD, 'DEV_inspeccionados_auditoria.csv'), encoding='utf-8'))}
dev = {r['rid'] for r in scr if r['doi'] in known} | first200 | insp
r1 = {r['rid'] for r in csv.DictReader(open(os.path.join(R2, 'NO_ABRIR_clave_muestra_ciega', 'CLAVE_muestra_ciega_NO_ABRIR_hasta_codificar.csv'), encoding='utf-8-sig'))}
l3 = {r['rid'] for r in csv.DictReader(open(os.path.join(R3, 'L3_LISTA_120.csv'), encoding='utf-8-sig'))}
l3 |= {r['replacement'] for r in csv.DictReader(open(os.path.join(R3, 'REEMPLAZOS_L3P.csv'), encoding='utf-8-sig'))}
stratum = lambda r: r['A'].split(';')[0] if r['A'] else 'A-NR'
pool = sorted([r for r in scr if r['decision'] == 'INCLUDE' and r['layer'] == 'P' and '2016' <= r['year'] <= '2026'
               and corp[r['rid']]['abstract'] and 'RETRACTED' not in r['flags'] and 'OWN' not in r['tags']
               and r['rid'] not in dev | r1 | l3], key=lambda r: r['rid'])
cand = {s: [r for r in pool if stratum(r) == s] for s in ALLOC}
alloc = {s: min(ALLOC[s], len(cand[s])) for s in ALLOC}
for s in ('A1', 'A2'):
    while sum(alloc.values()) < 60 and alloc[s] < len(cand[s]): alloc[s] += 1
rng = random.Random(SEED); smp = []
for s in ALLOC: smp += rng.sample(cand[s], alloc[s])
rng.shuffle(smp)
O = os.path.join(R2, 'RS3-H_ronda2'); K = os.path.join(O, 'NO_ABRIR_clave_ronda2'); os.makedirs(K, exist_ok=True)
H = ['n', 'title', 'year', 'abstract', 'author_keywords', 'INCLUIR_si_no', 'F(F0-F8)', 'A(A1-A4)', 'M(M1-M6)', 'E_bin(sim/banco/fisico)', 'nota']
rows = [[i, corp[r['rid']]['title'], corp[r['rid']]['year'], corp[r['rid']]['abstract'], corp[r['rid']]['author_kw'], '', '', '', '', '', ''] for i, r in enumerate(smp, 1)]
with open(os.path.join(O, 'MUESTRA_RONDA2_60_para_codificar.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(H); w.writerows(rows)
with open(os.path.join(K, 'CLAVE_ronda2_NO_ABRIR_hasta_codificar.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['n', 'rid', 'doi', 'estrato_A', 'decision_regla', 'regla', 'F', 'A', 'M', 'E_bin', 'flags'])
    for i, r in enumerate(smp, 1): w.writerow([i, r['rid'], r['doi'], stratum(r), r['decision'], r['rule'], r['F'], r['A'], r['M'], r['E_bin'], r['flags']])
try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook(); ws = wb.active; ws.title = 'codificar'; ws.append(H)
    for row in rows: ws.append(row)
    for c, wd in zip('ABCDEFGHIJK', (5, 40, 7, 90, 30, 12, 12, 12, 12, 14, 30)): ws.column_dimensions[c].width = wd
    for cell in ws[1]: cell.font = Font(bold=True); cell.fill = PatternFill('solid', fgColor='DDEBF7')
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = 'F2'
    dv1 = DataValidation(type='list', formula1='"si,no"', allow_blank=True); dv2 = DataValidation(type='list', formula1='"sim,banco,fisico"', allow_blank=True)
    ws.add_data_validation(dv1); ws.add_data_validation(dv2); dv1.add('F2:F61'); dv2.add('J2:J61')
    wb.save(os.path.join(O, 'MUESTRA_RONDA2_60_para_codificar.xlsx'))
except ImportError:
    print('openpyxl no disponible: solo CSV')
info = dict(seed=SEED, marco=len(pool), disponibles={s: len(cand[s]) for s in ALLOC}, asignacion=alloc, n=len(smp),
            excluidos=dict(desarrollo=len(dev), ronda1=len(r1), L3=len(l3)))
json.dump(info, open(os.path.join(O, 'MUESTRA_RONDA2_info.json'), 'w'), indent=1); print(info)
