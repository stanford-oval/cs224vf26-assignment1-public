# Plain RAG on Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (GTF3C3, OMIM:621201)
model: gemini-3.8-flash   generated: 2026-09-28 20:51

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `GTF3C3 gene Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures`

[1] **Entry - #621201 - NEURODEVELOPMENTAL DISORDER ...**  
    https://omim.org/entry/621201?search=prefix%3A%23&highlight=None  
    Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (NEDFBS) is an autosomal recessive disorder characterized by microcephaly, ...

[2] **Biallelic variants in GTF3C3 encoding a subunit of the TFIIIC2 ...**  
    https://pmc.ncbi.nlm.nih.gov/articles/PMC11878552/  
    by MS Abdel-Hamid · 2025 · Cited by 5 — Knockout of the GTF3C3 ortholog in zebrafish recapitulated the key clinical symptoms including microcephaly, brain anomalies and seizure susceptibility. We also ...

[3] **Neurodevelopmental Disorder with Dysmorphic Facies ...**  
    https://www.malacards.org/card/neurodevelopmental_disorder_with_dysmorphic_facies_brain_anomalies_and_seizures  
    Overall, the disorder is defined by early neurodevelopmental impairment combined with distinctive craniofacial features and structural brain involvement.

[4] **GTF3C3**  
    https://panelapp-aus.org/panels/entities/GTF3C3  
    Phenotypes. Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures, MIM# 621201. Green GTF3C3 in Genetic Epilepsy. Level 2 ...

[5] **Article Biallelic variants in GTF3C3 result in an autosomal ...**  
    https://www.sciencedirect.com/science/article/pii/S1098360024001874  
    by L De Hayr · 2025 · Cited by 4 — This study details a novel syndromic form of autosomal recessive intellectual disability resulting from recessive variants in GTF3C3, encoding a key ...

[6] **GTF3C3-related neurodevelopmental disorders**  
    https://ern-ithaca.eu/for-clinicians/calls-for-collaboration/gtf3c3-related-neurodevelopmental-disorders/  
    We have already gathered a group of patients presenting with microcephaly, developmental delay, dysmorphic facies, intelectual disability, and brain anomalies.

## 2. The context handed to the model
```
[1] Entry - #621201 - NEURODEVELOPMENTAL DISORDER ...
https://omim.org/entry/621201?search=prefix%3A%23&highlight=None
Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (NEDFBS) is an autosomal recessive disorder characterized by microcephaly, ...

[2] Biallelic variants in GTF3C3 encoding a subunit of the TFIIIC2 ...
https://pmc.ncbi.nlm.nih.gov/articles/PMC11878552/
by MS Abdel-Hamid · 2025 · Cited by 5 — Knockout of the GTF3C3 ortholog in zebrafish recapitulated the key clinical symptoms including microcephaly, brain anomalies and seizure susceptibility. We also ...

[3] Neurodevelopmental Disorder with Dysmorphic Facies ...
https://www.malacards.org/card/neurodevelopmental_disorder_with_dysmorphic_facies_brain_anomalies_and_seizures
Overall, the disorder is defined by early neurodevelopmental impairment combined with distinctive craniofacial features and structural brain involvement.

[4] GTF3C3
https://panelapp-aus.org/panels/entities/GTF3C3
Phenotypes. Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures, MIM# 621201. Green GTF3C3 in Genetic Epilepsy. Level 2 ...

[5] Article Biallelic variants in GTF3C3 result in an autosomal ...
https://www.sciencedirect.com/science/article/pii/S1098360024001874
by L De Hayr · 2025 · Cited by 4 — This study details a novel syndromic form of autosomal recessive intellectual disability resulting from recessive variants in GTF3C3, encoding a key ...

[6] GTF3C3-related neurodevelopmental disorders
https://ern-ithaca.eu/for-clinicians/calls-for-collaboration/gtf3c3-related-neurodevelopmental-disorders/
We have already gathered a group of patients presenting with microcephaly, developmental delay, dysmorphic facies, intelectual disability, and brain anomalies.
```

## 3. The gene, from the sources

The *GTF3C3* gene encodes a key subunit of the TFIIIC2 complex, although further details regarding its specific actions in the cell are not covered in the provided sources [2, 5]. Biallelic, recessive variants in *GTF3C3* cause an autosomal recessive condition designated as neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (NEDFBS) [1, 4, 5]. Affected individuals present with early neurodevelopmental impairment, developmental delay, intellectual disability, and distinctive dysmorphic craniofacial features [1, 3, 5, 6]. Clinical manifestations also prominently include microcephaly, structural brain anomalies, and seizures [1, 2, 3, 6]. In functional studies, knockout of the *GTF3C3* ortholog in zebrafish recapitulated these key human symptoms by inducing microcephaly, brain anomalies, and seizure susceptibility [2]. Aside from these findings, the precise molecular mechanisms by which *GTF3C3* variants disrupt cellular processes to produce the disorder are not covered in the text [2, 5].

*tokens in 623, out 2262*

## 4. The gene, closed book (no sources; beware hallucinations)

***GTF3C3* (General Transcription Factor IIIC Subunit 3)** encodes a core structural component of the human TFIIIC complex, an essential multi-protein factor for RNA polymerase III (Pol III) transcription. TFIIIC binds directly to promoter elements (box A and box B) on Pol III-dependent genes—primarily transfer RNAs (tRNAs) and 5S ribosomal RNA—recruiting TFIIIB and Pol III to initiate transcription, which is vital for protein synthesis and cellular growth.

Biallelic pathogenic variants (missense, nonsense, or splice-site) in *GTF3C3* impair TFIIIC assembly, stability, or DNA-binding capability. This leads to compromised Pol III transcription, depleted cellular tRNA pools

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P01)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The sources define GTF3C3-related neurodevelopmental disorder (NEDFBS, OMIM #621201) by a core constellation of:
* **Microcephaly** [1, 2, 6]
* **Dysmorphic facies / distinctive craniofacial features** [1, 3, 6]
* **Structural brain anomalies** [1, 2, 3, 6]
* **Seizures / seizure susceptibility** [1, 2, 4]
* **Developmental delay / intellectual disability** [3, 5, 6]

Because the sources do not provide complete penetrance statistics, full exclusion criteria, or granular HPO profiles [1–6], definitive exclusion or confirmation based solely on the provided text has limitations; however, comparing against the core syndrome criteria establishes the following:

* **P01**: **Ruled out**. Lacks microcephaly [1, 2, 6], structural brain anomalies [1, 2, 3, 6], and seizures [1, 2, 4].
* **P02**: **Ruled out**. Lacks microcephaly [1, 2, 6] and structural brain anomalies [1, 2, 3, 6].
* **P03**: **Ruled out**. Lacks microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], and seizures (only myoclonus and tremor are noted) [1, 2, 4].
* **P04**: **Ruled out**. Lacks microcephaly [1, 2, 6].
* **P05**: **Cannot be ruled out / Possible candidate**. Displays all cardinal features: primary microcephaly [1, 2, 6], dysmorphic facies (epicanthus, broad nasal tip, wide nasal bridge) [1, 3, 6], multiple structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and severe global developmental delay/intellectual disability [3, 5, 6]. However, the sources do not provide the detailed imaging or phenotypic profile to confirm this patient [1–6].
* **P06**: **Ruled out**. Lacks microcephaly [1, 2, 6], structural brain anomalies [1, 2, 3, 6], and seizures [1, 2, 4].
* **P07**: **Cannot be ruled out / Possible candidate**. Displays all cardinal features: primary microcephaly [1, 2, 6], dysmorphic facial features [1, 3, 6], structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and developmental delay/intellectual disability [3, 5, 6]. Cannot be confirmed because specific anomaly patterns are not detailed in the sources [1–6].
* **P08**: **Cannot be ruled out / Possible candidate**. Displays all cardinal features: secondary microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], structural brain anomalies/atrophy [1, 2, 3, 6], multiple seizure types [1, 2, 4], and severe developmental delay [3, 5, 6]. Cannot be confirmed due to lack of detailed phenotypic data in the sources [1–6].
* **P09**: **Cannot be ruled out / Possible candidate**. Displays all cardinal features: microcephaly [1, 2, 6], craniofacial/dental features [1, 3, 6], structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and severe intellectual disability [3, 5, 6]. Cannot be confirmed due to lack of detailed phenotypic data in the sources [1–6].
* **P10**: **Ruled out**. Lacks microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], structural brain anomalies [1, 2, 3, 6], and seizures [1, 2, 4].

---

### 2. Most Likely Patient and Estimated Probability

* **Most likely candidate**: Any one of **P05, P07, P08, or P09** (for example, **P05**).
* **Estimated Probability**: **~25% (0.25)**. 
* **Justification**: Four patients (P05, P07, P08, P09) present with every broad defining feature reported in the sources (microcephaly, dysmorphic facies, structural brain anomalies, seizures, and intellectual disability) [1, 2, 3, 4, 6]. Because the provided sources contain only high-level summary descriptions and lack detailed clinical or neuroimaging criteria, it is impossible based strictly on the text provided to differentiate which of these four is the true GTF3C3 case.

---

### 3. Missing Information Needed for Confidence

To confidently identify the exact patient, the following information (absent from sources [1–6]) is required:
1. **Specific neuroimaging findings**: The sources only state generic "brain anomalies" / "structural brain involvement" [1, 2, 3, 6] without specifying whether GTF3C3 causes simplified gyral patterns, pontocerebellar hypoplasia, periventricular nodular heterotopia, or white matter atrophy.
2. **Specific craniofacial dysmorphisms**: The sources state only "dysmorphic facies" / "distinctive craniofacial features" [1, 3, 6] without listing the specific facial characteristics.
3. **Microcephaly timing**: Clarification on whether microcephaly is congenital (primary) or progressive/postnatal (secondary) [1, 2, 6].
4. **Epilepsy phenotype**: The specific seizure types or interictal EEG patterns characteristic of biallelic *GTF3C3* variants [1, 2, 4].
5. **Detailed case reports/cohort data**: The specific clinical vignettes, HPO terms, or variant-level descriptions from the cited publications [2, 5, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P05)

Based on the provided sources, the condition **Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (NEDFBS)** caused by biallelic variants in *GTF3C3* is characterized by:
- Microcephaly [1, 2, 6]
- Structural brain anomalies [1, 2, 3, 6]
- Seizures / seizure susceptibility [1, 2, 4]
- Dysmorphic facies / distinctive craniofacial features [1, 3, 6]
- Early neurodevelopmental impairment / intellectual disability / developmental delay [1, 3, 5, 6]

---

### 1. Patient Rule-In / Rule-Out Evaluation

* **P01**: **Ruled out**. Lacks microcephaly, brain anomalies, and seizures, which are cardinal defining features of NEDFBS [1, 2, 3, 4, 6].
* **P02**: **Ruled out**. Lacks microcephaly and structural brain anomalies [1, 2, 3, 6].
* **P03**: **Ruled out**. Lacks microcephaly and dysmorphic facies, and has myoclonus/tremor rather than the defined seizure disorder [1, 2, 3, 4, 6].
* **P04**: **Ruled out**. Lacks microcephaly, a key clinical hallmark [1, 2, 6].
* **P05**: **Cannot be definitively ruled in or out**. Possesses all core features: primary microcephaly [1, 2, 6], dysmorphic facies (epicanthus, broad nasal bridge/tip) [1, 3, 6], structural brain anomalies (agenesis of corpus callosum, simplified gyral pattern, brainstem/pons/cerebellar hypoplasia) [1, 2, 3, 6], seizures [1, 2, 4], and severe global developmental delay/intellectual disability [1, 3, 5, 6]. However, the sources do not provide patient-specific HPO terms to confirm this specific individual [1–6].
* **P06**: **Ruled out**. Lacks microcephaly, structural brain anomalies, and seizures [1, 2, 3, 4, 6].
* **P07**: **Cannot be definitively ruled in or out**. Possesses all core features: primary microcephaly [1, 2, 6], dysmorphic facies (short chin, flat face, sloping forehead) [1, 3, 6], structural brain anomalies (periventricular nodular heterotopia, thin corpus callosum, Chiari malformation) [1, 2, 3, 6], seizures [1, 2, 4], and intellectual disability/developmental delay [1, 3, 5, 6]. The sources lack granular profiles to confirm this patient [1–6].
* **P08**: **Cannot be definitively ruled in or out**. Possesses all core features: secondary microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], structural brain anomalies (brain atrophy, delayed myelination, hypoplastic hippocampus, small basal ganglia) [1, 2, 3, 6], seizures/status epilepticus [1, 2, 4], and severe global developmental delay [1, 3, 5, 6]. The sources do not contain case-level details to rule them in [1–6].
* **P09**: **Cannot be definitively ruled in or out**. Possesses all core features: microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], structural brain anomalies (cerebellar atrophy, hypoplasia of the corpus callosum) [1, 2, 3, 6], seizures [1, 2, 4], and severe intellectual disability [1, 3, 5, 6]. The sources lack individual-level phenotypic data to confirm this patient [1–6].
* **P10**: **Ruled out**. Lacks microcephaly, dysmorphic facies, structural brain anomalies, and seizures [1, 2, 3, 4, 6].

*(Note: While P01, P02, P03, P04, P06, and P10 are ruled out based on the absence of core defining criteria, the sources do not explicitly describe the full negative phenotypic spectrum or variable expressivity [1–6].)*

---

### 2. Most Likely Patient and Estimated Probability

* **Most Likely Patient**: **P05** (tied with **P07**, **P08**, and **P09**). 
* **Probability**: **~25%** (approximately 1 in 4).

**Reasoning**: Patients P05, P07, P08, and P09 all fully satisfy the cardinal constellation of NEDFBS (microcephaly, dysmorphic facies, structural brain anomalies, seizures, and developmental delay/intellectual disability) [1, 2, 3, 4, 6]. Because the provided sources do not include granular clinical descriptions, individual patient HPO profiles, or neuroimaging specifics, it is impossible based strictly on sources [1–6] to distinguish between these four candidates.

---

### 3. Facts Needed but Not Provided by the Sources

To make a confident diagnosis among the potential candidates, the following information is required and absent from the sources:
1. **Specific Genetic Data**: Identification of biallelic pathogenic/likely pathogenic variants in *GTF3C3* in the patient [2, 5].
2. **Granular Brain MRI Phenotypes**: Specific structural anomalies associated with *GTF3C3* variants (e.g., whether the disorder specifically causes simplified gyral pattern/callosal agenesis as in P05, heterotopia as in P07, progressive atrophy as in P08, or cerebellar/corpus callosum hypoplasia as in P09) [1, 2, 3, 6].
3. **Specific Craniofacial Spectrum**: The exact "distinctive craniofacial features" or dysmorphic signs characteristic of *GTF3C3* deficiency [1, 3, 6].
4. **Natural History & Onset Data**: Whether the microcephaly is consistently congenital (primary) or postnatal (secondary), and the precise seizure types characteristic of the condition [1, 2, 4, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based on the provided sources, the condition **Neurodevelopmental disorder with dysmorphic facies, brain anomalies, and seizures (NEDFBS)**, caused by biallelic variants in *GTF3C3*, is defined by the core clinical constellation of:
* Microcephaly [1, 2, 6]
* Structural brain anomalies [1, 2, 3, 6]
* Seizures / seizure susceptibility [1, 2, 4]
* Dysmorphic craniofacial features [1, 3, 6]
* Intellectual disability / global developmental delay [1, 3, 5, 6]

---

### 1. Patient Evaluation (Rule-in / Rule-out)

The provided excerpts contain only high-level syndrome summaries and do **not** provide complete clinical synopses, specific HPO terms, individual case reports, or penetrance figures [1–6]. Consequently:
* **Definitive rule-in** is **not possible** for any patient because the sources do not provide genetic data, pathogenic variant details, or patient-specific matching criteria [1–6].
* **Definitive rule-out** is strictly **not possible** from the text alone, as the sources do not specify whether any of the cardinal features have incomplete penetrance [1–6]. However, several patients lack the key cardinal features defining the disorder:

* **P01**: **Cannot be ruled in**; lacks microcephaly [1, 2, 6], brain anomalies [1, 2, 3, 6], and seizures [1, 2, 4]. A definitive rule-out cannot be confirmed because the sources do not explicitly state non-penetrance rates [1–6].
* **P02**: **Cannot be ruled in**; has seizures and dysmorphic features, but lacks microcephaly [1, 2, 6] and structural brain anomalies [1, 2, 3, 6]. Cannot be definitively ruled out due to lack of exclusion criteria in the sources [1–6].
* **P03**: **Cannot be ruled in**; has brain anomalies and developmental delay, but lacks microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], and seizures [1, 2, 4]. Cannot be definitively ruled out based on the sources alone [1–6].
* **P04**: **Cannot be ruled in**; has dysmorphic features, seizures, brain anomalies, and intellectual disability, but lacks microcephaly [1, 2, 6]. Cannot be definitively ruled out from the text [1–6].
* **P05**: **Cannot be ruled in or ruled out**; possesses all cardinal features mentioned in the sources: primary microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], multiple structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and intellectual disability/global delay [1, 3, 5, 6]. However, the sources lack specific clinical or molecular details to confirm this patient [1–6].
* **P06**: **Cannot be ruled in**; lacks microcephaly [1, 2, 6], seizures [1, 2, 4], and brain anomalies [1, 2, 3, 6]. Cannot be definitively ruled out based on the sources [1–6].
* **P07**: **Cannot be ruled in or ruled out**; possesses all cardinal features: primary microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and developmental delay/intellectual disability [1, 3, 5, 6]. The sources lack patient-specific identifiers or genetic confirmation [1–6].
* **P08**: **Cannot be ruled in or ruled out**; possesses all cardinal features: secondary microcephaly [1, 2, 6], dysmorphic facies [1, 3, 6], structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and developmental delay [1, 3, 5, 6]. The sources do not provide sufficient granularity to confirm [1–6].
* **P09**: **Cannot be ruled in or ruled out**; possesses all cardinal features: microcephaly [1, 2, 6], dysmorphic facial features [1, 3, 6], structural brain anomalies [1, 2, 3, 6], seizures [1, 2, 4], and severe intellectual disability [1, 3, 5, 6]. The sources do not provide sufficient detail to confirm [1–6].
* **P10**: **Cannot be ruled in**; lacks microcephaly [1, 2, 6], seizures [1, 2, 4], dysmorphic facies [1, 3, 6], and structural brain anomalies [1, 2, 3, 6]. Cannot be definitively ruled out from the text alone [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most likely candidate**: Four patients (**P05**, **P07**, **P08**, and **P09**) exhibit the complete cardinal pentad (intellectual disability/developmental delay, microcephaly, dysmorphic facies, structural brain anomalies, and seizures) [1, 2, 3, 4, 6]. 
* Because **P05** displays classic, severe congenital structural brain involvement (agenesis of corpus callosum, simplified gyral pattern, cerebellar/brainstem hypoplasia) combined with primary microcephaly, dysmorphic facies, and seizures [1, 2, 3], **P05** is an exemplary candidate.
* **Estimated Probability**: **~25%** (approximately 1 in 4 among the four candidates matching all cardinal features). Based strictly on the provided text, the sources do not provide distinguishing criteria to elevate any one of P05, P07, P08, or P09 above the others.

---

### 3. Facts Needed to Be Confident (Missing from Sources)

To establish a definitive diagnosis, the following information is required but missing from sources [1–6]:
1. **Genetic / Molecular Data**: Identification of biallelic pathogenic or likely pathogenic variants in *GTF3C3* [2, 5].
2. **Specific Neuroimaging Profiles**: A detailed breakdown of the exact brain anomalies characteristic of *GTF3C3* deficiency (e.g., whether simplified gyral pattern, periventricular nodular heterotopia, or hypomyelination is the primary pattern) [1, 2, 3, 6].
3. **Specific Craniofacial Phenotype**: Detailed descriptions of the "dysmorphic facies" / "distinctive craniofacial features" to distinguish from overlapping syndromes [1, 3, 6].
4. **Epilepsy Characterization**: Specific seizure semiology and EEG patterns associated with *GTF3C3* variants [1, 2, 4].
5. **Penetrance and Exclusion Criteria**: Quantitative clinical data on whether microcephaly, seizures, or specific brain malformations are obligate (100% penetrant) features of the disorder [1–6].

--------------------------------------------------------------------------------

picks across rounds: ['P01', 'P05', 'P01']
