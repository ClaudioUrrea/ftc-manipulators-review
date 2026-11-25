"""RS4-8. Contrast with previous reviews. Table 5 of the manuscript (stage E8-c): the two closest reviews of FTC in
manipulators or industrial robots that pair faults with strategies (Quamar and Nasir 2026; Khan et al. 2025) and the
scope boundary (Urrea 2025). Maican et al. 2025 (diagnosis only) is kept in this file for the detection-delay comparison.

Attributes of the other reviews are taken from their full texts or publisher pages and
recorded with their source; every figure of the present review is read from the RS4
result files. Output: C1_contraste_revisiones.csv, contraste.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd  # noqa: E402

import rs4_comun as c  # noqa: E402

J = {n: json.loads((c.RES / f"{n}.json").read_text(encoding="utf-8")) for n in ["descriptivos", "hipotesis", "rq1_rq2", "reporte", "brechas"]}
d, h, q, r, g = J["descriptivos"], J["hipotesis"], J["rq1_rq2"], J["reporte"], J["brechas"]
pct = lambda x: f"{100 * x:.1f} %"  # noqa: E731

own = {
    "Scope": "FTC of single robot manipulators (serial, parallel, redundant, space, dual-arm, continuum) under actuator, joint and sensor faults; multi-robot team FTC excluded",
    "Protocol and reporting": "Protocol registered on OSF (10.17605/OSF.IO/ECQA7), PRISMA 2020 and PRISMA-S, dated amendments",
    "Sources and strings": "Web of Science Core Collection and Scopus; exact strings published; OpenAlex snowballing (recall 0.88)",
    "Corpus": f"{d['screened']} unique records screened; {d['L1_n']} primary studies in the mapping set ({d['L1_window_n']} in 2016-2026); {d['L3_n']} read at full text",
    "Screening and coding": "Scripted rules validated against blind human coding in two rounds (inclusion kappa 0.68)",
    "Fault representation": f"Equation-level normal form; {q['fit_studies'].get('full', 0)} of {d['L3_n']} full-text fault models map fully onto it",
    "Fault-strategy link": f"F x A map; {g['core_status'].get('hardware (L3)', 0)} of 28 actuator and joint cells with hardware evidence for the fault class, {len(g['core_hw_ge3'])} with three or more studies, {g['core_status'].get('empty', 0)} empty",
    "Evidence grading": "Five levels (E0-E4) at full text; three bins in the mapping set; measurement error of the abstract bin corrected (Rogan-Gladen)",
    "Physical validation": (f"{pct(d['L1_window_hw_share'])} of 2016-2026 abstracts; design-based full-text estimate {pct(h['E_prev_design'])} "
                            f"(95 % CI {pct(h['E_prev_design_ci'][0])}-{pct(h['E_prev_design_ci'][1])})"),
    "Reporting checklist": f"FAME checklist R1-R10 scored per study (median {r['score_median']:.0f} of 10); fault-injection checklist proposed",
    "Detection delay reported": f"{q['needs_info_delay_quantified']} of {q['needs_info_n']} full-text studies that use fault information quantify it",
    "Data and code": "Coded corpus, extraction sheet and scripts released (GitHub and Figshare)",
}
quamar = {
    "Scope": "FTC and fault diagnosis of robotic manipulators, organized by method evolution, sensors, artificial intelligence and digital twins",
    "Protocol and reporting": "PRISMA 2020 flow diagram; two search phases (1975-2000, 2000-2025); no registered protocol mentioned",
    "Sources and strings": "IEEE Xplore, Web of Science and Scopus; keyword list, no search strings",
    "Corpus": "320 papers, 1975-2025; quality filter (three of four criteria)",
    "Screening and coding": "Not reported as validated",
    "Fault representation": "Verbal taxonomy (occurrence, severity, component, origin, signal effect); no fault equations; locked, free-swinging and loss-of-effectiveness faults not named",
    "Fault-strategy link": "Comparison of method families (model-based, data-driven, hybrid); no fault-by-strategy map",
    "Evidence grading": "Validation used as an inclusion criterion, not graded or counted",
    "Physical validation": "Not quantified",
    "Reporting checklist": "None",
    "Detection delay reported": "Not assessed",
    "Data and code": "None (data statement: no data used)",
}
urrea = {
    "Scope": "Hybrid FTC in cooperative robotics (system level, several domains)",
    "Protocol and reporting": "Narrative review; no protocol",
    "Sources and strings": "Not stated",
    "Corpus": "57 references, all 2021-2025; no study count",
    "Screening and coding": "Not applicable",
    "Fault representation": "No formal fault model",
    "Fault-strategy link": "Passive, active and hybrid FTC; mechanical, algorithmic and hybrid redundancy; learning-based methods",
    "Evidence grading": "Not graded",
    "Physical validation": "About one quarter of strategies (secondhand estimate, about 23 %)",
    "Reporting checklist": "None; calls for standardized benchmarks and testing protocols",
    "Detection delay reported": "Not assessed",
    "Data and code": "No new data",
}
maican = {
    "Scope": "Fault detection and diagnosis (no accommodation) for human-centric robotic actuation in healthcare",
    "Protocol and reporting": "Structured search with two screeners; no PRISMA statement or registered protocol",
    "Sources and strings": "IEEE Xplore, Scopus, Web of Science, Google Scholar (PubMed also named)",
    "Corpus": "127 studies, 2016-2025",
    "Screening and coding": "Two reviewers on titles and abstracts",
    "Fault representation": "Failure modes by actuator family (harmonic drive, series-elastic, cable, PMSM, force-torque sensed)",
    "Fault-strategy link": "Not applicable (diagnosis only)",
    "Evidence grading": "Validation environments counted (on-body or clinical 21.3 %, HIL 18.1 %)",
    "Physical validation": "Not applicable",
    "Reporting checklist": "Validation framework (time to detect, minimal detectable fault amplitude, false-alarm rate) and reporting checklist",
    "Detection delay reported": "Time to detect reported in 0 of 127 studies",
    "Data and code": "Not released",
}
khan = {
    "Scope": "FTC of industrial robots (actuator, sensor, gearbox, controller, communication and software faults), with emphasis on AI-based fault management",
    "Protocol and reporting": "Narrative review; no PRISMA statement or registered protocol",
    "Sources and strings": "Scopus bibliometric search ('Fault tolerant Industrial Robot') used for a keyword map",
    "Corpus": "284 Scopus documents (1981-2023), 86 kept for the keyword map; 111 references; no study count",
    "Screening and coding": "Not reported",
    "Fault representation": "Verbal classes by time behavior (abrupt, incipient, intermittent), additive or multiplicative effect and subsystem; no fault equations for actuators or joints",
    "Fault-strategy link": "Table of fault types by robot location with example approaches (locked and free-swinging joints with kinematic redundancy); not graded",
    "Evidence grading": "Not graded",
    "Physical validation": "Not quantified",
    "Reporting checklist": "None",
    "Detection delay reported": "Not assessed",
    "Data and code": "On request",
}
src = {
    "Khan et al. 2025 (Artif. Intell. Rev. 58, 362)": "Full text, open access https://link.springer.com/article/10.1007/s10462-025-11327-2 (read 25-11-2026; Sections 1, 3 and 8, Table 4, data statement)",
    "Quamar and Nasir 2026 (Eng. Appl. Artif. Intell. 184, 116367)": "Full text (05/referencias/Quamar_Nasir_2026_EAAI_116367.pdf; reading notes 06/LECTURA_Quamar2026.md)",
    "Urrea 2025 (Actuators 14, 177)": "Publisher page https://www.mdpi.com/2076-0825/14/4/177 (read 24-11-2026)",
    "Maican et al. 2025 (Actuators 14, 566)": "Publisher page https://www.mdpi.com/2076-0825/14/12/566 (read 24-11-2026)",
    "This review": "RS4 result files",
}
rows = []
for attr in own:
    rows.append({"attribute": attr, "Quamar and Nasir 2026": quamar[attr], "Khan et al. 2025": khan[attr], "Urrea 2025": urrea[attr],
                 "This review": own[attr], "Maican et al. 2025 (text only)": maican[attr]})
C = pd.DataFrame(rows)
c.save_csv(C, "C1_contraste_revisiones.csv")
contrast = dict(
    hw_window_abstract=d["L1_window_hw_share"], hw_design=h["E_prev_design"], hw_design_ci=h["E_prev_design_ci"],
    hw_rg=h["rogan_gladen"]["L1 2016-2026"]["p_corrected"],
    urrea_quarter=0.25, ratio_design_to_quarter=c.rnd(h["E_prev_design"] / 0.25, 2),
    delay_quantified=q["delay"].get("quantified", 0), L3_n=d["L3_n"], L1_vs_quamar=c.rnd(d["L1_n"] / 320, 2),
    sources=src,
)
c.save_json(contrast, "contraste.json")
print(C.to_string()[:3000]); print(contrast)
