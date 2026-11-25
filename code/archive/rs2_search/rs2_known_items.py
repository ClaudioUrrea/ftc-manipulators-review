"""RS2 paso 3: pruebas de known-items (protocolo s.6) sobre CORPUS_RS2.csv y SCREEN_RS2.csv.
Uso: python3 -I rs2_known_items.py <carpeta_05> <carpeta_DATOS>   Salida: KNOWN_ITEMS_RESULT_RS2.csv"""
import csv, os, re, sys, glob
csv.field_size_limit(10**9)
P, D = sys.argv[1], sys.argv[2]
corp = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8'))}
scr = {r['rid']: r for r in csv.DictReader(open(os.path.join(D, 'SCREEN_RS2.csv'), encoding='utf-8'))}
bydoi = {r['doi']: k for k, r in corp.items() if r['doi']}
out = []
print('== Actuators known items (esperado vs regla) ==')
for r in csv.DictReader(open(os.path.join(P, 'KNOWN_ITEMS_ACTUATORS.csv'), encoding='utf-8')):
    k = bydoi.get(r['doi'].lower())
    if not k:
        out.append(dict(test='ACT', key=r['doi'], expected=r['expected'], retrieved='NO', src='', decision='', rule='')); print(r['doi'], r['expected'], 'NO RECUPERADO'); continue
    s = scr[k]
    out.append(dict(test='ACT', key=r['doi'], expected=r['expected'], retrieved='SI', src=corp[k]['src'], decision=s['decision'], rule=s['rule']))
    print(r['doi'], r['expected'], '->', corp[k]['src'], s['decision'], s['rule'], s['F'], s['A'], s['M'], s['E_bin'])
print('== Seed reviews (busqueda por DOI o titulo) ==')
seeds = {'Visinsky1994': r'robotic fault.detection and fault.tolerance', 'Milecki2023': r'review of fault-tolerant control systems used in robotic manipulators',
         'Chen2023': r'fault-tolerant strategy for space manipulators', 'Khan2025': r'fault.tolerant control.*industrial robots|industrial robots.*fault.tolerant',
         'Quamar2026': r'fault diagnosis and fault.tolerant control schemes for robotic manipulators', 'Zenteno2021': r'sliding mode control with application to fault.tolerant',
         'Metwly2024': r'robotic arm joint motors and online health monitoring', 'Urrea2025': r'hybrid fault.tolerant control in cooperative robotics', 'Maican2025': r'fault detection and diagnosis for human.centric robotic actuation'}
for key, pat in seeds.items():
    hits = [k for k, r in corp.items() if re.search(pat, r['title'], re.I)]
    if not hits: out.append(dict(test='SEED', key=key, expected='in-scope', retrieved='NO')); print(key, 'NO RECUPERADO'); continue
    for k in hits:
        s = scr[k]; out.append(dict(test='SEED', key=key, expected='in-scope', retrieved='SI', src=corp[k]['src'], decision=s['decision'], rule=s['rule']))
        print(key, '|', corp[k]['doi'], '|', corp[k]['year'], corp[k]['src'], s['decision'], s['rule'], '|', corp[k]['title'][:80])
with open(os.path.join(D, 'KNOWN_ITEMS_RESULT_RS2.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ['test', 'key', 'expected', 'retrieved', 'src', 'decision', 'rule'], extrasaction='ignore'); w.writeheader(); w.writerows(out)
