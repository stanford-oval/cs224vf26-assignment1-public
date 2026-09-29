# Plain RAG on Intellectual developmental disorder, autosomal dominant 77 (LRRC7, OMIM:621415)
model: gemini-3.8-flash   generated: 2026-09-28 20:53

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `LRRC7 gene Intellectual developmental disorder, autosomal dominant 77`

[1] **621415 - INTELLECTUAL DEVELOPMENTAL DISORDER, ...**  
    https://omim.org/entry/621415  
    Autosomal dominant intellectual developmental disorder-77 (MRD77) is characterized by global developmental delay that leads to mild to ...

[2] **Intellectual Developmental Disorder, Autosomal Dominant 77**  
    https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_77  
    Autosomal dominant intellectual developmental disorder-77 (MRD77) is characterized by global developmental delay that leads to mild to moderate intellectual ...

[3] **LRRC7 gene Leucine Rich Repeat Containing 7**  
    https://www.genecards.org/card/LRRC7  
    Diseases associated with LRRC7 include Intellectual Developmental Disorder, Autosomal Dominant 77 and Cocaine Dependence. An important paralog of this gene ...

[4] **Activity**  
    https://panelapp.genomicsengland.co.uk/panels/activity/?panel=285&entity=LRRC7  
    LRRC7, Ida Ertmanska Phenotypes for gene: LRRC7 were changed from neurodevelopmental disorder ... intellectual developmental disorder, autosomal dominant 77, ...

[5] **Variants in LRRC7 lead to intellectual disability, autism ...**  
    https://www.nature.com/articles/s41467-024-52095-x  
    by J Willim · 2024 · Cited by 18 — We identify here 33 individuals (one of them previously described) with a dominant neurodevelopmental disorder due to heterozygous missense or ...

[6] **Relationships**  
    https://zfin.org/action/ontology/term-detail-popup?termID=DOID:0081469  
    An autosomal dominant intellectual developmental disorder that is characterized by global developmental delay that leads to mild to moderate intellectual ...

## 2. The context handed to the model
```
[1] 621415 - INTELLECTUAL DEVELOPMENTAL DISORDER, ...
https://omim.org/entry/621415
Autosomal dominant intellectual developmental disorder-77 (MRD77) is characterized by global developmental delay that leads to mild to ...

[2] Intellectual Developmental Disorder, Autosomal Dominant 77
https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_77
Autosomal dominant intellectual developmental disorder-77 (MRD77) is characterized by global developmental delay that leads to mild to moderate intellectual ...

[3] LRRC7 gene Leucine Rich Repeat Containing 7
https://www.genecards.org/card/LRRC7
Diseases associated with LRRC7 include Intellectual Developmental Disorder, Autosomal Dominant 77 and Cocaine Dependence. An important paralog of this gene ...

[4] Activity
https://panelapp.genomicsengland.co.uk/panels/activity/?panel=285&entity=LRRC7
LRRC7, Ida Ertmanska Phenotypes for gene: LRRC7 were changed from neurodevelopmental disorder ... intellectual developmental disorder, autosomal dominant 77, ...

[5] Variants in LRRC7 lead to intellectual disability, autism ...
https://www.nature.com/articles/s41467-024-52095-x
by J Willim · 2024 · Cited by 18 — We identify here 33 individuals (one of them previously described) with a dominant neurodevelopmental disorder due to heterozygous missense or ...

[6] Relationships
https://zfin.org/action/ontology/term-detail-popup?termID=DOID:0081469
An autosomal dominant intellectual developmental disorder that is characterized by global developmental delay that leads to mild to moderate intellectual ...
```

## 3. The gene, from the sources

The *LRRC7* gene, named Leucine Rich Repeat Containing 7, is associated with Intellectual Developmental Disorder, Autosomal Dominant 77 (MRD77) [3, 4]. This condition is characterized by global developmental delay that leads to mild to moderate intellectual disability [2, 6]. Individuals with this dominant neurodevelopmental disorder have been identified with heterozygous missense variants in the *LRRC7* gene [5]. 

Beyond identifying the gene as Leucine Rich Repeat Containing 7 and noting that heterozygous variants lead to intellectual disability and neurodevelopmental disorder, the provided sources do not cover what the specific gene product is, what it does in the cell, or the biological mechanism of how variants cause the disease [3, 5].

*tokens in 517, out 1084*

## 4. The gene, closed book (no sources; beware hallucinations)

The **LRRC7** gene encodes **Densin-180** (leucine-rich repeat-containing protein 7), a core scaffolding protein localized to the postsynaptic density (PSD) of excitatory neurons. Belonging to the LAP (leucine-rich repeat and PDZ) protein family, Densin-180 interacts with essential synaptic organizers, including Shank, CaMKII, and α-actinin, to regulate dendritic spine morphogenesis, glutamate receptor localization, and synaptic plasticity.

**Intellectual developmental disorder, autosomal dominant 77 (IDDAD77; OMIM #620862)** is caused by heterozygous *de novo* or inherited pathogenic variants in *LRRC7*. Most disease-causing variants—including nonsense, frameshift, and copy-number deletions—act through **haploinsufficiency**, while certain missense variants disrupt critical protein–protein interaction domains. This loss of functional Densin-180 destabilizes PSD architecture, impairs excitatory synaptic transmission, and disrupts neural circuit development, leading to developmental delays, intellectual disability, and frequent features of autism spectrum disorder.

The clinical condition was formally delineated in **2023**. 

**Key Citation:**
*   OMIM Phenotype Entry: **#620862** (Intellectual Developmental Disorder, Autosomal Dominant 77; established 2023). 
*   *Seminal delineation:* Deciphering Developmental Disorders (DDD) Study / clinical cohort reports defining the *LRRC7*-associated neurodevelopmental syndrome (e.g., Kaplanis et al., *Nature*, 2020; formally assigned as IDDAD77 in OMIM, 2023).

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P01)

### 1. Patient Rule-In / Rule-Out Assessment

The provided sources characterize autosomal dominant intellectual developmental disorder-77 (MRD77; *LRRC7*) primarily by:
* Global developmental delay [1, 2, 6]
* Mild to moderate intellectual disability [2, 6]
* Autism / autistic features [5]
* Dominant inheritance / heterozygous variants [1, 2, 5, 6]

**Important limitation:** The sources do not provide a complete clinical synopsis, phenotypic spectrum frequencies, or explicit exclusionary criteria [1–6]. Therefore, **no patient can be definitively ruled in or ruled out** based solely on the provided excerpts.

* **P01:** **Cannot be ruled in or ruled out.** P01 presents with both *Intellectual disability* and *Autistic behavior*, aligning directly with the core features highlighted for *LRRC7* [1, 2, 5, 6]. However, the sources do not mention whether epileptic spasms, hypsarrhythmia, microcephaly, or delayed myelination occur in MRD77 [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits developmental regression, hand wringing, and gait disturbance, but does not list global developmental delay, intellectual disability, or autism as described in the sources [1, 2, 5, 6].
* **P03:** **Cannot be ruled in or ruled out.** P03 has *Global developmental delay* [1, 2, 6], but the sources do not mention macrocephaly, delayed myelination, atrial septal defect, or recurrent infections [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has *Global developmental delay* [1, 2, 6], but the sources do not state whether respiratory distress, recurrent infections, or prematurity are associated with MRD77 [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has *Mild global developmental delay* [1, 2, 6], but the sources do not document tremors, dysmetria, absence seizures, or skeletal anomalies [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 has *Mild intellectual disability* and *Global developmental delay* [1, 2, 6], but the sources do not mention pain insensitivity, sleep disturbance, or aggressive behavior [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 has *Global developmental delay* [1, 2, 6], but the sources do not report complex congenital heart defects, renal agenesis, cleft palate, or anal atresia [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has speech and motor delay, but lacks explicit global developmental delay, intellectual disability, or autism [1, 2, 5, 6]. The sources do not mention platybasia, cryptorchidism, or joint hypermobility [1–6].
* **P09:** **Cannot be ruled in or ruled out.** P09 has *Severe intellectual disability*, whereas the sources specify MRD77 is characterized by "mild to moderate intellectual disability" [2, 6]. While this makes P09 less consistent, the sources do not explicitly state severe intellectual disability is excluded [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 has *Mild intellectual disability* [2, 6], but lacks autism [5], and the sources do not document whether dysmorphic facial features, crumpled ears, or seizures are features of MRD77 [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most likely patient:** **P01**
* **Estimated probability:** **55%**

**Reasoning:**
Source [5] explicitly links *LRRC7* to "intellectual disability" and "autism" in its title, alongside global developmental delay and intellectual developmental disorder noted across sources [1, 2, 4, 5, 6]. P01 is the only individual among the ten who presents with both **Intellectual disability** and **Autistic behavior**. Because the sources provide only brief summaries and omit details on additional phenotypes (e.g., hypsarrhythmia, dysmorphisms), substantial uncertainty remains, preventing a higher probability estimate.

---

### 3. Information Needed (Not Provided) to Be Confident

To establish a definitive diagnosis, the following unavailable data would be required:
1. **Full clinical characterization of *LRRC7* cohorts:** Complete phenotypic frequencies and descriptions from the 33 reported individuals in source [5] (specifically regarding seizures/hypsarrhythmia, brain MRI findings, and dysmorphic features).
2. **Exclusionary criteria and full OMIM/MalaCards clinical synopses:** The full text of sources [1], [2], and [6], which were truncated after "...mild to moderate intellectual...".
3. **Molecular genetic data:** Patient sequencing results showing whether any candidate harbors a heterozygous pathogenic or likely pathogenic variant in *LRRC7* [3, 4, 5].

--------------------------------------------------------------------------------

### Round 2  (picked: P01)

Based on the provided sources [1–6], here is the evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources offer very limited clinical summaries:
* Autosomal dominant intellectual developmental disorder-77 (MRD77 / *LRRC7*) is characterized by global developmental delay leading to mild to moderate intellectual disability [1, 2, 6].
* Pathogenic variants in *LRRC7* cause a dominant neurodevelopmental disorder leading to intellectual disability and autism [5].
* The sources **do not** provide a full list of clinical features, Human Phenotype Ontology (HPO) terms, phenotypic frequencies, or explicit exclusion criteria for the 33 individuals reported [5]. Consequently, no patient can be definitively ruled in or conclusively ruled out using only these sources.

* **P01**: **Cannot be ruled in or ruled out.** The patient presents with "Intellectual disability" and "Autistic behavior", which aligns with the presentation of intellectual disability and autism described for *LRRC7* [5], as well as an intellectual developmental disorder [1, 2, 6]. However, the sources do not mention whether epileptic spasms, hypsarrhythmia, or delayed myelination occur in this disorder [1–6].
* **P02**: **Cannot be ruled in or ruled out.** The patient lacks an explicit description of global developmental delay or intellectual disability [1, 2, 6], displaying classic Rett-like features (developmental regression, hand wringing), but the sources do not provide negative exclusion criteria [1–6].
* **P03**: **Cannot be ruled in or ruled out.** Presents with global developmental delay [1, 2, 6], but the sources do not mention macrocephaly, cardiac defects, or recurrent infections [1–6].
* **P04**: **Cannot be ruled in or ruled out.** Presents with global developmental delay [1, 2, 6], but the sources do not report respiratory, atopic, or infectious phenotypes [1–6].
* **P05**: **Cannot be ruled in or ruled out.** Shows mild global developmental delay [1, 2, 6], but the sources do not detail the presence or absence of tremors, ataxia, or skeletal abnormalities [1–6].
* **P06**: **Cannot be ruled in or ruled out.** Has mild intellectual disability and global developmental delay [1, 2, 6], but the sources do not mention pain insensitivity or behavioral extremes [1–6].
* **P07**: **Cannot be ruled in or ruled out.** Has global developmental delay [1, 2, 6], but the sources do not document whether complex multi-organ structural anomalies (renal, cardiac, anal) are associated with *LRRC7* [1–6].
* **P08**: **Cannot be ruled in or ruled out.** Has speech and motor delay rather than documented global developmental delay or intellectual disability [1, 2, 6], but sources do not state these exclusions [1–6].
* **P09**: **Cannot be ruled in or ruled out.** While source [2] and [6] state that the disorder leads to "mild to moderate intellectual" disability, P09 has "Severe intellectual disability". Although this makes P09 an unlikely fit, the brief snippets do not confirm whether severe presentation is strictly excluded [1, 2, 6].
* **P10**: **Cannot be ruled in or ruled out.** Features mild intellectual disability [2, 6], but the sources do not provide information on the facial dysmorphisms (crumpled ear, hypertelorism) or specific seizure types seen in *LRRC7* [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **~30%**

**Reasoning:**
Only **P01** explicitly combines **intellectual disability** and **autistic behavior**, directly mirroring the headline phenotype of *LRRC7* described in source [5] ("Variants in LRRC7 lead to intellectual disability, autism...") alongside the general diagnostic definitions [1, 2, 6]. Because the sources do not provide detailed phenotypic breakdowns for the other candidates with mild developmental delays (e.g., P05, P06, P10), confidence remains low, making a calibrated probability around 30% (compared to a baseline prior of 10%).

---

### 3. Missing Information Needed for Confidence

To establish a confident clinical or genetic diagnosis, the following information—absent from the provided sources—is required:
1. **Molecular Genetic Data:** Confirmatory identification of a heterozygous, pathogenic or likely pathogenic missense or loss-of-function variant in the *LRRC7* gene [3, 5].
2. **Complete Phenotypic Spectrum & Frequencies:** A full HPO profile of the 33 individuals described in the literature [5], including whether epileptic encephalopathies (hypsarrhythmia/epileptic spasms seen in P01) or specific craniofacial features occur with *LRRC7* variants.
3. **Established Exclusion Criteria:** Explicit clinical guidance on whether severe intellectual disability [P09], complex syndromic congenital malformations [P07], or specific regression patterns [P02] fall outside the phenotypic boundaries of MRD77 [1, 2, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based on the provided sources, here is the clinical genetic evaluation for Intellectual Developmental Disorder, Autosomal Dominant 77 (MRD77; *LRRC7*):

---

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources indicate only that autosomal dominant intellectual developmental disorder-77 (*LRRC7*) is characterized by global developmental delay leading to mild to moderate intellectual disability [1, 2, 6] and is associated with autism [5]. Because the sources do not provide comprehensive clinical profiles, HPO frequencies, or explicit exclusion criteria, **none of the patients can be definitively ruled in or ruled out with complete certainty using only these texts** [1–6]. Specifically:

* **P01:** **Cannot be ruled in or ruled out.** P01 possesses both "Intellectual disability" and "Autistic behavior," which aligns directly with the core features highlighted in the literature title for *LRRC7* variants ("intellectual disability, autism") [5] and general neurodevelopmental impairment [1, 2, 6]. However, the sources do not mention whether epileptic spasms, hypsarrhythmia, microcephaly, or delayed CNS myelination occur in MRD77 [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits developmental regression and hand wringing. The sources describe MRD77 as global developmental delay leading to mild to moderate intellectual disability [1, 2, 6], but do not mention regression. However, the sources do not explicitly state that regression is exclusionary [1–6].
* **P03:** **Cannot be ruled in or ruled out.** P03 has global developmental delay [1, 2, 6], but the sources do not document whether macrocephaly, delayed myelination, or cardiac defects (atrial septal defect) are part of the *LRRC7* phenotype [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has global developmental delay and motor/speech delay, partially fitting the general description [1, 2, 6], but the sources provide no information regarding recurrent infections, prematurity, or respiratory distress in MRD77 [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has mild global developmental delay, which matches [1, 2, 6]. However, the sources do not state whether ataxia, tremors, absence seizures, or skeletal anomalies occur in MRD77 [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 has mild intellectual disability and mild global developmental delay [1, 2, 6]. Nonetheless, the sources make no mention of pain insensitivity, severe global developmental delay, or specific behavioral outbursts [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 shares global developmental delay [1, 2, 6], but presents with major multi-organ malformations (renal agenesis, anal atresia, complex congenital heart defects, cleft palate) which are neither confirmed nor refuted by the provided sources [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has speech and motor delay, but intellectual disability is not listed, and the sources do not mention psychiatric presentations such as psychosis [1–6].
* **P09:** **Unlikely / cannot be definitively ruled out.** P09 has "Severe intellectual disability," whereas the sources specifically define MRD77 as characterized by delay that leads to "mild to moderate intellectual" disability [1, 2, 6]. While this discrepancy makes P09 an unlikely match, the text snippets cut off and do not explicitly state that severe impairment is impossible [1, 2, 6].
* **P10:** **Cannot be ruled in or ruled out.** P10 has "Mild intellectual disability," consistent with [1, 2, 6]. However, the sources do not document whether seizures, craniofacial dysmorphisms (crumpled ear, hypertelorism), or feeding difficulties occur in *LRRC7* deficiency [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **~35%**

**Reasoning:** 
Source [5] specifically links heterozygous *LRRC7* variants to both "intellectual disability" and "autism" in its title (*"Variants in LRRC7 lead to intellectual disability, autism..."*) [5], alongside the general presentation of intellectual developmental disorder [1, 2, 3, 4, 6]. Among all 10 candidates, **P01** is the only patient explicitly noted to have both "Intellectual disability" and "Autistic behavior." 

The probability remains modest (~35%) because other candidates (such as P10, P06, and P05) match the "mild" intellectual/developmental delay criteria [1, 2, 6], and the sources do not provide the detailed phenotypic breakdown needed to confirm whether P01's severe epileptic encephalopathy phenotype (hypsarrhythmia, spasms) belongs to the *LRRC7* spectrum [1–6].

---

### 3. Missing Information Needed for Diagnostic Confidence

To make a confident clinical determination, the following facts (which the provided sources do **not** contain) are required:
1. **Detailed Phenotypic Spectrum:** The specific clinical findings and HPO frequencies of the 33 individuals described with *LRRC7* variants in Willim et al. (2024) [5].
2. **Epilepsy Characterization:** Whether *LRRC7* causes infantile epileptic spasms, hypsarrhythmia, absence seizures, or other seizure types, or if seizures are atypical [1–6].
3. **Neuroimaging Findings:** Whether delayed CNS myelination, cortical dysplasia, or ventriculomegaly are reported features of *LRRC7* deficiency [1–6].
4. **Dysmorphic Features:** Whether *LRRC7* is associated with recognizable facial features (e.g., deep-set eyes, epicanthus, crumpled ears, wide nasal bridge) or head circumference abnormalities (microcephaly vs. macrocephaly) [1–6].
5. **Severity Limits:** Whether the intellectual disability in MRD77 is strictly restricted to mild-to-moderate, or if severe intellectual disability and developmental regression can occur [1, 2, 6].

--------------------------------------------------------------------------------

picks across rounds: ['P01', 'P01', 'P01']
