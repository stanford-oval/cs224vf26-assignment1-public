# Steering digest — round 1

**Question:** For Cornelia de Lange syndrome 7 (OMIM #621570), caused by variants in MAU2: how can one identify which patients
have this disease from their phenotypes alone?

Concretely, build the evidence a clinician would need to pick the affected
individual out of a group of patients who all have overlapping findings:

  1. Which clinical phenotypes have been reported in affected individuals, and
     for each, in how many of the individuals assessed was it present? Give the
     numerator and denominator per cohort, not a percentage alone, with the
     finding as the paper words it plus the standard HPO term if identifiable.
  2. Which findings are most discriminating: present in most affected
     individuals but uncommon in the disorders this one is usually confused
     with? Name those disorders and say how confident the distinction is.
  3. Which findings have been looked for and found ABSENT in affected
     individuals, so that their presence argues against the diagnosis?
  4. Whether the phenotype differs by variant type, position, age or sex.
  5. Any finding one paper reports and another explicitly contradicts.

Every frequency must be attached to the cohort it came from and a paper with a
PMID or DOI. Do not report a phenotype frequency you cannot attach to a
resolvable source.

- spent: $0.27 / $10.00  (init $0.04  plan $0.00  explore $0.03  screen $0.07  deep $0.14  measure $0.00)
- hypotheses: 10 — 6 pooled, 4 binned, 0 awaiting a test
- evidence items: 45
- open directions: 32
- uncovered asks: ['Clinical phenotypes reported in affected individuals with MAU2 variants (OMIM #621570), with original paper wording and corresponding standard HPO terms where identifiable', 'Frequency of each reported clinical phenotype given as exact numerator and denominator per cohort, attached to the specific cohort and a resolvable source (PMID or DOI)', 'Most discriminating clinical findings present in most affected individuals but uncommon in commonly confused overlapping disorders, naming those differential disorders and specifying the confidence of distinction', 'Clinical findings specifically assessed and found absent in affected individuals whose presence would argue against the diagnosis', 'Phenotype differences or correlations by variant type, variant position, age, or sex', 'Any contradictory clinical findings across papers where one report claims presence and another explicitly contradicts it']

## Top open directions (id — promise — question)
- `d32` — 0.89 — What is the sensitivity and specificity of MAU2-specific DNA methylation episignatures compared directly against RAD21, SMC3, and SMC1A episignatures across ambiguous CdLS presentations?
- `d15` — 0.88 — What are the exact patient-by-patient numerator/denominator frequencies for congenital heart defects, limb anomalies, and gastrointestinal abnormalities in the Parenti et al. 18-patient MAU2 cohort?
- `d17` — 0.88 — What are the exact numerator/denominator frequencies of major organ malformations (cardiac defects, diaphragmatic hernia, gastrointestinal malrotation) specifically documented in the 18 MAU2 probands from Parenti et al. (2025/2026)?
- `d19` — 0.85 — Resolve the conflict over: Microcephaly (HP:0000252) is present in the vast majority of MAU2-deficient individuals (at least 14 of the 18 patients, or >=77%) in the Parenti et al. cohort, demonstrating that cranial growth failure is a primary cardinal finding of CdLS7.
- `d20` — 0.85 — What is the exact frequency, severity (SD below mean occipitofrontal circumference), and age of onset of microcephaly across the complete individual patient table of the 18 Parenti et al. subjects?
- `d22` — 0.85 — Resolve the conflict over: Synophrys (HP:0000664) and thick, arched eyebrows (HP:0002553) have an intermediate penetrance of approximately 50% to 65% (10-12 of 18 assessed patients) in MAU2 CdLS7, occurring at a significantly lower frequency than in classical NIPBL-related CdLS (>95%).
- `d23` — 0.85 — Does the presence or absence of synophrys in MAU2-CdLS7 correlate with the specific functional class of MAU2 variant (in-frame missense disrupting NIPBL interaction vs truncating haploinsufficiency)?
- `d25` — 0.85 — Resolve the conflict over: MAU2-related CdLS (CdLS7) exhibits a bimodal phenotypic severity distribution driven by variant mechanism, where truncating/loss-of-function variants causing MAU2 haploinsufficiency lead to a classical CdLS dysmorphic score, whereas in-frame missense/deletion variants impairing heterodimerization yield an attenuated cohesinopathy phenotype clinically indistinguishable from SMC3- or RAD21-related CdLS.
- `d26` — 0.85 — Does international clinical consensus scoring (Kline et al. CdLS clinical score) correlate quantitatively with MAU2 episignature subtype across an expanded multi-center cohort?
- `d16` — 0.82 — Do the two MAU2-specific episignatures defined by Parenti et al. correlate strictly with cardinal dysmorphic feature severity scores (such as the international CdLS consensus scoring system)?
- `d18` — 0.82 — Does the DNA methylation episignature of MAU2 probands cleanly differentiate MAU2-CdLS7 from SMC3- and RAD21-related CdLS in clinical blood samples?
- `d33` — 0.82 — What is the exact penetrance of minor digital anomalies (such as fifth-finger clinodactyly or subtle brachydactyly) in expanded MAU2 patient cohorts compared to classic NIPBL and SMC1A cohorts?
- `d21` — 0.80 — Do truncating MAU2 variants causing haploinsufficiency associate with more severe microcephaly than in-frame variants that disrupt NIPBL-MAU2 heterodimerization?
- `d24` — 0.80 — What is the sensitivity and specificity of objective 3D facial photogrammetry in differentiating MAU2-related CdLS7 from other non-NIPBL cohesinopathies (e.g., SMC1A, SMC3, RAD21, HDAC8)?
- `d31` — 0.78 — Can machine learning-assisted 3D facial photogrammetry differentiate MAU2-related CdLS facial dysmorphism from RAD21- and SMC3-associated dysmorphic features?

## Recent hypotheses (id — status — text)
- `h9` — pooled/supported — The clinical phenotypic overlap between CdLS7 and RAD21- or SMC3-related CdLS is so extensive that clinical scoring syst
- `h8` — binned/conflicted — MAU2-related CdLS (CdLS7) exhibits a bimodal phenotypic severity distribution driven by variant mechanism, where truncat
- `h7` — binned/refuted — The presence of classic facial dysmorphic signs (synophrys, arched eyebrows, long eyelashes) correlates with variant cla
- `h6` — binned/conflicted — Synophrys (HP:0000664) and thick, arched eyebrows (HP:0002553) have an intermediate penetrance of approximately 50% to 6
- `h5` — binned/conflicted — Microcephaly (HP:0000252) is present in the vast majority of MAU2-deficient individuals (at least 14 of the 18 patients,
- `h4` — pooled/supported — Genotype-phenotype correlations in MAU2 remain incompletely characterized due to the very small total number of publishe
- `h3` — pooled/supported — Severe limb reduction defects (HP:0009804, such as phocomelia, amelia, or severe transverse limb deficiencies) and sever
- `h2` — pooled/supported — Distinguishing CdLS7 from classical NIPBL-related CdLS (CdLS1) relies on the milder overall neurodevelopmental impairmen
- `h10` — pooled/supported — Severe structural limb reduction defects (including forearm aplasia, absent ulna/radius, and oligodactyly) have a true p
- `h1` — pooled/supported — Clinical phenotypes in CdLS7 individuals consistently include neurodevelopmental delay/intellectual disability (HP:00012

## Deprioritised — still here, can be brought back (`hypotheses_unbin`)
- `h5` — contested (3 for / 1 against): The explicit numerical fraction of 'at least 14 of the 18 patients (> — Microcephaly (HP:0000252) is present in the vast majority of MAU2-deficient individuals (a
- `h6` — contested (6 for / 1 against): The hypothesis assumes classic NIPBL-related CdLS has >95% penetrance — Synophrys (HP:0000664) and thick, arched eyebrows (HP:0002553) have an intermediate penetr
- `h8` — contested (3 for / 1 against): Molecular categorization demonstrates two distinct MAU2-specific DNA  — MAU2-related CdLS (CdLS7) exhibits a bimodal phenotypic severity distribution driven by va
- `h7` — refuted: The available literature demonstrates distinct molecular and epigenetic mechanisms between  — The presence of classic facial dysmorphic signs (synophrys, arched eyebrows, long eyelashe

---
Drop a steer event into the inbox. Keys: `directions_add` [{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` {id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` [str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` [{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], `budget_delta` num, `control` continue|stop_after_round|finalize_now.