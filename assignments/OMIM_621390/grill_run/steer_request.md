# Steering digest — round 1

**Question:** For Neurodevelopmental disorder with early-onset seizures, facial dysmorphism, and behavioral abnormalities (OMIM #621390), caused by variants in KLHL20: how can one identify which patients
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

- spent: $0.23 / $10.00  (init $0.03  plan $0.01  explore $0.02  screen $0.06  deep $0.11  measure $0.00)
- hypotheses: 10 — 4 pooled, 6 binned, 0 awaiting a test
- evidence items: 36
- open directions: 34
- uncovered asks: ['Reported clinical phenotypes in individuals with KLHL20-related neurodevelopmental disorder (OMIM #621390), including verbatim wording from the paper and standard HPO term if identifiable.', 'Frequency of each phenotype reported as numerator and denominator per cohort (not percentage alone), attached to a resolvable source (PMID or DOI).', 'Most discriminating findings that are present in most affected individuals but uncommon in disorders typically confused with this condition, including the names of those differential disorders and confidence in the distinction.', 'Phenotypes or findings looked for and found absent in affected individuals that would argue against the diagnosis if present.', 'Analysis of whether phenotype differs by variant type, variant position, patient age, or patient sex.', 'Phenotypic findings or claims where one paper reports a finding and another paper explicitly contradicts it.']

## Top open directions (id — promise — question)
- `d22` — 0.95 — What are the exact numerator and denominator frequencies for specific HPO terms (such as Global developmental delay HP:0001263, Seizures HP:0001250, and specific facial dysmorphisms) across all documented KLHL20 patients in the complete Sleyp et al. supplementary clinical table?
- `d17` — 0.90 — What are the exact individual-level clinical data, HPO annotations, and variant coordinates in the primary KLHL20 publication by Sleyp et al. (2022/2023)?
- `d36` — 0.90 — Does the recurrent p.Gly357Arg variant act via a dominant-negative interference or a toxic gain-of-function degron mechanism rather than simple haploinsufficiency?
- `d19` — 0.85 — What are the exact numerators and denominators for specific seizure types (e.g., infantile spasms, focal seizures, generalized tonic-clonic) and seizure responsiveness to anti-seizure medications in published KLHL20 cohorts?
- `d23` — 0.85 — Does seizure semiology, age of onset, or penetrance differ between carriers of the recurrent Kelch-domain p.Gly357Arg variant versus non-recurrent missense variants in KLHL20?
- `d24` — 0.85 — Resolve the conflict over: The combination of prominent autistic traits and hyperactivity alongside subtle craniofacial dysmorphism differentiates KLHL20-associated disorder from classic non-syndromic developmental and epileptic encephalopathies (such as SCN1A- or STXBP1-related DEEs), where dysmorphic facial features and primary ASD profiles are atypical.
- `d26` — 0.85 — What is the true frequency and distribution of detailed seizure types and EEG patterns in KLHL20 variants compared to SCN1A and STXBP1 cohorts?
- `d29` — 0.85 — Resolve the conflict over: Facial dysmorphism in KLHL20-related NEDSFBA constitutes an obligate discriminating signature recognizable by computational facial phenotyping (dense 3D facial imaging) that separates it from clinically overlapping non-syndromic developmental and epileptic encephalopathies (DEEs).
- `d35` — 0.85 — Do complete loss-of-function homozygous mutations in Klhl20 result in embryonic lethality in mammalian model organisms, explaining their absence in living human clinical cohorts?
- `d28` — 0.82 — What is the exact penetrance and semiology of early-onset seizures in KLHL20 patients compared to non-syndromic early infantile epileptic encephalopathies?
- `d31` — 0.80 — How do craniofacial features and systemic manifestations differ between dominant de novo missense KLHL20 variants and recessive loss-of-function or founder variants?
- `d32` — 0.80 — What is the long-term seizure freedom rate and medication responsiveness in adult KLHL20 mutation carriers?
- `d27` — 0.78 — Can 3D dense surface facial modeling objectively distinguish KLHL20 facial shape variations from other Kelch-like gene family disorders (such as KLHL15) and chromatin-associated syndromic ASDs?
- `d18` — 0.75 — Are there reported homozygous loss-of-function KLHL20 patients in autozygous/consanguineous diagnostic databases (e.g., LODB), and do they exhibit distinct phenotypic features from heterozygous missense cases?
- `d20` — 0.75 — What specific facial metrics or 3D dense-surface facial features systematically differ between individuals with de novo KLHL20 variants and age- and sex-matched neurodevelopmental controls?

## Recent hypotheses (id — status — text)
- `h9` — pooled/supported — Facial dysmorphism in KLHL20-related neurodevelopmental disorder is subtle and non-gestalt-defining, rendering automated
- `h8` — binned/conflicted — The combination of prominent autistic traits and hyperactivity alongside subtle craniofacial dysmorphism differentiates 
- `h7` — binned/refuted — Biallelic loss-of-function variants in KLHL20 yield an expanded, more severe autosomal recessive neurodevelopmental synd
- `h6` — binned/conflicted — Facial dysmorphism in KLHL20-related NEDSFBA constitutes an obligate discriminating signature recognizable by computatio
- `h5` — binned/refuted — In the definitive initial discovery series describing neurodevelopmental disorder with early-onset seizures, facial dysm
- `h4` — binned/refuted — Genotype-phenotype correlations likely reflect variation depending on whether the mechanism is dominant de novo missense
- `h3` — pooled/supported — Negative findings or features whose presence argues against pure KLHL20-related NEDSFBA include prominent neurovisceral 
- `h2` — pooled/supported — Discriminating features that help distinguish KLHL20-related disease from other DEEs (e.g., CDKL5, SCN1A, STXBP1) includ
- `h10` — pooled/supported — In KLHL20-related NEDSFBA, epilepsy manifestations are predominant in infancy and early childhood, whereas behavioral di
- `h1` — binned/conflicted — Primary phenotypic features present in high frequencies (estimated >75% of described individuals) include severe to prof

## Deprioritised — still here, can be brought back (`hypotheses_unbin`)
- `h1` — contested (1 for / 2 against): The hypothesis posits that ID is severe-to-profound in >75% of indivi — Primary phenotypic features present in high frequencies (estimated >75% of described indiv
- `h6` — contested (1 for / 1 against): Sleyp et al. (2022) characterize the facial dysmorphisms in KLHL20-re — Facial dysmorphism in KLHL20-related NEDSFBA constitutes an obligate discriminating signat
- `h8` — contested (2 for / 0 against): Sleyp et al. (2022) found that 2 of 3 patients with non-recurrent mis — The combination of prominent autistic traits and hyperactivity alongside subtle craniofaci
- `h5` — refuted: The available literature source material establishes KLHL20 de novo variants as causative f — In the definitive initial discovery series describing neurodevelopmental disorder with ear
- `h4` — refuted: The hypothesis posits genotype-phenotype correlations contrasting dominant de novo missense — Genotype-phenotype correlations likely reflect variation depending on whether the mechanis
- `h7` — refuted: Extensive literature evaluation reveals that human disease associated with KLHL20 (OMIM #62 — Biallelic loss-of-function variants in KLHL20 yield an expanded, more severe autosomal rec

---
Drop a steer event into the inbox. Keys: `directions_add` [{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` {id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` [str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` [{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], `budget_delta` num, `control` continue|stop_after_round|finalize_now.