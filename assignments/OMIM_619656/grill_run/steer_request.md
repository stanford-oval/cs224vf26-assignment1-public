# Steering digest — round 1

**Question:** For Loeys-Dietz syndrome 6 (OMIM #619656), caused by variants in SMAD2: how can one identify which patients
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

- spent: $0.32 / $10.00  (init $0.04  plan $0.00  explore $0.03  screen $0.08  deep $0.16  measure $0.00)
- hypotheses: 12 — 2 pooled, 10 binned, 0 awaiting a test
- evidence items: 60
- open directions: 39
- uncovered asks: ['Clinical phenotypes reported in affected individuals with SMAD2-related Loeys-Dietz syndrome 6, including exact numerator and denominator per cohort (not percentage alone), the finding as worded in the paper, and the standard HPO term if identifiable', 'Most discriminating findings that are present in most affected individuals but uncommon in overlapping disorders, including naming the confused disorders and stating the confidence of the distinction', 'Findings looked for and found absent in affected individuals, whose presence would argue against the diagnosis', 'Analysis of whether the phenotype differs by variant type, variant position, age, or sex', 'Any finding that one paper reports and another explicitly contradicts', 'Attachment of every reported phenotype frequency to its specific cohort and resolvable source citation (PMID or DOI)']

## Top open directions (id — promise — question)
- `d19` — 0.85 — What is the pooled frequency of bifid uvula vs cleft palate when extracted specifically from the primary cohort papers describing the original SMAD2/LDS6 series (e.g. Micha et al. 2015, Cannaerts et al. 2019)?
- `d21` — 0.85 — What are the exact maximal aortic diameters documented at the time of acute aortic dissection across all published SMAD2 cases?
- `d23` — 0.85 — Resolve the conflict over: In seminal SMAD2 pathogenic variant cohorts, thoracic aortic aneurysm (dilation) manifests in approximately two-thirds of assessed carriers (specifically 10/15 in the 2019 delineation cohort), whereas acute aortic dissection is substantially less frequent at initial clinical ascertainment.
- `d24` — 0.85 — What is the penetrance and median age of onset of acute aortic dissection versus isolated thoracic aneurysm in larger international SMAD2 registries?
- `d25` — 0.85 — Resolve the conflict over: Genotype-phenotype correlation exists between variant location/type and severity: missense variants in the conserved MH2 domain altering phosphorylation or protein-protein interaction interfaces often correlate with early-onset, severe syndromic vasculopathy, whereas some heterozygous truncating/haploinsufficiency variants present with milder, later-onset thoracic aortic aneurysms without overt craniofacial findings.
- `d27` — 0.85 — Do SMAD2 MH2 domain missense mutations exhibit measurable dominant-negative activity compared to haploinsufficiency in human induced pluripotent stem cell-derived vascular smooth muscle cells?
- `d29` — 0.85 — What is the true penetrance of the cardinal craniofacial triad in SMAD2 variant carriers when stratified by ascertainment mechanism (proband vs cascade testing)?
- `d31` — 0.85 — Resolve the conflict over: Aortic dissection in SMAD2-associated Loeys-Dietz syndrome 6 occurs predominantly secondary to antecedent, clinically detectable thoracic aortic root or ascending aortic aneurysm dilation, rather than presenting as catastrophic dissection at normal or near-normal aortic calibers (<40 mm).
- `d32` — 0.85 — What is the exact aortic root and ascending aortic diameter at the time of acute type A or B aortic dissection in an international multicenter registry of confirmed SMAD2 pathogenic variant carriers?
- `d34` — 0.85 — Resolve the conflict over: Missense variants clustered in the conserved MH2 signaling domain of SMAD2 confer a higher risk of progressing from aneurysm to acute aortic dissection compared to upstream truncating or null alleles.
- `d35` — 0.85 — Does an international multi-center registry of SMAD2 variant carriers show a statistically significant hazard ratio for acute aortic dissection in MH2 domain missense versus loss-of-function variants after adjusting for aortic diameter and blood pressure?
- `d38` — 0.85 — What is the true penetrance of palatal abnormalities (cleft palate, submucous cleft, and bifid uvula) across pooled, verified international registries of heterozygous SMAD2 pathogenic variant carriers?
- `d41` — 0.85 — What are the exact numerators and denominators of overt cleft palate, bifid uvula, and hypertelorism in systematically curated registries of SMAD2 pathogenic variant carriers?
- `d26` — 0.80 — Does transcript-level nonsense-mediated decay efficiency in SMAD2 truncating variants dictate whether a patient develops early complex congenital heart disease versus adult-onset aneurysms?
- `d36` — 0.80 — Do patient-derived smooth muscle cells carrying MH2 missense SMAD2 variants exhibit dominant-negative disruption of heteromeric transcriptional complexes compared to heterozygous null cell lines?

## Recent hypotheses (id — status — text)
- `h9` — binned/refuted — Bifid uvula (HP:0000193) serves as a more sensitive discriminator of SMAD2-mediated LDS than overt cleft palate or syste
- `h8` — binned/refuted — Overt cleft palate (HP:0000175) has an overall penetrance of less than 15% across all published SMAD2 mutation carriers,
- `h7` — binned/refuted — The documented penetrance of cardinal craniofacial features (hypertelorism HP:0000316, bifid uvula HP:0000193, or cleft 
- `h6` — binned/conflicted — Genotype-phenotype correlation exists between variant location/type and severity: missense variants in the conserved MH2
- `h5` — pooled/supported — Significant intellectual disability or craniosynostosis is absent or exceedingly rare in typical SMAD2-associated LDS6, 
- `h4` — binned/conflicted — Ectopia lentis (HP:0001083) has been systematically documented as absent in verified SMAD2/LDS6 cases, making the presen
- `h3` — binned/refuted — Craniofacial features including hypertelorism (HP:0000316) and bifid uvula (HP:0000193) or cleft palate (HP:0000175) are
- `h2` — binned/refuted — Arterial tortuosity (HP:0001053) affecting head/neck/vertebral and branch vessels is present in approximately 40-70% of 
- `h12` — binned/conflicted — Missense variants clustered in the conserved MH2 signaling domain of SMAD2 confer a higher risk of progressing from aneu
- `h11` — binned/conflicted — Aortic dissection in SMAD2-associated Loeys-Dietz syndrome 6 occurs predominantly secondary to antecedent, clinically de
- `h10` — binned/conflicted — In seminal SMAD2 pathogenic variant cohorts, thoracic aortic aneurysm (dilation) manifests in approximately two-thirds o
- `h1` — pooled/supported — Thoracic aortic aneurysm and dissection (HP:0002616 / HP:0002617) occurs in a majority of published symptomatic SMAD2 ki

## Deprioritised — still here, can be brought back (`hypotheses_unbin`)
- `h4` — contested (3 for / 1 against): Established diagnostic dogma asserts that ectopia lentis is universal — Ectopia lentis (HP:0001083) has been systematically documented as absent in verified SMAD2
- `h10` — contested (2 for / 2 against): Foundational discovery reports identified acute arterial dissections  — In seminal SMAD2 pathogenic variant cohorts, thoracic aortic aneurysm (dilation) manifests
- `h12` — contested (4 for / 1 against): Aortic dissection has been documented in carriers of truncating SMAD2 — Missense variants clustered in the conserved MH2 signaling domain of SMAD2 confer a higher
- `h11` — contested (1 for / 1 against): General LDS guidelines and reviews document that aortic dissection oc — Aortic dissection in SMAD2-associated Loeys-Dietz syndrome 6 occurs predominantly secondar
- `h2` — refuted: The literature confirms that widespread arterial tortuosity is a key phenotypic hallmark di — Arterial tortuosity (HP:0001053) affecting head/neck/vertebral and branch vessels is prese
- `h6` — contested (3 for / 2 against): The hypothesis asserts that truncating/haploinsufficiency variants ca — Genotype-phenotype correlation exists between variant location/type and severity: missense
- `h3` — refuted: The literature provided confirms that heterozygous variants in SMAD2 cause Loeys-Dietz synd — Craniofacial features including hypertelorism (HP:0000316) and bifid uvula (HP:0000193) or
- `h7` — refuted: The literature provided in the SOURCES block provides no empirical or statistical support f — The documented penetrance of cardinal craniofacial features (hypertelorism HP:0000316, bif
- `h8` — refuted: The available literature provided in the sources acknowledges that SMAD2 mutations cause Lo — Overt cleft palate (HP:0000175) has an overall penetrance of less than 15% across all publ
- `h9` — refuted: The available literature does not support the hypothesis that bifid uvula (HP:0000193) is p — Bifid uvula (HP:0000193) serves as a more sensitive discriminator of SMAD2-mediated LDS th

---
Drop a steer event into the inbox. Keys: `directions_add` [{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` {id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` [str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` [{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], `budget_delta` num, `control` continue|stop_after_round|finalize_now.