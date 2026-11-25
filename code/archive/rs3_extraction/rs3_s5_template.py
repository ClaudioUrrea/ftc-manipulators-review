"""RS3 paso 3: crea o completa la tabla de extraccion de L3 (Supplementary Table S5), una fila por registro de L3_LISTA_120.csv.
Idempotente: si EXTRACCION_L3_S5.csv existe, conserva lo extraido y solo agrega filas que falten. Campos: S5_DICCIONARIO.md.
Uso: python3 -I rs3_s5_template.py <carpeta_DATOS> <carpeta_RS3>"""
import csv, os, sys
csv.field_size_limit(10**9)
D, O = sys.argv[1:3]
COLS = ['rid', 'sample', 'selection', 'weight', 'doi', 'url', 'year', 'journal', 'first_author', 'title', 'OWN',
        'F_abs', 'A_abs', 'M_abs', 'E_bin_abs', 'status', 'access', 'ft_eligible', 'ft_exclusion', 'replaced_by',
        'M_ft', 'dof', 'robot_model', 'F_ft', 'F4_sub', 'fault_equation', 'normal_form_fit', 'fault_magnitude', 'onset', 'profile',
        'n_simultaneous', 'faulty_channels', 'A_primary', 'A_all', 'mechanism', 'stability', 'sensing', 'fault_info', 'detection_delay',
        'structural_condition', 'E_ft', 'platform', 'injection', 'baselines', 'metric', 'm_nominal', 'm_fault_noFTC', 'm_fault_FTC',
        'repetitions', 'code_data', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R_score',
        'T_ML', 'T_DT', 'T_OPEN', 'T_BENCH', 'notes', 'extracted_on']
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8'))}
lst = list(csv.DictReader(open(os.path.join(O, 'L3_LISTA_120.csv'), encoding='utf-8')))
path = os.path.join(O, 'EXTRACCION_L3_S5.csv')
old = {r['rid']: r for r in csv.DictReader(open(path, encoding='utf-8'))} if os.path.exists(path) else {}
rows = []
for r in lst:
    if r['rid'] in old: rows.append({c: old[r['rid']].get(c, '') for c in COLS}); continue
    a = corp[r['rid']]['authors'].split(';')[0].strip()
    rows.append({c: '' for c in COLS} | {k: r[k] for k in ('rid', 'sample', 'selection', 'weight', 'doi', 'url', 'year', 'journal', 'title', 'OWN', 'F_abs', 'A_abs', 'M_abs', 'E_bin_abs')}
                | dict(first_author=a, status='pending'))
with open(path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
print(len(rows), 'filas;', sum(r['status'] == 'done' for r in rows), 'extraidas;', sum(r['status'] == 'pending' for r in rows), 'pendientes')
