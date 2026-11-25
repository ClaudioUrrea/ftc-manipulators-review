"""RS2 auditoria: perdidas del recall. Para cada registro snowball INCLUDE 2016-2026 que no esta en el corpus, baja titulo, resumen y
palabras clave de OpenAlex y prueba los dos bloques de F01/SF01 (falla, manipulador) sobre titulo+resumen, para saber si la cadena lo
habria recuperado con metadatos completos (causa = indexacion) o no (causa = cadena).
Uso: python3 -I rs2_losses.py <carpeta_DATOS>   Salida: PERDIDAS_RECALL_RS2.csv (la columna juicio_manual se llena a mano)"""
import csv, json, os, re, sys, time, urllib.request
D = sys.argv[1]
A = ['fault toleran*','failure toleran*','fault accommodat*','fault compensat*','fault recover*','failure recover*','reconfigurable control*','control reconfigur*','post fault*','post failure','graceful degradation','actuator fault*','actuator failure*','loss of effectiveness','stuck actuator*','actuator stuck','lock in place','motor fault*','motor failure*','joint failure*','joint fault*','locked joint*','joint locking','joint lock','jammed joint*','joint jam*','free swinging','intermittent fault*','sensor fault*','sensor failure*','encoder fault*','encoder failure*']
B = ['manipulator*','robot* arm*','robotic arm*','industrial robot*','serial robot*','parallel robot*','redundant robot*','collaborative robot*','cobot*','scara','delta robot*','space robot*','robot* joint*','dual arm*','multi arm*','articulated robot*','continuum robot*','stewart platform*']
def rx(terms):
    ps = [r'[\s-]+'.join(re.escape(w).replace(r'\*', r'\w*') for w in t.split()) for t in terms]
    return re.compile(r'\b(' + '|'.join(ps) + r')\b', re.I)
RA, RB = rx(A), rx(B)
def get(u):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'FAME-review-RS2'}), timeout=40) as r: return json.load(r)
        except Exception: time.sleep(2 * (i + 1))
rows = [r for r in csv.DictReader(open(os.path.join(D, 'SNOWBALL_RS2.csv'), encoding='utf-8'))
        if r['decision'] == 'INCLUDE' and r['in_corpus'] == '0' and r['has_abstract'] == '1']
out = []
for r in rows:
    w = get('https://api.openalex.org/works/' + r['oa_id'] + '?select=title,abstract_inverted_index,type,primary_location,publication_date,keywords') or {}
    ii = w.get('abstract_inverted_index') or {}
    ab = ' '.join(t for _, t in sorted((p, t) for t, ps in ii.items() for p in ps))
    txt = (w.get('title') or '') + ' ' + ab
    src = ((w.get('primary_location') or {}).get('source') or {})
    a, b = RA.search(txt), RB.search(txt)
    out.append(dict(direction=r['direction'], seed=r['seed'], year=r['year'], doi=r['doi'], pub_date=w.get('publication_date'), type=w.get('type'), source=src.get('display_name', ''),
                    title=w.get('title'), bloque_falla=a.group(0) if a else 'NO', bloque_manip=b.group(0) if b else 'NO',
                    cadena_lo_recupera=int(bool(a and b)), abstract=ab, juicio_manual='', causa=''))
p = os.path.join(D, 'PERDIDAS_RECALL_RS2.csv')
old = {r['doi']: r for r in csv.DictReader(open(p, encoding='utf-8'))} if os.path.exists(p) else {}
for o in out:
    if o['doi'] in old: o['juicio_manual'], o['causa'] = old[o['doi']]['juicio_manual'], old[o['doi']]['causa']
with open(p, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
for o in out: print(o['doi'], '|', o['pub_date'], o['type'], '|', o['source'][:40], '| A:', o['bloque_falla'], '| B:', o['bloque_manip'], '\n  ', o['title'], '\n  ', o['abstract'][:700], '\n')
