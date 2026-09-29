# Steering digest — round 1

**Question:** For Intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (OMIM #618089), caused by variants in FBXO11: how can one identify which patients
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

- spent: $0.37 / $10.00  (init $0.04  plan $0.00  explore $0.04  screen $0.10  deep $0.19  measure $0.00)
- hypotheses: 13 — 5 pooled, 8 binned, 0 awaiting a test
- evidence items: 65
- open directions: 40
- uncovered asks: ['Clinical phenotypes reported in affected individuals with FBXO11-related intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (OMIM #618089), including exact cohort-specific counts (numerator and denominator per cohort, not percentages alone), original paper wording, standard HPO terms if identifiable, and citation with PMID or DOI.', 'Most discriminating clinical findings present in most affected individuals but uncommon in overlapping/confusable disorders, including names of those disorders and the confidence of the distinction.', 'Findings looked for and found absent in affected individuals whose presence would argue against the diagnosis (pertinent negatives).', 'Analysis of whether phenotype differs by variant type, variant position, age, or sex.', 'Any findings or phenotypic characteristics that one paper reports and another explicitly contradicts.']

## Top open directions (id — promise — question)
- `d19` — 0.85 — Does the frequency of microcephaly (HP:0000252) versus macrocephaly (HP:0000256) differ by variant class (truncating loss-of-function vs missense) across pooled post-2018 FBXO11 cohorts?
- `d24` — 0.85 — Can computational facial phenotyping (e.g., GestaltMatcher) reliably discriminate FBXO11-related disorder from clinically overlapping neurodevelopmental disorders sharing hypotonia and behavioral dysregulation?
- `d25` — 0.85 — Is the TRPS-like presentation restricted exclusively to specific missense variants in the functional domains of FBXO11, or can loss-of-function (truncating/frameshift) variants also cause nail hypoplasia and cone-shaped epiphyses?
- `d26` — 0.85 — Do FBXO11 truncating/nonsense variants versus missense variants localized to specific functional domains (e.g., F-box domain vs. UBR Zn-finger domain) correlate with the severity and penetrance of behavioral abnormalities?
- `d28` — 0.85 — Resolve the conflict over: Seizures occur in 25-45% of FBXO11 variant carriers, representing a substantially more frequent neurological feature than described in initial index cohorts and functioning as an active discriminating sign.
- `d30` — 0.85 — How do quantitative facial gestalt algorithms (e.g., GestaltMatcher) perform in differentiating FBXO11 from clinically overlapping intellectual disability syndromes?
- `d31` — 0.85 — Resolve the conflict over: The simultaneous presence of axial/congenital hypotonia (HP:0001252) alongside disruptive behavioral disturbances (HP:0000708) is a distinctive signature of FBXO11-related disorder that differentiates it from non-syndromic ADHD or purely hyperactive neurobehavioral conditions.
- `d34` — 0.85 — Resolve the conflict over: The neurobehavioral phenotype in FBXO11 deficiency exhibits longitudinal age-dependent evolution, transitioning from childhood hyperactive/aggressive dysregulation (ADHD, temper tantrums) to adolescent and adult internalizing psychiatric symptoms such as anxiety and depression.
- `d35` — 0.85 — Does standardized longitudinal psychiatric assessment in a multi-center cohort of FBXO11 mutation carriers reveal true age-dependent symptom evolution versus lifetime cumulative comorbidity?
- `d37` — 0.85 — Resolve the conflict over: Overt craniofacial dysmorphism is penetrant in only approximately two-thirds of FBXO11-related disorder cases (ca. 60-67%) and can be subtle or clinically non-evident, rather than serving as an obligatory diagnostic hallmark across all affected cohorts.
- `d38` — 0.85 — Does computer-aided objective facial gestalt analysis (e.g., GestaltMatcher) detect subtle sub-clinical facial signatures in FBXO11 variant carriers who are clinically designated as non-dysmorphic?
- `d40` — 0.85 — Resolve the conflict over: Increased body weight or obesity (HP:0001513) is a recurrent feature in FBXO11-related disorder that occurs in over 50% of specific cohorts, distinguishing it from syndromic intellectual disability entities characterized by growth failure or cachexia.
- `d41` — 0.85 — Does FBXO11 variant type (loss-of-function/truncating vs missense) systematically govern metabolic phenotype vs growth failure?
- `d21` — 0.82 — Does the prevalence and severity of disruptive externalizing behaviors correlate with variant class (truncating/loss-of-function versus domain-specific missense variants) or inheritance mode (de novo vs familial transmission) in FBXO11?
- `d27` — 0.80 — What proportion of adults harboring inherited FBXO11 variants meet formal diagnostic criteria for neuropsychiatric conditions compared to pediatric probands identified via de novo sequencing?

## Recent hypotheses (id — status — text)
- `h9` — binned/conflicted — Increased body weight or obesity (HP:0001513) is a recurrent feature in FBXO11-related disorder that occurs in over 50% 
- `h8` — binned/conflicted — Seizures occur in 25-45% of FBXO11 variant carriers, representing a substantially more frequent neurological feature tha
- `h7` — binned/conflicted — Overt craniofacial dysmorphism is penetrant in only approximately two-thirds of FBXO11-related disorder cases (ca. 60-67
- `h6` — pooled/supported — Most variants represent haploinsufficiency via de novo loss-of-function (frameshift, nonsense, canonical splice site mut
- `h5` — pooled/supported — Features that are consistently absent or rare (acting as negative discriminators) include progressive neurodegeneration,
- `h4` — binned/conflicted — Discrimination against Coffin-Siris syndrome (ARID1B and related genes) relies on the absence of hypoplastic or absent f
- `h3` — binned/conflicted — Recurrent craniofacial dysmorphisms include prominent forehead/frontal bossing (HP:0002007), broad nasal tip (HP:0000455
- `h2` — binned/conflicted — Behavioral abnormalities (HP:0000708) including hyperactivity/ADHD (HP:0007018), aggressive behavior (HP:0000718), and a
- `h13` — binned/conflicted — The neurobehavioral phenotype in FBXO11 deficiency exhibits longitudinal age-dependent evolution, transitioning from chi
- `h12` — binned/conflicted — The simultaneous presence of axial/congenital hypotonia (HP:0001252) alongside disruptive behavioral disturbances (HP:00
- `h11` — pooled/supported — Behavioral dysregulation (HP:0000708) in FBXO11-related neurodevelopmental disorder is an incompletely penetrant feature
- `h10` — pooled/supported — Nail hypoplasia (HP:0001792) and pear-shaped nose (HP:0000447) do not reliably exclude FBXO11 variants, as specific FBXO

## Deprioritised — still here, can be brought back (`hypotheses_unbin`)
- `h7` — contested (3 for / 1 against): Published literature review calculates the penetrance of facial dysmo — Overt craniofacial dysmorphism is penetrant in only approximately two-thirds of FBXO11-rel
- `h2` — contested (3 for / 2 against): Cohort penetrance discrepancy: Gregor et al. (2018) documented behavi — Behavioral abnormalities (HP:0000708) including hyperactivity/ADHD (HP:0007018), aggressiv
- `h9` — contested (4 for / 1 against): Increased body weight exceeded 50% in one familial Chinese cohort (7/ — Increased body weight or obesity (HP:0001513) is a recurrent feature in FBXO11-related dis
- `h3` — contested (4 for / 2 against): While high/broad forehead, broad nasal tip, hypertelorism, and thin u — Recurrent craniofacial dysmorphisms include prominent forehead/frontal bossing (HP:0002007
- `h4` — contested (3 for / 2 against): Published FBXO11 cohorts (Jansen et al. 2019, Gregor et al. 2022) emp — Discrimination against Coffin-Siris syndrome (ARID1B and related genes) relies on the abse
- `h8` — contested (3 for / 2 against): The initial index cohort (Gregor et al. 2018) already observed seizur — Seizures occur in 25-45% of FBXO11 variant carriers, representing a substantially more fre
- `h12` — contested (2 for / 0 against): Hypotonia prevalence varies sharply between cohorts, ranging from 60- — The simultaneous presence of axial/congenital hypotonia (HP:0001252) alongside disruptive 
- `h13` — contested (2 for / 2 against): Externalizing symptoms (hyperactivity, ADHD, and aggressive behaviora — The neurobehavioral phenotype in FBXO11 deficiency exhibits longitudinal age-dependent evo

---
Drop a steer event into the inbox. Keys: `directions_add` [{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` {id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` [str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` [{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], `budget_delta` num, `control` continue|stop_after_round|finalize_now.