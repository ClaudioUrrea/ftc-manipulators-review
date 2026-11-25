# Supplementary File S10. Agreement of the scripted rules with blind human coding, and reproducibility check of the full-text extraction

Agreement tables and bootstrap intervals: `S10_agreement_round1.csv/.json` (round 1) and `S10_agreement_round2.csv/.json` (round 2). Reproducibility check of the extraction: `S10c_*`. All values below are read from those files.

## Round 1 (blind sample of 60 records, 20 per rule outcome; seed 20261116)
The coder (the review author) coded title, abstract and keywords without tools and without the key; the coding sheet was frozen before the key was opened. Kappa intervals: bootstrap stratified by rule outcome (2000 replicates).
- Inclusion, rule INCLUDE against human inclusion: raw agreement 0.85; Cohen's kappa 0.68 (95% CI 0.51-0.85); Gwet's AC1 0.72 (0.55-0.88).
- Precision of INCLUDE 18/20 = 0.90 (Wilson 0.70-0.97); negative predictive value of EXCLUDE 19/20 = 0.95 (0.76-0.99); UNCERTAIN judged in scope 6/20 = 0.30 (0.15-0.52).
- Counting UNCERTAIN as included: kappa 0.46 (0.31-0.61); UNCERTAIN records are therefore kept outside the mapping set.
- Codes, on the 24 records included by the coder with rule codes: manipulator class kappa 0.47-1.00 (AC1 0.84-1.00); fault class kappa 0.47-1.00 (AC1 0.75-1.00); evidence bin kappa 0.65 (AC1 0.95); accommodation family A1 kappa 0.20, A2 0.57, A3 0.56, A4 0.00 with AC1 0.96 (one positive case). Low kappa values with high raw agreement belong to rare codes.
- Pattern: most disagreements were at the A1/A2 boundary (schemes that the rule coded as active and the coder read as fixed adaptive laws).

## Round 2 (amendment 1.8; new blind sample of 60 rule-INCLUDE primary records, 2016-2026, stratified by rule A code; seed 20261124)
- The sample excludes the rule development set, the round 1 sample, every full-text record and own records.
- Coder included 50 of 60 (0.83, Wilson 0.72-0.91); this inclusion is not blind to the rule frame and is secondary.
- Primary (n = 50): A1 kappa 0.36 (0.16-0.55), AC1 0.40; A2 kappa 0.55 (0.28-0.80), AC1 0.70; A3 kappa 0.75 (0.50-0.94), AC1 0.88; A4 kappa 0.52 (0.15-0.79), AC1 0.84.
- Post hoc: round 1 recomputed with the version 1.8 rules gives A1 kappa 0.30 (before 0.20); A2-A4 unchanged.
- Decision rule fixed in the protocol (Section 7): A1 and A2 kappa below 0.60, so the fault-by-accommodation cross-tabulation of the mapping set is descriptive only, and every fault-by-accommodation statement rests on the full-text set.

## S10c. Reproducibility check of the AI-assisted full-text extraction (20 studies; 10 per sample; seed 20261124)
A second extraction, run blind to the first with the same AI-assisted procedure, was compared field by field with the first, frozen extraction. It measures the reproducibility of the procedure, not the agreement of two independent reviewers.
- Coded fields agreeing: 90% overall; evidence level (E0-E4) 20/20 (kappa 1.00); hardware validation 20/20; primary accommodation family 18/20 (kappa 0.84); manipulator class 18/20 (kappa 0.83); F4 sub-code 19/20 (kappa 0.87); exact set of fault classes 12/20 (kappa 0.56); normal-form fit 12/20 (kappa 0.25); reporting items R1-R10 agreed in 16-20 of 20 each; total reporting score identical in 14 of 20 studies.
- Adjudication against the full text: 34 discrepancies; 19 corrected the first extraction (11 studies) and 15 kept it; the corrections were applied before the synthesis (`S10c_extraction_adjudication.csv`).

## S10d. Third extraction targeted at the hardest codes (20 studies; stage E8-c)
Sample: all F4q, F5 and F7 studies of the synthesis set (15) plus five drawn at random from the rest of the full-text set (seed 20261125). The studies were coded from the full text in a separate session, assisted by generative AI as the first extraction, without access to the first extraction or to the key until the coded sheet was frozen (SHA-256 recorded). Like the second extraction, it measures the reproducibility of the procedure, not the agreement of an independent human reviewer. Values from `S10d_agreement.json` and `S10d_adjudication_summary.json`.
- Agreement: evidence level 17/20 (kappa 0.725); hardware validation 18/20 (kappa 0.794); primary accommodation family 19/20 (kappa 0.913); F4 sub-code 19/20 (kappa 0.905); fault information 18/20 (kappa 0.843); exact set of fault classes 19/20 (mean Jaccard 0.975); exact set of hardware fault classes 17/20 (mean Jaccard 0.883); structural reserve 17/20; 90% of coded fields overall.
- First adjudication against the full text (stage E8-c; `S10d_discrepancies_adjudicated.csv`, `S10d_adjudication_summary.json`): 16 discrepancies in 10 studies; 0 extraction errors, 3 errors of the third extraction (one study: a hardware section missed) and 13 codes judged ambiguous, for which the extraction was kept. This first adjudication was superseded by the readjudication below.
- Readjudication (stage E8-c2; `S10d_readjudication.csv`): the 16 discrepancies were readjudicated against the full text, with AI assistance, by applying the written rules first (the rule for ambiguous evidence claims and the definitions of structural reserve and fault information); the declared tie-break, keeping the first extraction and listing the case, was not needed. Twelve discrepancies, in 8 studies, were errors of the first extraction and were corrected, and the synthesis was rerun; four, in 2 studies, were errors of the third extraction. These are the values reported in Section 2.6 of the manuscript and in item 9 of File S7.
- The coded sheet (`S10d_coded_sheet_blind_20.csv`) is published as it was frozen (SHA-256 recorded) and is not edited or translated: one column holds the coder's notes in Spanish.
