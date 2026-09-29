# Plain RAG on Intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (FBXO11, OMIM:618089)
model: gemini-3.8-flash   generated: 2026-09-28 20:45

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `FBXO11 gene Intellectual developmental disorder with dysmorphic facies and behavioral abnormalities`

[1] **The first familial case of inherited intellectual ...**  
    https://pubmed.ncbi.nlm.nih.gov/32902151/  
    by CG Lee · 2020 · Cited by 12 — Here, we present the first report of a family showing autosomal dominantly inherited IDDFBA, harboring a novel heterozygous variant in FBXO11 (c ...

[2] **Intellectual Developmental Disorder with Dysmorphic ...**  
    https://www.malacards.org/card/intellectual_developmental_disorder_with_dysmorphic_facies_and_behavioral_abnormalities  
    Reported clinical features include intellectual disability, speech delay, hyperkinetic disorder, hyperactivity, seizures, pre- and postnatal growth retardation,

[3] **FBXO11**  
    https://www.simonssearchlight.org/research/what-we-study/fbxo11/  
    FBXO11-related syndrome is also called intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (IDDFBA).

[4] **New ocular findings in a patient with a novel pathogenic ...**  
    https://www.sciencedirect.com/science/article/abs/pii/S1091853122001446  
    by RG Silva · 2022 · Cited by 5 — Intellectual developmental disorder with dysmorphic facies and behavioral abnormalities ... De novo FBXO11 mutations are associated with intellectual disability ...

[5] **Submission Details**  
    https://thegencc.org/submissions/GENCC_000111-HGNC_13590-OMIM_618089-HP_0000006-GENCC_100002  
    FBXO11 mutations are associated with intellectual disability and behavioural anomalies. variants in FBXO11 cause a syndromic form of intellectual disability ...

[6] **intellectual developmental disorder with dysmorphic facies ...**  
    https://zfin.org/DOID:0061129  
    An autosomal dominant intellectual developmental disorder that has_material_basis_in heterozygous mutation in FBXO11 gene on chromosome 2p16.

## 2. The context handed to the model
```
[1] The first familial case of inherited intellectual ...
https://pubmed.ncbi.nlm.nih.gov/32902151/
by CG Lee · 2020 · Cited by 12 — Here, we present the first report of a family showing autosomal dominantly inherited IDDFBA, harboring a novel heterozygous variant in FBXO11 (c ...

[2] Intellectual Developmental Disorder with Dysmorphic ...
https://www.malacards.org/card/intellectual_developmental_disorder_with_dysmorphic_facies_and_behavioral_abnormalities
Reported clinical features include intellectual disability, speech delay, hyperkinetic disorder, hyperactivity, seizures, pre- and postnatal growth retardation,

[3] FBXO11
https://www.simonssearchlight.org/research/what-we-study/fbxo11/
FBXO11-related syndrome is also called intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (IDDFBA).

[4] New ocular findings in a patient with a novel pathogenic ...
https://www.sciencedirect.com/science/article/abs/pii/S1091853122001446
by RG Silva · 2022 · Cited by 5 — Intellectual developmental disorder with dysmorphic facies and behavioral abnormalities ... De novo FBXO11 mutations are associated with intellectual disability ...

[5] Submission Details
https://thegencc.org/submissions/GENCC_000111-HGNC_13590-OMIM_618089-HP_0000006-GENCC_100002
FBXO11 mutations are associated with intellectual disability and behavioural anomalies. variants in FBXO11 cause a syndromic form of intellectual disability ...

[6] intellectual developmental disorder with dysmorphic facies ...
https://zfin.org/DOID:0061129
An autosomal dominant intellectual developmental disorder that has_material_basis_in heterozygous mutation in FBXO11 gene on chromosome 2p16.
```

## 3. The gene, from the sources

The *FBXO11* gene is located on chromosome 2p16, and heterozygous variants in this gene form the material basis for intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (IDDFBA), also known as FBXO11-related syndrome [3, 6]. IDDFBA can be inherited in an autosomal dominant manner, and *de novo* mutations in *FBXO11* also cause this syndromic form of intellectual disability [1, 4, 5, 6]. Clinical features associated with these variants include intellectual disability, behavioral anomalies, speech delay, hyperkinetic disorder, hyperactivity, seizures, and pre- and postnatal growth retardation [2, 5]. 

However, the provided sources do not cover what the *FBXO11* gene product is or what role it performs inside the cell [1, 2, 3, 4, 5, 6]. Furthermore, the specific cellular mechanisms detailing how these variants cause disease are not covered in the provided text [1, 2, 3, 4, 5, 6].

*tokens in 568, out 1408*

## 4. The gene, closed book (no sources; beware hallucinations)

The *FBXO11* gene encodes F-box only protein 11, a substrate-recognition component of the modular SCF (SKP1-CUL1-F-box) E3 ubiquitin ligase complex. In this role, FBXO11 facilitates the ubiquitination and subsequent proteasomal degradation of specific target proteins (including BCL6, CDT2, and PRMT5), thereby regulating critical biological processes such as cell-cycle progression, chromatin modification, and neurogenesis.

Heterozygous *de novo* mutations—predominantly loss-of-function variants (nonsense, frameshift, and splice-site) as well as deleterious missense variants—cause disease through haploinsufficiency. This disruption of targeted protein turnover compromises neurodevelopmental pathways, culminating in intellectual disability, distinct facial dysmorphisms, and behavioral difficulties (such as autism spectrum traits and hyperactivity). 

The disorder was first delineated in **2018**. 

**Citation:** 
Gregor, A., et al. (2018). "De Novo Variants in *FBXO11* Cause an Intellectual Disability Syndrome with Facial Dysmorphism and Behavioral Abnormalities." *The American Journal of Human Genetics*, 103(2), 305–316.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P01)

Based solely on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

Under the provided sources, **none of the patients can be definitively ruled in or ruled out** based solely on clinical features [1–6]. The sources establish that this disorder (IDDFBA) is caused by a heterozygous mutation in the *FBXO11* gene [1, 6] and list a very limited set of clinical features: intellectual disability, speech delay, hyperkinetic disorder, hyperactivity, seizures, pre- and postnatal growth retardation, behavioral abnormalities, and unspecified dysmorphic facies [2, 5]. The sources do not provide genetic sequencing results, exhaustive clinical criteria, or exclusion criteria for any patient [1–6].

* **P01:** **Cannot be ruled in or ruled out.** P01 presents with intellectual disability [2, 5], speech delay [2], behavioral abnormalities (anxiety, autistic behavior) [1, 5], and dysmorphic facies [1–4]. However, the sources do not provide specific facial descriptors (e.g., broad forehead, downslanted palpebral fissures) or molecular confirmation of an *FBXO11* variant to rule them in [1, 6], nor do they list cardiac or digit abnormalities as exclusion criteria to rule them out [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 has intellectual disability [2, 5], abnormal facial shape [1–3], and short stature (consistent with growth retardation) [2]. The sources lack molecular data to rule them in [1, 6] and contain no exclusion criteria to rule them out [1–6].
* **P03:** **Cannot be ruled in or ruled out.** P03 has intellectual disability [2, 5], poor speech [2], and autism/behavioral features [1, 5]. However, the sources do not provide genetic data to confirm the diagnosis [1, 6], nor do they specify whether craniosynostosis or ataxia rule IDDFBA out [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has intellectual disability [2, 5], speech delay [2], anxiety [1, 5], and dysmorphic facial features [1–4]. The sources provide neither the *FBXO11* genetic data to confirm the condition [1, 6] nor exclusion criteria to eliminate P04 [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has hyperactivity [2] and short stature [2], but has a "specific learning disability" rather than explicit "intellectual disability" [1, 2, 5]. The sources define IDDFBA as an intellectual developmental disorder [1, 2, 5, 6], but do not specify whether learning disability alone is sufficient or rules the diagnosis out [1–6]. Molecular confirmation is also missing [1, 6].
* **P06:** **Cannot be ruled in or ruled out.** P06 has intellectual disability [2, 5], speech delay [2], behavioral abnormalities (anxiety, autistic behavior) [1, 5], and dysmorphic facial features [1–4]. Conclusive rule-in is impossible without molecular testing [1, 6], and no exclusion criteria exist in the sources to rule P06 out [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 has intellectual disability [2, 5], speech delay [2], seizures [2], short stature [2], and behavioral/psychiatric issues [1, 5]. However, the sources provide no genetic confirmation [1, 6] and no exclusion criteria (e.g., regarding hypertrichosis or overweight) [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has intellectual disability [2, 5] and speech delay [2]. The sources do not mention hepatic or biliary abnormalities [1–6], but because they do not provide an exhaustive phenotype or exclusion criteria, P08 cannot be formally ruled out or ruled in [1–6].
* **P09:** **Cannot be ruled in or ruled out.** P09 has intellectual disability [2, 5], speech delay [2], anxiety [1, 5], and facial dysmorphisms (micrognathia, retrognathia) [1–4]. The sources do not include molecular data to confirm the diagnosis [1, 6], nor exclusion criteria to dismiss it [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 presents with intellectual disability [2, 5], speech delay [2], seizures [2], behavioral features [1, 5], and facial dysmorphisms [1–4]. Without molecular testing [1, 6] or exclusion criteria [1–6], P10 cannot be definitively ruled in or ruled out.

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **~30%**

**Reasoning:** 
IDDFBA is fundamentally defined by the triad of intellectual developmental disorder/intellectual disability, dysmorphic facies, and behavioral abnormalities [1–3, 5, 6], accompanied by speech delay [2]. 
P01 demonstrates every core clinical domain highlighted across the sources: severe intellectual disability [2, 5], delayed speech and language development [2], extensive dysmorphic facial features [1–4], and behavioral abnormalities (anxiety, autistic behavior) [1, 5]. 

The probability is assigned at approximately 30% (rather than higher) because several other patients (such as P06, P07, P04, and P10) also share overlapping general features reported in the text (such as speech delay, seizures, short stature, and behavioral symptoms) [2, 5]. Based *strictly* on the minimal clinical descriptions in sources [1–6], distinguishing conclusively among these candidates is not possible.

---

### 3. Missing Facts Needed for Confidence

To establish a definitive diagnosis, the following information is required but absent from the sources:
1. **Molecular Genetic Testing:** Confirmation of a heterozygous pathogenic variant in the *FBXO11* gene (located on chromosome 2p16) [1, 6].
2. **Specific Craniofacial Manifestations:** Detailed descriptions of what constitutes the "dysmorphic facies" referenced in the condition’s name [1–4, 6] (the sources do not specify particular facial characteristics such as palpebral fissure slant, nasal features, or jaw abnormalities).
3. **Specific Ocular Details:** Source [4] mentions "ocular findings" in its title, but the text provided does not describe what those findings are.
4. **Exclusion Criteria / Negative Phenotypic Boundaries:** Explicit guidance on whether systemic involvement (such as congenital heart disease, liver dysfunction, craniosynostosis, or specific dermatoglyphic findings) is consistent with or exclusionary for *FBXO11*-related disorder [1–6].
5. **Feature Penetrance and Frequencies:** Specific prevalence or penetrance data for reported features such as seizures, growth retardation, and hyperkinetic disorder/hyperactivity [2].

--------------------------------------------------------------------------------

### Round 2  (picked: P01)

### 1. Patient Rule-In / Rule-Out Assessment

Based strictly on the provided sources, the diagnostic entity is **intellectual developmental disorder with dysmorphic facies and behavioral abnormalities (IDDFBA)**, caused by heterozygous variants in *FBXO11* [1, 3, 6]. The specific clinical features explicitly documented in the sources are:
* Intellectual disability / global intellectual developmental disorder [1, 2, 3, 4, 5, 6]
* Dysmorphic facies (unspecified) [1, 2, 3, 4, 6]
* Behavioral abnormalities / anomalies [1, 2, 3, 4, 5]
* Speech delay [2]
* Hyperactivity / hyperkinetic disorder [2]
* Seizures [2]
* Pre- and postnatal growth retardation [2]
* Ocular findings (unspecified) [4]

Crucially, **the sources do not provide exclusionary criteria, full phenotypic frequencies, or detailed facial/systemic descriptions** [1–6]. Consequently, the sources **do not permit definitively ruling in or ruling out any single patient**:

* **P01**: **Cannot be ruled in or ruled out.** The patient has severe intellectual disability [2, 4, 5], delayed speech and language development [2], behavioral abnormalities (anxiety, autistic behavior) [1, 2, 5], ocular involvement (deeply set eye) [4], and dysmorphic facies [2, 3]. However, the sources do not describe specific facial dysmorphisms or structural cardiac/limb criteria to confirm or exclude this patient [1–6].
* **P02**: **Cannot be ruled in or ruled out.** The patient has intellectual disability [2], abnormal facial shape (dysmorphic facies) [2, 3], and short stature (consistent with growth retardation) [2]. However, the sources lack sufficient detail regarding nuchal translucency or prematurity to rule the patient in or out [1–6].
* **P03**: **Cannot be ruled in or ruled out.** The patient has intellectual disability [2], poor speech [2], and behavioral issues (autism) [5]. However, the sources do not state whether cranial (craniosynostosis), auditory/cochlear, or cerebellar features occur or are exclusionary [1–6].
* **P04**: **Cannot be ruled in or ruled out.** The patient possesses intellectual disability [2], speech delay [2], behavioral anomalies (anxiety) [5], and facial dysmorphisms [2, 3]. The sources do not document whether microcephaly, GI dysmotility, or palmar crease variations belong to the spectrum or rule it out [1–6].
* **P05**: **Cannot be ruled in or ruled out.** The patient displays hyperactivity [2], short stature [2], and facial features [2, 3], but has a "specific learning disability" rather than explicit intellectual disability [2], and hypertrichosis is not described in the sources [1–6]. The sources do not establish whether these findings exclude the condition [1–6].
* **P06**: **Cannot be ruled in or ruled out.** The patient exhibits intellectual disability [2], speech delay [2], behavioral abnormalities (anxiety, autistic behavior) [5], and facial dysmorphisms [2, 3]. The sources do not provide characterization of specific facial features (e.g., macroglossia, prognathia) to verify or exclude the diagnosis [1–6].
* **P07**: **Cannot be ruled in or ruled out.** The patient matches several specific features listed in the sources, including intellectual disability [2], speech delay [2], seizures [2], short stature (growth retardation) [2], and behavioral changes (auditory hallucinations) [5]. However, the sources do not mention hypertrichosis or weight gain, nor do they provide exclusionary rules [1–6].
* **P08**: **Cannot be ruled in or ruled out.** The patient has intellectual disability [2], speech delay [2], and dysmorphic features [2, 3], but also has marked hepatic and biochemical abnormalities (elevated bile acids, transaminases, hepatomegaly) which are neither documented nor stated as exclusionary in the sources [1–6].
* **P09**: **Cannot be ruled in or ruled out.** The patient has intellectual disability [2], speech delay [2], and anxiety [5], along with micrognathia [2, 3]. The sources do not indicate whether spasticity or chest wall deformities are part of IDDFBA or exclude it [1–6].
* **P10**: **Cannot be ruled in or ruled out.** The patient has intellectual disability [2], speech delay [2], seizures [2], behavioral abnormalities [5], and facial dysmorphism [2, 3]. However, the sources do not mention whether cardiomyopathy, palpebral elongation, or digital pad abnormalities occur or rule out the disorder [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient**: **P01**
  * *Reasoning based on sources*: P01 exhibits the full core triad defined by the disorder's name—**I**ntellectual developmental disorder (severe intellectual disability, global developmental delay), **D**ysmorphic **F**acies (multiple cranial/facial dysmorphisms), and **B**ehavioral **A**bnormalities (anxiety, autistic behavior) [1, 2, 3, 5], along with speech delay [2] and ocular findings (deeply set eye) [4].
* **Probability**: **~25%**
  * *Justification*: Because exactly one patient among ten has the disorder, the baseline prior probability is 10%. While P01 and P07 align with multiple cardinal features from the sources (P01 for dysmorphic facies, behavioral changes, speech delay, and intellectual disability [1–5]; P07 for seizures, short stature, speech delay, and intellectual disability [2]), the sources provide so little granularity and zero exclusionary rules that confidence remains low.

---

### 3. Missing Information Needed for Confidence

To establish a confident diagnosis, the following information—absent from the provided sources—is required:
1. **Specific dysmorphology phenotype**: A detailed definition of the characteristic facial gestalt (the sources only state "dysmorphic facies" [1–4, 6] without specifying individual nasal, ocular, oral, or cranial features).
2. **Specific ocular phenotype**: Clarification of the exact "ocular findings" referenced in [4].
3. **Exclusionary criteria and full clinical spectrum**: Data on whether systemic features present in these patients (e.g., hepatobiliary disease, craniosynostosis, congenital heart defects, hypertrichosis) exclude or belong to *FBXO11*-related disorder.
4. **Frequency data for behavioral features**: Specific definitions and rates for the "behavioral abnormalities" beyond generalized hyperactivity [2] and anomalies [5] (e.g., prevalence of autism, anxiety, or psychosis).
5. **Molecular genetic confirmation**: Detection of a pathogenic heterozygous variant in the *FBXO11* gene (located at chromosome 2p16) [1, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based solely on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluations (Rule In / Rule Out)

The provided sources define IDDFBA (*FBXO11*-related syndrome) as an autosomal dominant disorder [1, 6] associated with intellectual disability [2, 4, 5, 6], speech delay [2], behavioral abnormalities/anomalies (including hyperkinetic disorder and hyperactivity) [2, 3, 4, 5], seizures [2], pre- and postnatal growth retardation [2], dysmorphic facies [1, 2, 3, 4, 6], and ocular findings [4]. 

Because the sources do not provide definitive exclusionary criteria, complete clinical dysmorphology profiles, or pathognomonic clinical features (beyond requiring a heterozygous variant in *FBXO11* [1, 6]), **no patient can be definitively ruled in or ruled out** based solely on clinical terms:

* **P01:** **Cannot be ruled in or ruled out.** P01 exhibits intellectual disability [2, 4, 5, 6], delayed speech and language development [2], behavioral abnormalities (anxiety, autistic behavior) [2, 3, 5], an ocular finding (deeply set eye) [4], and dysmorphic facial features [1, 2, 3, 4, 6]. However, the sources do not provide specific facial gestalt criteria or cardiac details to definitively rule P01 in, nor exclusion criteria to rule P01 out [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 has intellectual disability [2, 4, 5, 6], short stature (consistent with growth retardation) [2], and abnormal facial shape [1, 2, 3, 4, 6]. However, the sources do not specify whether increased nuchal translucency or premature birth occur in or exclude IDDFBA [1–6].
* **P03:** **Cannot be ruled in or ruled out.** P03 has intellectual disability [2, 4, 5, 6], poor speech [2], and behavioral abnormalities (autism) [2, 3, 5]. However, the sources do not mention sagittal craniosynostosis, ataxia, or cochlear nerve abnormalities, nor do they state if these rule out the condition [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has intellectual disability [2, 4, 5, 6], delayed speech [2], anxiety [2, 5], and facial dysmorphisms [1, 2, 3, 4, 6]. However, the sources do not provide sufficient phenotypic detail (e.g., microcephaly, chronic constipation) to confirm or exclude this diagnosis [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has hyperactivity [2], short stature (growth retardation) [2], and facial dysmorphisms [1, 2, 3, 4, 6]. However, P05 is described with a "specific learning disability" rather than intellectual disability [2, 4, 5, 6], and the sources do not clarify whether learning disability alone is sufficient or exclusionary [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 presents with intellectual disability [2, 4, 5, 6], delayed speech [2], behavioral abnormalities (anxiety, autistic behavior) [2, 3, 5], and dysmorphic facial features [1, 2, 3, 4, 6]. The sources lack the specific facial details (e.g., macroglossia) needed to confirm or rule out the disorder [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 possesses intellectual disability [2, 4, 5, 6], delayed speech [2], seizures [2], short stature [2], and behavioral/psychiatric abnormalities (auditory hallucinations) [2, 5]. However, P07 is also described as "overweight," which may conflict with "postnatal growth retardation" [2], but the sources do not state if growth retardation is mandatory or if being overweight excludes IDDFBA [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has intellectual disability [2, 4, 5, 6], delayed speech [2], and dysmorphic facial features [1, 2, 3, 4, 6]. The sources do not mention hepatic or bile acid abnormalities and do not state whether their presence excludes IDDFBA [1–6].
* **P09:** **Cannot be ruled in or ruled out.** P09 shows intellectual disability [2, 4, 5, 6], delayed speech [2], anxiety [2, 5], and facial dysmorphic features [1, 2, 3, 4, 6]. The sources do not provide sufficient specifics to rule P09 in or out [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 displays intellectual disability [2, 4, 5, 6], delayed speech [2], seizures [2], behavioral abnormalities [2, 5], an ocular feature (long palpebral fissure) [4], and dysmorphic facial features [1, 2, 3, 4, 6]. However, the sources do not mention cardiomyopathy or hand anomalies, nor do they state if they exclude IDDFBA [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **~25–30%**

**Reasoning:**
Given that exactly one patient among the 10 has the condition, the baseline prior probability is 10%. P01 demonstrates an extensive phenotypic overlap with the cardinal descriptors provided across the sources: intellectual disability [2, 4, 5, 6], delayed speech and language development [2], behavioral abnormalities (autistic behavior, anxiety) [2, 3, 5], ocular findings (deeply set eye) [4], and prominent dysmorphic facial features [1, 2, 3, 4, 6]. Furthermore, unlike P07 (who presents with "overweight," potentially conflicting with reported "growth retardation" [2]) or P05 (who has a "specific learning disability" rather than "intellectual disability" [2, 4, 5, 6]), P01 has no features directly at odds with the text. Nevertheless, because several other patients (such as P04, P06, and P10) also share broad overlap with these non-specific descriptors [1–6], the probability cannot be considered definitively high based on the provided texts alone.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a definitive diagnosis, the following information is required that the sources do not provide:
1. **Molecular Genetic Data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in the *FBXO11* gene (located on chromosome 2p16) [1, 6].
2. **Specific Dysmorphic Facial Gestalt:** Detailed delineations of which specific cranial and facial dysmorphisms define IDDFBA (the sources only provide the broad term "dysmorphic facies" [1, 2, 3, 4, 6]).
3. **Specific Ocular Phenotypes:** Explicit identification of the specific ocular abnormalities associated with *FBXO11* mutations (source [4] mentions "ocular findings" only in the publication title without listing them).
4. **Exclusionary Criteria and Co-occurring Features:** Clear clinical criteria indicating whether systemic findings (e.g., cardiac defects, craniosynostosis, hepatic dysfunction, micrognathia, or obesity) occur within the IDDFBA spectrum or rule it out [1–6].
5. **Feature Penetrance:** Data detailing the penetrance and frequency of individual reported features (such as seizures, growth retardation, or specific behavioral manifestations) in *FBXO11* patients [2, 5].

--------------------------------------------------------------------------------

picks across rounds: ['P01', 'P01', 'P01']
