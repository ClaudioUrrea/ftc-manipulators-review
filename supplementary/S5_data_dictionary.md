# Supplementary Table S5 — data dictionary (protocol v1.11, Section 9; updated in stages E8-c2b and E8-c3, 25-11-2026)
One row per L3 record extracted (123 rows: L3-R, L3-P and the L3-P replacements actually extracted; 105 eligible at full text, ft_eligible = yes). Full text read from the publisher's HTML; when it was not available, from a PDF (access codes below). The version read (publisher, accepted manuscript, preprint or author's copy of the published version) is stated in the notes. Empty cell = not reported; "NR" = explicitly checked and not reported.

| Field | Content and allowed values |
|---|---|
| rid … E_bin_abs | Identifiers, sample label (L3-R, L3-P), selection reason, stratum weight N_h/n_h (L3-R only), abstract-based rule codes (from RS2) |
| status | pending, done, held (extracted after the blind coding), no_access |
| access | html_institutional, html_open, pdf_open (a PDF read through open access: the publisher's open-access PDF when no HTML exists, author decision 16-11-2026, or, when the publisher version was not accessible, an accepted manuscript, a preprint or an author's copy of the published version; the version is stated in the notes; definition corrected in stage E8-c2b), pdf_institutional (PDF obtained through institutional or reviewer access, used when no HTML exists or to complete items missing from the HTML; author decision 16-11-2026), pdf_supplied (PDF obtained by the review author outside the library proxy, for example from the study authors; added 24-11-2026 for R01067), none |
| ft_eligible / ft_exclusion | yes / no; reason code of protocol Section 5 (EX-PLAT, EX-SCOPE, EX-FAULT, EX-FDI, EX-HW, IC1, IC2, IC3, EX-TYPE). Rows with "no" form Supplementary Table S4 |
| replaced_by | L3-P only: rid of the replacement (rule in L3-P_reserva.csv); L3-R exclusions are not replaced |
| M_ft, dof, robot_model | Manipulator class M1-M6; degrees of freedom; named robot or "generic n-link", "2-link planar" |
| F_ft, F4_sub | Fault codes F0-F8 (multi, ";"); F4t stuck-at torque, F4q locked joint. Precedence (amendment 1.10): a stuck channel (s_i = 1) is F4t whatever lambda_i and b_i, including the hard-over case (stuck at the actuator limit); a channel that delivers no torque (lambda_i = 0 and b_i = 0, or s_i = 1 with zero stuck torque) is F5; an effectiveness applied after the saturation is coded F1 |
| fault_equation | Fault model as written (ASCII/LaTeX), with the paper's symbols |
| normal_form_fit | full, partial, none, with the mapping to tau_a,i = (1-s_i) sat(lambda_i tau_c,i + b_i) + s_i tau_bar_i or to the joint-level constraint; three residual codes record why no actuator-level mapping is attempted: "sensor fault" (F8-only model, written in the sensor form y_i = q_i + delta_i), "not applicable" (fault handled at planning level without an actuator model) and "NR" (no fault model written) |
| fault_magnitude, onset, profile | Numerical values used in validation (for example lambda = 0.6 on joint 2); onset time; abrupt, incipient, intermittent, unspecified |
| n_simultaneous, faulty_channels | Number of simultaneously faulty channels; which joints |
| A_primary, A_all, mechanism | Primary family A1-A4 (mechanism that restores performance); all families; mechanism in a few words. A1 and A2 are mutually exclusive for one scheme (amendment 1.8), read literally (stage E8-c2b, 25-11-2026; protocol Section 4.2): a scheme is A2 when it computes online an estimate of the fault itself and that estimate enters the control law (the fault signal, a lumped term that the study states contains the fault, the effectiveness or its inverse, a bias or a stuck value), or when it detects or isolates the fault; it is A1 when it adapts only gains, bounds (including a bound on the fault magnitude or on the lumped term) or the weights of approximators of the fault-free dynamics, or adapts nothing |
| stability | none, UUB, asymptotic, exponential, finite-time, fixed-time, prescribed-time, prescribed performance, ISS, other |
| sensing | Measurements used by the accommodation: enc (joint position), vel, tau (joint torque), ft (force/torque), cur (motor current), vis, imu, other |
| fault_info | none, detection, isolation, estimation (of lambda, b, a stuck value or a lumped term containing the fault), known or full knowledge (the fault or the failed joint is given to the controller); a short qualifier in parentheses may follow the category. Consistent with A (stage E8-c2b): an A2 study records detection, isolation or estimation; an A1 study records none or known (given, not estimated online). Stage E8-c3: the category is written first and the qualifier in parentheses says what is given or obtained and where (equation or section); RS4 reads the category, not the qualifier. A1 with known is a passive law with the fault given a priori (File S1, Section 4.2, amendment 1.11(b)) |
| detection_delay | Delay assumed or measured between onset and accommodation |
| structural_condition | Remaining actuation authority, redundancy degree, underactuation, task relaxation required |
| E_ft, platform | E0 analysis; E1 numerical simulation; E2 high-fidelity simulation (actuator dynamics, limits and noise, physics engine or co-simulation); E3 bench or HIL; E4 physical manipulator with injected or real faults; platform or tool |
| injection | software command scaling, hardware disconnection, brake, real damage, simulated only |
| baselines | Controllers compared (nominal controller, other FTC) |
| metric, m_nominal, m_fault_noFTC, m_fault_FTC | Main tracking metric (for example RMS joint error in rad) and its values without fault, with fault and no accommodation, and with fault and the proposed accommodation |
| repetitions | Number of runs, statistics reported |
| code_data | none, on request, link |
| hw_fault_classes | E3-E4 studies only (added in stage E8-c, 25-11-2026): the fault classes (subset of F_ft) applied on the hardware run, from platform, injection, fault_magnitude and notes, or from the full text when these do not settle it; NR = the hardware run does not state its fault class (counts for no class). Hardware evidence in the F x A map is counted by fault class with this field |
| hw_note | Why hw_fault_classes differs from F_ft (for example, a class tested only in simulation) |
| hw_reserve | E3-E4 studies only (added in stage E8-c3, 25-11-2026): reserve exercised on the robot of the hardware run, one category: full actuation (the fault applied on hardware needs no reserve); physical actuation redundancy; kinematic redundancy of the physical arm; virtual channels (the redundancy of the scheme does not exist on the robot, for example channels split from one motor input); none or not stated. The location in the full text follows in parentheses. Hardware evidence that rests on virtual channels or on an unstated reserve is removed in the sensitivity variant "Hardware only with a physical reserve" (S13c) |
| hw_result | E3-E4 studies only (E8-c3): quantitative (a numeric metric of the faulty run on the robot, such as an error, an RMS or integral index, or a settling, recovery or detection time, printed in the text or a table); qualitative (figures or snapshots only, or approximate values read from the plots); not reported. The figure, table or section follows in parentheses |
| scope_flag | GEN: generic nonlinear, stochastic, fractional-order, switched or Markov-jump system class with a manipulator as validation plant; NET: network of manipulators, fault of an individual arm accommodated at that arm; RULE-IC1, RULE-IC3: admitted under the IC1 (mechanism positioning an end effector with actuated rollers) or IC3 (safe degradation) rules of amendment 1.10 |
| reserve_type | F4 and F5 studies: modeled redundant inputs; kinematic redundancy of the arm; physical actuation redundancy; underactuation of the arm |
| F7_sub | F7c, cable break or damage in a cable-driven robot (an actuation channel is lost); F7r, reducer, backlash or wear of the transmission |
| R1-R10, R_score | FAME reporting checklist, 0 or 1 each (protocol Section 9); score 0-10 |
| T_ML, T_DT, T_OPEN, T_BENCH | Tags at full text, 0 or 1 |

## Metric normalization (comparison across studies; RS4)
Studies report different metrics and units, so effect sizes are expressed as dimensionless ratios of the same metric within one study:
- Degradation ratio without accommodation: D0 = (m_fault_noFTC − m_nominal) / m_nominal.
- Residual degradation with accommodation: D1 = (m_fault_FTC − m_nominal) / m_nominal.
- Recovery fraction: RF = 1 − (m_fault_FTC − m_nominal) / (m_fault_noFTC − m_nominal), defined when m_fault_noFTC > m_nominal; RF = 1 means full recovery, RF ≤ 0 no improvement.
When only the faulty-without-accommodation case is missing, D1 is reported and RF is not computed. Values are taken only from numbers printed in text or tables, never read from plots. R00231 prints the three values, but its metric is the residual to the fault-free run, so m_nominal is 0 by construction; D0 and D1 are undefined and the study is not counted among those that report the three values needed for the ratios.

## Scoring rules for the FAME reporting checklist (fixed before full-text extraction; amendment v1.6)
- R1 fault equation: the fault enters the dynamics through a written equation (a verbal description does not count; a single lumped term that mixes faults with model uncertainty does not count).
- R2 magnitude: numerical values of the injected fault are given (gain, bias, torque bound, locked angle).
- R3 onset and profile: onset time and time profile are stated (both required). A fault that simply acts over the whole run (constant or time function, no stated onset) scores 0; an explicit statement such as "the fault occurs at t = 0 s" scores 1 (convention applied to all fichas, checked 16-11-2026).
- R4 injection mechanism: the paper states where and how the fault is applied (scaling of the command, additive torque, disconnection, brake, real damage); in simulation, an explicit injected expression on a named channel counts.
- R5 baselines: a fault-free reference (a separate run or the pre-fault segment of the same run) and a faulty run are both reported, and the proposed accommodation is compared with at least one alternative (no accommodation or another controller) under the same fault.
- R6 metrics: at least one summary metric (RMS, IAE, maximum or steady-state error, recovery time) is printed as a number for the faulty case; values read from plots or a single approximate remark do not count.
- R7 actuator limits: torque or input bounds are present in the validation (saturation modeled or enforced).
- R8 noise or disturbances: measurement noise or external disturbances are present in the validation.
- R9 repetitions or statistics: more than one run per scenario, or dispersion statistics.
- R10 code or data: a link or repository is given (on request does not count).

## Evidence-level ambiguities
When a paper claims experiments but describes no hardware, or describes results with simulation time and steps, E is coded at the lower supported level and the note starts with E_AMBIG; RS4 repeats the E analyses with E_AMBIG studies moved to E4 and with any E_AMBIG hardware claim not counted (Supplementary Table S13).
