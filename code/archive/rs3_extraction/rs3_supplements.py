"""RS3 paso 4: tablas suplementarias desde los datos (se regeneran al avanzar la extraccion).
S2 cadenas exactas con fecha y conteo; S3 conteos del diagrama PRISMA 2020; S4 exclusiones a texto completo (desde S5);
S6 corpus L1 con codigos (contiene las decisiones de regla: se escribe en NO_ABRIR_hasta_codificar_RS3-H hasta cerrar la ronda 2 de RS3-H, enmienda v1.8).
Uso: python3 -I rs3_supplements.py <carpeta_RS1(05)> <carpeta_E2a(02)> <carpeta_DATOS> <carpeta_RS3>"""
import csv, json, os, re, sys
csv.field_size_limit(10**9)
P, B, D, O = sys.argv[1:5]; DATE = '2026-11-15'
brecha = open(os.path.join(B, 'BRECHA_WOS.md'), encoding='utf-8').read().split('## RS2', 1)[1]
counts = {}
for m in re.finditer(r'^\| (S?F\d\d\w*) \|(?: #\d+[^|]*\|)? (\d+) \|', brecha, re.M): counts.setdefault(m.group(1), int(m.group(2)))
for code, pat in (('SF01e-complemento', r'SF01e-complemento \(no ingl[eé]s\) = (\d+)'), ('SF08sup', r'SF08sup \(t[eé]rminos[^)]*\) = (\d+)')):
    counts[code] = int(re.search(pat, brecha).group(1))
def strings(fn, db):
    L = open(os.path.join(P, fn), encoding='utf-8').read().splitlines(); out = []
    for i, l in enumerate(L):
        m = re.match(r'^(S?F\d\d\w*(?:-complemento)?) (.*)$', l)
        if not m or m.group(1) not in counts or any(o[0] == m.group(1) for o in out): continue
        head, s = m.group(2), ''
        if head.rstrip().endswith(':') and i + 1 < len(L) and L[i + 1].strip(): s = L[i + 1].strip()
        elif ':' in head: purpose, s = head.split(':', 1); head = purpose
        out.append((m.group(1), db, head.rstrip(': ').strip(), s.strip()))
    return out
rows = strings('CADENAS_DEFINITIVAS_WOS.txt', 'WoS CC') + strings('CADENAS_DEFINITIVAS_SCOPUS.txt', 'Scopus')
EN = {'F01': 'Main corpus (all years; exported in full)', 'SF01': 'Main corpus (all years; exported in full)',
      'F01e': 'Effect of the language filter: F01 without the language limit', 'SF01e': 'Effect of the language filter: SF01 without the language limit',
      'F02': 'Diagnosis-term complement (count and sample only)', 'SF02': 'Diagnosis-term complement (count and sample only)',
      'F02c': 'Diagnosis records not retrieved by F01 (random sample of 100 inspected)', 'SF02c': 'Diagnosis records not retrieved by SF01',
      'F03': "Records by the review's author within F01 (tag OWN)", 'F04': 'Records of Actuators within F01 (known-item control)', 'SF04': 'Records of Actuators within SF01 (known-item control)',
      'F04s': 'Records of the target journal (Sensors) within F01', 'SF04s': 'Records of the target journal (Sensors) within SF01',
      'F05': 'Reviews within F01 (layer R)', 'SF05': 'Reviews within SF01 (layer R)', 'F06': 'Seed-review known-item test', 'SF06': 'Seed-review known-item test',
      'F07': 'Size of the multi-robot exclusion (EX-SCOPE)', 'SF07': 'Size of the multi-robot exclusion (EX-SCOPE)',
      'SF01e-complemento': 'Non-English complement of SF01 (screened with the same rules; listed in the supplement)',
      'SF08sup': 'Post hoc query with manipulator terms missing from SF01 (found by snowballing); bounds the loss due to the string'}
sf01 = next(r[3] for r in rows if r[0] == 'SF01'); blocks = re.findall(r'TITLE-ABS-KEY\((?:[^()]|\([^()]*\))*\)', sf01); FB, MB = blocks[0], blocks[1]
def clean(c, s):
    s = s.split('->')[0].strip().rstrip('.')
    s = s.replace('F01 sin "AND LA=(English)"', 'F01 without "AND LA=(English)"').replace('SF01 sin "AND LANGUAGE(english)"', 'SF01 without "AND LANGUAGE(english)"')
    s = s.replace('bloque de manipulador de SF01', MB).replace('bloque de manipulador', MB).replace('bloque de falla', FB)
    s = re.sub(r'\. Exportar solo una muestra.*$', '', s)
    return s.replace('(SF01) AND ISSN', '(#SF01) AND ISSN')
rows = [(c, db, EN[c], clean(c, s)) for c, db, h, s in rows]
role = lambda c: 'main corpus' if c in ('F01', 'SF01') else ('complementary set (screened, not merged)' if c in ('SF01e-complemento', 'SF08sup') else 'control (count only)')
with open(os.path.join(O, 'S2_search_strings.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['code', 'database', 'role', 'purpose_or_derivation', 'string_or_combination', 'executed', 'count'])
    for c, db, h, s in rows: w.writerow([c, db, role(c), h, s, DATE, counts[c]])
missing = sorted(set(counts) - {r[0] for r in rows})
# S3 PRISMA
J = lambda n: json.load(open(os.path.join(D, n)))
dd, sc, sb, sup = J('CONTEOS_dedup_RS2.json'), J('CONTEOS_screen_RS2.json'), J('CONTEOS_snowball_RS2.json'), J('CONTEOS_supplementary_RS2.json')
s5 = list(csv.DictReader(open(os.path.join(O, 'EXTRACCION_L3_S5.csv'), encoding='utf-8')))
ft = lambda pred: sum(1 for r in s5 if pred(r))
prisma = [('identification', 'Records identified: Web of Science Core Collection (F01)', dd['wos_records']),
          ('identification', 'Records identified: Scopus (SF01)', dd['scopus_records']),
          ('identification', 'Duplicate records removed', dd['identified'] - dd['unique']),
          ('identification', 'Other methods: snowball records (OpenAlex, backward and forward, unique)', sb['unique_snowball']),
          ('identification', 'Other methods: reviews added to layer R (Zenteno 2021, Urrea 2025, Maican 2025)', 3),
          ('screening', 'Records screened (title, abstract, author keywords; scripted rules)', sc['n'])]
prisma += [('screening', f'Records excluded: {k}', v) for k, v in sorted(sc['exclude_by_rule'].items(), key=lambda x: -x[1])]
prisma += [('screening', 'Records UNCERTAIN (flagged residue; not in L1; added in a sensitivity analysis, amendment 1.9)', sc['decision']['UNCERTAIN']),
           ('included', 'Mapping set L1: INCLUDE primary studies (all years)', sc['include_primary']),
           ('included', 'Layer R: reviews retrieved by the strings', sc['include_layer_R']),
           ('included', 'L1 primary studies 2016-2026 (synthesis window)', sc['include_primary_2016_2026']),
           ('eligibility', 'Reports sought for retrieval (L3 = L3-R + L3-P)', len(s5)),
           ('eligibility', 'Reports not retrieved', ft(lambda r: r['status'] == 'no_access')),
           ('eligibility', 'Reports assessed for eligibility (full text read)', ft(lambda r: r['ft_eligible'] in ('yes', 'no'))),
           ('eligibility', 'Reports excluded at full text', ft(lambda r: r['ft_eligible'] == 'no')),
           ('included', 'Studies included in the synthesis set (full text eligible)', ft(lambda r: r['ft_eligible'] == 'yes')),
           ('supplementary', 'Non-English complement (SF01e-complemento): records / INCLUDE by rules', f"{sup['S01e']['n']} / {sup['S01e']['include_primary']}"),
           ('supplementary', 'Missing-term set (SF08sup): records / INCLUDE primary by rules', f"{sup['S08sup']['n']} / {sup['S08sup']['include_primary']}")]
with open(os.path.join(O, 'S3_PRISMA_counts.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['phase', 'box', 'n']); w.writerows(prisma)
with open(os.path.join(O, 'S4_fulltext_exclusions.csv'), 'w', newline='', encoding='utf-8') as f:
    LAB = {'EX-PLAT': 'Other platform', 'IC2': 'No actuator or joint fault model', 'EX-FDI': 'Diagnosis without accommodation',
           'EX-HW': 'Design without a control law', 'EX-FAULT': 'Fault type outside scope', 'EX-SCOPE': 'Multi-robot team fault tolerance',
           'IC1': 'Not a manipulator', 'IC3': 'No accommodation', 'EX-TYPE': 'Not a primary article'}
    def lab(r):  # rule (d) of amendment 1.10 is recorded in the extraction notes
        if r['ft_exclusion'] == 'EX-HW' and 'rule (d)' in r.get('notes', ''):
            return 'Fault-tolerant configuration without a defined post-failure behavior (rule (d), amendment 1.10)'
        return LAB.get(r['ft_exclusion'], r['ft_exclusion'])
    w = csv.writer(f); w.writerow(['rid', 'sample', 'doi', 'year', 'first_author', 'title', 'reason', 'reason_text', 'replaced_by'])
    for r in s5:
        if r['ft_eligible'] == 'no': w.writerow([r['rid'], r['sample'], r['doi'], r['year'], r['first_author'], r['title'], r['ft_exclusion'], lab(r), r['replaced_by']])
scr = list(csv.DictReader(open(os.path.join(D, 'SCREEN_RS2.csv'), encoding='utf-8')))
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8'))}
with open(os.path.join(O, 'NO_ABRIR_hasta_codificar_RS3-H', 'S6_L1_corpus_codes.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['rid', 'source', 'doi', 'year', 'first_author', 'title', 'journal', 'doctype', 'layer', 'decision', 'rule', 'F', 'A', 'M', 'E_bin', 'tags', 'flags'])
    for r in scr:
        c = corp[r['rid']]; w.writerow([r['rid'], r['src'], r['doi'], r['year'], c['authors'].split(';')[0].strip(), r['title'], r['journal'], c['doctype'], r['layer'], r['decision'], r['rule'], r['F'], r['A'], r['M'], r['E_bin'], r['tags'], r['flags']])
print('S2', len(rows), 'cadenas; sin cadena:', missing, '| S3', len(prisma), 'casillas | S4', ft(lambda r: r['ft_eligible'] == 'no'), '| S6', len(scr))
