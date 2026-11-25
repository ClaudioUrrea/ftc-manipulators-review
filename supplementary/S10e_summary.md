# Supplementary File S10e. Recoding of 20 studies by the review author, used only for error detection

The review author recoded 20 full-text studies (15 with hardware evidence, 4 with an ambiguous hardware claim and 1 at random) without seeing the extraction. Its internal-consistency criteria were fixed on 25-11-2026 at 07:53, after the coded sheet was saved (07:42) and before it was opened, and revised at 08:02 and 08:12, still unopened. The sheet failed one criterion (three studies coded passive with the fault known to the controller); after seeing the result, the author corrected two of the three rows and kept the third. The failed check concerned only this combination, which the extraction rule later admitted (Section 2.4 of the manuscript; File S1, Section 4.2, amendment 1.11(b)). The rule fixed beforehand was to omit the recoding if it failed; after the failure, the author decided to use it only to detect extraction errors (a declared deviation). It was not independent of the design of the coding frame. The same consistency checks were then applied, unchanged, to the extraction: they flag 5 studies, 2 passive schemes with the fault parameters or the failed joints given a priori (R00135, R00682), which the extraction rule admits because fault information given a priori is coded apart from the family (File S1, Section 4.2, amendment 1.11(b)), and 3 fault-information entries worded outside the vocabulary (R00005, R00028, R00954), which were rewritten. The same checks under the extraction rule, extended to the structural reserve and to the families of redundancy- and learning-based schemes, flag 17 cases in 13 studies; all were resolved against the full text (11 studies corrected, 2 codes confirmed). The phase-1 result of the recoding (failed) is unchanged. Agreement is reported descriptively (Wilson 95% intervals; for F_codes and hw_fault_classes, exact agreement of the set); no kappa is used as evidence of validity.

| Field | Base sheet: agree / n (proportion; 95% CI) | Revised sheet (v2): agree / n (proportion; 95% CI) |
|---|---|---|
| E_level | 2/20 (0.10; 0.03-0.30) | 2/20 (0.10; 0.03-0.30) |
| hardware_validated | 7/20 (0.35; 0.18-0.57) | 7/20 (0.35; 0.18-0.57) |
| injection_on_hardware | 7/20 (0.35; 0.18-0.57) | 7/20 (0.35; 0.18-0.57) |
| A_primary | 5/20 (0.25; 0.11-0.47) | 5/20 (0.25; 0.11-0.47) |
| F4_sub | 19/20 (0.95; 0.76-0.99) | 19/20 (0.95; 0.76-0.99) |
| fault_information | 5/20 (0.25; 0.11-0.47) | 7/20 (0.35; 0.18-0.57) |
| F_codes | 3/20 (0.15; 0.05-0.36) | 3/20 (0.15; 0.05-0.36) |
| hw_fault_classes | 5/20 (0.25; 0.11-0.47) | 5/20 (0.25; 0.11-0.47) |
| structural_reserve | 20/20 (1.00; 0.84-1.00) | 20/20 (1.00; 0.84-1.00) |

Each of the 107 discrepancies (union of both sheets) was adjudicated against the full text with generative-AI assistance, applying the written rules first (codebook S9, data dictionary of S5, the rule for ambiguous evidence claims and the literal A1/A2 reading of File S1, Section 4.2). Ambiguous cases were not resolved by default in favor of the extraction; none remained unresolved.

- Extraction errors, corrected: 15 in 7 studies (R00045, R00096, R00213, R00257, R00301, R00495, R00689).
- Errors of the recoding: 92.

| Field | Extraction error | Error of the recoding |
|---|---|---|
| A_primary | 5 | 10 |
| fault_information | 5 | 10 |
| E_level | 2 | 16 |
| F_codes | 0 | 17 |
| hw_fault_classes | 1 | 14 |
| hardware_validated | 1 | 12 |
| injection_on_hardware | 1 | 12 |
| F4_sub | 0 | 1 |

Files: S10e_author_recoding_discrepancies.csv (discrepancies), S10e_adjudication.csv (decision, rule and source per discrepancy), S10e_comparison.json (agreement by field). No extraction was verified by an independent human reviewer.
