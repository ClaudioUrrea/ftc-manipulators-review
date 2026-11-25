"""RS2 paso 2 (version auditada 15-11-2026; enmienda v1.8 del 24-11-2026 solo en la asignacion de A, ver PROTOCOLO_RS1 s.13): cribado por reglas y codificacion FAME con CODEBOOK_FAME.csv.
Orden fijo (protocolo s.7): EX-TYPE, EX-LANG, EX-PLAT, EX-SCOPE, EX-FAULT, EX-FDI, EX-HW, luego IC1-IC3.
Decisiones de la auditoria (enmienda v1.5 del protocolo):
 - Texto de cribado y codificacion = titulo + resumen + palabras clave de AUTOR. Se excluyen Keywords Plus (WoS) e Index Keywords (Scopus):
   las asigna la base, no el autor, y son asimetricas entre fuentes.
 - IC1: termino de robot o manipulador en ese texto; si falta -> EXCLUDE (EX-IC1).
 - IC3: termino de tolerancia a fallas o acomodacion. IC2: termino de falla especifico (F1-F8 o falla de actuador/articulacion/motor/sensor).
 - INCLUDE = IC1 e IC3 y (IC2 especifico, o el termino de IC3 esta en el titulo o en las palabras clave de autor).
   IC1 e IC3 solo de paso en el resumen, sin falla especifica -> UNCERTAIN (IC-weak). IC1 e IC2 sin IC3 -> UNCERTAIN (IC-partial(12)).
 - Tambien INCLUDE: IC1, falla de actuador o articulacion en el texto y termino de control o planificacion en el titulo (acomodacion implicita).
 - Capa R: tipo Review o titulo con review/survey/overview/state of the art.
Uso: python3 -I rs2_screen.py <CODEBOOK_FAME.csv> <carpeta_DATOS>   Salida: SCREEN_RS2.csv, CONTEOS_screen_RS2.json"""
import csv, json, os, re, sys, collections
csv.field_size_limit(10**9)
CB, D = sys.argv[1], sys.argv[2]
cb = {r['code']: r for r in csv.DictReader(open(CB, encoding='utf-8'))}
rx = lambda c, k='include_regex': re.compile(cb[c][k], re.I) if cb[c][k] and not cb[c][k].startswith('(') else None
R = {c: (rx(c), rx(c, 'exclude_regex')) for c in cb}
OK_TYPES = ('article', 'review', 'proceedings paper', 'conference paper')
BAD_TYPES = re.compile(r'editorial|letter|meeting abstract|correction|erratum|book chapter|\bnote\b', re.I)
M_TERM = re.compile(r'\b(manipulat\w*|robot\w*|cobots?|scara|stewart platforms?|puma|hexapods?)\b', re.I)
F_SPEC = re.compile(r'\b((actuator|joint|motor|drive|torque|sensor|encoder|transmission|thruster|cable)s? (fault|failure|degradation|stuck|jam|damage)\w*|fault(y|ed)? (actuator|joint|motor|sensor|encoder)\w*|failed (actuator|joint|motor)\w*|(joint|actuator) (lock|jam)\w*|locked[- ]joint\w*|loss of (actuator )?effectiveness|free[- ]swinging)\b', re.I)
FTC = re.compile(r'\b(fault[- ]?toleran\w*|failure[- ]?toleran\w*|fault[- ]accommodat\w*|failure accommodat\w*|fault[- ]compensat\w*|failure compensat\w*|fault[- ]recover\w*|failure[- ]recover\w*|reconfigurable control\w*|control reconfigur\w*|ftc|fault[- ]hiding|post[- ]?fault\w*|post[- ]failure|graceful degradation)\b', re.I)
F_ACT = re.compile(r'\b((actuator|joint|motor|drive)s? (fault|failure)s?|loss of (actuator )?effectiveness|locked[- ]joints?|free[- ]swinging)\b', re.I)
CTRL_T = re.compile(r'\b(control\w*|compensat\w*|tracking|planning|redundancy resolution)\b', re.I)
A1_LAW = re.compile(r'\b(sliding[- ]mode\w*|terminal sliding\w*|super[- ]twisting|adaptive\w*|robust\w*|backstepping|h[- ]?(infinity|inf)\b|h\u221e|prescribed[- ]performance|passive fault[- ]?toleran\w*)', re.I)   # v1.8, desde la definicion de A1 del codebook
REVIEW = re.compile(r'\b(review|survey|overview|state[- ]of[- ]the[- ]art)\b', re.I)
OWN = re.compile(r'\bUrrea,? ?C', re.I)

def sents(t): return [s for s in re.split(r'(?<=[.!?])\s+', t) if s]

def screen(r):
    title, ab, kw = r['title'], r['abstract'], r['author_kw']
    txt = ' '.join([title, ab, kw])
    dt = r['doctype'].lower()
    unc = []
    if not any(k in dt for k in OK_TYPES) or BAD_TYPES.search(dt) or R['EX-TYPE'][0].search(title): return 'EXCLUDE', 'EX-TYPE', unc
    if r['language'].strip().lower() != 'english': return 'EXCLUDE', 'EX-LANG', unc
    inc, exc = R['EX-PLAT']
    n_inc = len(inc.findall(txt))
    if n_inc:
        ss = sents(ab)
        strong = bool(exc.search(title) or exc.search(kw) or exc.search(' '.join(ss[1:-1])))
        if (inc.search(title) or n_inc >= 2) and not strong: return 'EXCLUDE', 'EX-PLAT', unc
        unc.append('EX-PLAT')
    inc, exc = R['EX-SCOPE']
    if inc.search(txt):
        if exc.search(txt): unc.append('EX-SCOPE')
        else: return 'EXCLUDE', 'EX-SCOPE', unc
    inc, exc = R['EX-FAULT']
    if inc.search(txt) and not exc.search(txt): return 'EXCLUDE', 'EX-FAULT', unc
    inc, exc = R['EX-FDI']
    if inc.search(txt) and not exc.search(txt): return 'EXCLUDE', 'EX-FDI', unc
    inc, exc = R['EX-HW']
    if inc.search(txt):
        if exc.search(txt): unc.append('EX-HW')
        else: return 'EXCLUDE', 'EX-HW', unc
    ic1 = bool(M_TERM.search(txt))
    ic2 = bool(F_SPEC.search(txt) or any(R[c][0].search(txt) for c in ('F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8')))
    ic3 = bool(FTC.search(txt)); topic = bool(FTC.search(title + ' ' + kw))
    if not ic1: return 'EXCLUDE', 'EX-IC1', unc
    if ic3 and (ic2 or topic): return ('UNCERTAIN' if unc else 'INCLUDE'), ';'.join(unc), unc
    if ic3: return 'UNCERTAIN', ';'.join(unc + ['IC-weak']), unc
    if F_ACT.search(txt) and CTRL_T.search(title): return ('UNCERTAIN' if unc else 'INCLUDE'), ';'.join(unc), unc   # ley de control disenada bajo falla de actuador o articulacion
    if ic2: return 'UNCERTAIN', ';'.join(unc + ['IC-partial(12)']), unc
    return 'EXCLUDE', 'EX-IC2', unc

def code(r):
    txt = ' '.join([r['title'], r['abstract'], r['author_kw']])
    hit = lambda c: bool(R[c][0] and R[c][0].search(txt))
    F = [c for c in ('F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8') if hit(c)] or ['F0']
    A = [c for c in ('A2', 'A3', 'A4', 'A1') if hit(c)]
    flags = []
    if 'A2' in A and 'A1' in A: A.remove('A1')   # v1.8: A1 y A2 son excluyentes para un mismo esquema (A1 exige ausencia de informacion de la falla)
    if not A:   # v1.8: sin codigo A explicito, A1 solo si el texto declara una ley robusta o adaptativa fija; si no, A queda sin asignar (A-NR)
        if A1_LAW.search(txt): A, flags = ['A1'], ['A1-LAW']
        else: A, flags = [], ['A-NR']
    M = [c for c in ('M2', 'M3', 'M4', 'M5', 'M6', 'M1') if hit(c)]
    if not M: M, flags = ['M1'], flags + ['M1-FALLBACK']
    E = 'E4' if hit('E4') else ('E3' if hit('E3') else 'E0-E2')
    T = [c for c in ('T-ML', 'T-DT', 'T-SAT', 'T-OPEN', 'T-BENCH') if hit(c)]
    return ';'.join(F), ';'.join(A), ';'.join(M), E, T, flags

def layer(r): return 'R' if 'review' in r['doctype'].lower() or REVIEW.search(r['title']) else 'P'

if __name__ == '__main__':
    rows = list(csv.DictReader(open(os.path.join(D, 'CORPUS_RS2.csv'), encoding='utf-8')))
    out = []
    for r in rows:
        dec, rule, _ = screen(r)
        F = A = M = E = ''; T, fl = [], []
        if dec != 'EXCLUDE': F, A, M, E, T, fl = code(r)
        if OWN.search(r['authors']): T.append('OWN')
        if 'retracted' in (r['doctype'] + ' ' + r['title'] + ' ' + r.get('note', '')).lower(): fl.append('RETRACTED')
        if not r['abstract']: fl.append('NO-ABS')
        out.append(dict(rid=r['rid'], src=r['src'], doi=r['doi'], year=r['year'], title=r['title'], journal=r['journal'], cited_by=r['cited_by'],
                        layer=layer(r), decision=dec, rule=rule, F=F, A=A, M=M, E_bin=E, tags=';'.join(T), flags=';'.join(fl)))
    with open(os.path.join(D, 'SCREEN_RS2.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(out[0].keys())); w.writeheader(); w.writerows(out)
    C = collections.Counter; y = lambda o: '2016' <= o['year'] <= '2026'
    cnt = dict(n=len(out), decision=C(o['decision'] for o in out), exclude_by_rule=C(o['rule'] for o in out if o['decision'] == 'EXCLUDE'),
               uncertain_by_rule=C(o['rule'] for o in out if o['decision'] == 'UNCERTAIN'),
               n_2016_2026=sum(y(o) for o in out), decision_2016_2026=C(o['decision'] for o in out if y(o)),
               include_primary=sum(o['decision'] == 'INCLUDE' and o['layer'] == 'P' for o in out),
               include_primary_2016_2026=sum(o['decision'] == 'INCLUDE' and o['layer'] == 'P' and y(o) for o in out),
               include_layer_R=sum(o['decision'] == 'INCLUDE' and o['layer'] == 'R' for o in out),
               E_bin_include_primary_2016_2026=C(o['E_bin'] for o in out if o['decision'] == 'INCLUDE' and o['layer'] == 'P' and y(o)),
               include_by_src=C(o['src'] for o in out if o['decision'] == 'INCLUDE'),
               own=sum('OWN' in o['tags'] for o in out), own_include=sum('OWN' in o['tags'] and o['decision'] == 'INCLUDE' for o in out),
               retracted=sum('RETRACTED' in o['flags'] for o in out), noabs=sum('NO-ABS' in o['flags'] for o in out))
    json.dump(cnt, open(os.path.join(D, 'CONTEOS_screen_RS2.json'), 'w'), indent=1)
    print(json.dumps(cnt))
