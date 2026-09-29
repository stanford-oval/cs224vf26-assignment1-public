# Steering digest — round 1

**Question:** For Neurodevelopmental disorder with congenital cardiac defects and variable renal and ocular abnormalities (OMIM #621474), caused by variants in KDM2B: how can one identify which patients
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

- spent: $0.32 / $10.00  (init $0.03  plan $0.00  explore $0.03  screen $0.08  deep $0.17  measure $0.00)
- hypotheses: 11 — 3 pooled, 8 binned, 0 awaiting a test
- evidence items: 60
- open directions: 38
- uncovered asks: ['Clinical phenotypes reported in affected individuals with numerator and denominator counts per cohort (not percentages alone)', 'Phenotype descriptions as worded in the original paper plus standard HPO terms where identifiable', 'Source citation (PMID or DOI) and cohort identification for every reported phenotype frequency', 'Most discriminating findings present in most affected individuals but uncommon in differential diagnoses', 'Names of overlapping disorders usually confused with this condition', 'Confidence assessment of the phenotypic distinction against confused disorders', 'Clinical findings systematically assessed and confirmed absent in affected individuals (findings arguing against the diagnosis)', 'Phenotypic differences or genotype-phenotype correlations stratified by variant type, variant position, age, or sex', 'Contradictory findings reported between different studies']

## Top open directions (id — promise — question)
- `d20` — 0.95 — What are the exact patient-by-patient clinical numerators and denominators for cardiac, ocular, renal, and neurological features in the original clinical delineation paper by the episignature consortium referenced in Ceroni et al. and Kato et al.?
- `d29` — 0.92 — What is the exact pairwise classification specificity between KDM2B CxxC subsignatures and CHD7 (CHARGE syndrome) / KMT2D (Kabuki syndrome) peripheral blood episignatures?
- `d37` — 0.92 — Can peripheral blood DNA methylation episignatures definitively separate KDM2B-related neurodevelopmental disorder from CHD7-related CHARGE syndrome in patients with ambiguous clinical presentations?
- `d26` — 0.90 — Does the specific CxxC domain DNA-binding disruption cause structural cardiac and urogenital defects via a dominant-negative or gain-of-function mechanism compared to haploinsufficiency?
- `d35` — 0.90 — What is the sensitivity and false-negative rate of the KDM2B blood episignature among non-CxxC missense variants and loss-of-function variants with incomplete penetrance?
- `d28` — 0.88 — Does an ensemble classifier combining the KDM2B haploinsufficiency subsignature and the CxxC domain-specific subsignature improve diagnostic sensitivity for moderate-effect VUS?
- `d22` — 0.85 — In comprehensive cohort studies of KDM2B, what proportion of patients have undergone targeted temporal bone CT and flexible nasopharyngoscopy to definitively confirm or refute the true absence of semicircular canal hypoplasia and choanal stenosis?
- `d24` — 0.85 — Resolve the conflict over: In the definitive clinical discovery cohort establishing OMIM #621474, neurodevelopmental impairment/intellectual disability is an obligate feature (100% numerator/denominator in patients evaluated after 2 years of age), whereas congenital heart defects have a frequency of 50-70% and structural renal anomalies occur in under 40% of cases.
- `d25` — 0.85 — What is the true penetrance of non-syndromic versus syndromic neurodevelopmental impairment among unselected adult carriers of KDM2B loss-of-function variants in population biobanks?
- `d27` — 0.85 — Resolve the conflict over: A specific peripheral blood DNA methylation episignature distinguishes KDM2B-related neurodevelopmental disorder from clinically overlapping chromatin and recyclinopathy disorders (such as CHARGE, Kabuki, and Ritscher-Schinzel syndromes) with >95% sensitivity and specificity.
- `d30` — 0.85 — Resolve the conflict over: Individuals carrying heterozygous pathogenic variants in the CxxC zinc-finger domain of KDM2B exhibit a significantly higher penetrance of structural ocular malformations (microphthalmia, coloboma) and multi-organ anomalies mimicking CHARGE/Kabuki syndrome than individuals with non-CxxC loss-of-function variants.
- `d31` — 0.85 — Does an unselected, international registry of KDM2B-variant individuals reveal a statistically significant difference in ocular structural anomaly penetrance between CxxC missense variants and truncating/frameshift LoF variants?
- `d33` — 0.85 — Resolve the conflict over: A clinical diagnosis of KDM2B-related disorder cannot be established solely on facial dysmorphology or non-molecular criteria because KDM2B lacks a discrete facial gestalt, requiring genome-wide DNA methylation episignature analysis to resolve classification from Kabuki and CHARGE syndromes.
- `d34` — 0.85 — How effectively can computer vision algorithms like GestaltMatcher differentiate KDM2B-CxxC facial phenotypes from Kabuki (KMT2D/KDM6A) and CHARGE (CHD7) syndrome cohorts?
- `d36` — 0.85 — What is the true prevalence of semicircular canal hypoplasia or inner ear malformations on high-resolution temporal bone CT in molecularly confirmed KDM2B-related neurodevelopmental disorder?

## Recent hypotheses (id — status — text)
- `h9` — pooled/supported — Absence of choanal atresia and semicircular canal hypoplasia cannot reliably exclude CHARGE syndrome in favor of KDM2B-r
- `h8` — binned/conflicted — A specific peripheral blood DNA methylation episignature distinguishes KDM2B-related neurodevelopmental disorder from cl
- `h7` — binned/conflicted — In the definitive clinical discovery cohort establishing OMIM #621474, neurodevelopmental impairment/intellectual disabi
- `h6` — binned/refuted — Missense variants clustered within the CxxC zinc finger domain of KDM2B (amino acids ~600-650) demonstrate significantly
- `h5` — binned/conflicted — Truncating/loss-of-function variants (frameshift, nonsense, canonical splice site) span across KDM2B and generally lead 
- `h4` — pooled/supported — Severe limb reduction defects, ectrodactyly, and coarse lysosomal-like storage features have consistently been absent, a
- `h3` — binned/conflicted — The combination of developmental delay, cardiac malformations, and ocular coloboma or renal dysplasia closely mimics CHA
- `h2` — pooled/supported — Ocular and renal abnormalities occur in an intermediate subset (each approximately 30-50%), presenting as strabismus, re
- `h11` — binned/conflicted — A clinical diagnosis of KDM2B-related disorder cannot be established solely on facial dysmorphology or non-molecular cri
- `h10` — binned/conflicted — Individuals carrying heterozygous pathogenic variants in the CxxC zinc-finger domain of KDM2B exhibit a significantly hi
- `h1` — binned/conflicted — Neurodevelopmental delay/intellectual disability and speech delay are present in virtually 100% of reported individuals 

## Deprioritised — still here, can be brought back (`hypotheses_unbin`)
- `h1` — contested (3 for / 1 against): CxxC domain variants show full (>95-100%) penetrance of developmental — Neurodevelopmental delay/intellectual disability and speech delay are present in virtually
- `h8` — contested (5 for / 1 against): KDM2B exhibits divergence into two distinct sub-episignatures (loss-o — A specific peripheral blood DNA methylation episignature distinguishes KDM2B-related neuro
- `h7` — contested (5 for / 2 against): CHD penetrance depends heavily on variant domain: while CHD occurs in — In the definitive clinical discovery cohort establishing OMIM #621474, neurodevelopmental 
- `h3` — contested (4 for / 1 against): No published KDM2B cohort has systematically assessed or reported neg — The combination of developmental delay, cardiac malformations, and ocular coloboma or rena
- `h5` — contested (5 for / 1 against): The hypothesis posits that missense variants in catalytic/zinc-finger — Truncating/loss-of-function variants (frameshift, nonsense, canonical splice site) span ac
- `h10` — contested (4 for / 0 against): While Ceroni et al. emphasize CxxC zinc-finger missense variants as d — Individuals carrying heterozygous pathogenic variants in the CxxC zinc-finger domain of KD
- `h11` — contested (7 for / 1 against): van Oirsouw et al. (2026) report that individuals with KDM2B CxxC-dom — A clinical diagnosis of KDM2B-related disorder cannot be established solely on facial dysm
- `h6` — refuted: The hypothesis posits that missense variants in the CxxC zinc finger domain of KDM2B have > — Missense variants clustered within the CxxC zinc finger domain of KDM2B (amino acids ~600-

---
Drop a steer event into the inbox. Keys: `directions_add` [{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` {id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` [str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` [{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], `budget_delta` num, `control` continue|stop_after_round|finalize_now.