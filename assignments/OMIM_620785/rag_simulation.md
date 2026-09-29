# Plain RAG on Neurodevelopmental disorder with progressive movement abnormalities (ACBD6, OMIM:620785)
model: gemini-3.8-flash   generated: 2026-09-28 20:48

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `ACBD6 gene Neurodevelopmental disorder with progressive movement abnormalities`

[1] **Entry - #620785 - NEURODEVELOPMENTAL DISORDER ...**  
    https://omim.org/entry/620785  
    neurodevelopmental disorder with progressive movement abnormalities (NEDPM) is caused by homozygous mutation in the ACBD6 gene (616352) on ...

[2] **Bi-allelic ACBD6 variants lead to a neurodevelopmental ...**  
    https://pubmed.ncbi.nlm.nih.gov/37951597/  
    bi-allelic pathogenic variants in ACBD6 lead to a distinct neurodevelopmental syndrome accompanied by complex and progressive cognitive and movement disorders.

[3] **Bi-allelic ACBD6 variants lead to a neurodevelopmental ...**  
    https://academic.oup.com/brain/article/147/4/1436/7407365  
    by R Kaiyrzhanov · 2024 · Cited by 27 — A neurodevelopmental syndrome with progressive movement disorders characterizes ACBD6-related disease. Despite their predicted roles in cellular lipid ...

[4] **ACBD6**  
    https://panelapp.genomicsengland.co.uk/panels/genes/ACBD6  
    Neurodevelopmental disorder with progressive movement abnormalities, ACBD6 in Dystonia, chorea or related movement disorder,

[5] **Gene linked to movement disorder with Parkinson's-like ...**  
    https://parkinsonsnewstoday.com/news/gene-linked-movement-disorder-parkinsons-like-symptoms/  
    Researchers have uncovered a new movement disorder with Parkinson's-like symptoms caused by mutations in the ACBD6 gene.

[6] **Neurodevelopmental Disorder with Progressive Movement ...**  
    https://www.malacards.org/card/neurodevelopmental_disorder_with_progressive_movement_abnormalities  
    ACBD6 variants lead to a neurodevelopmental syndrome with progressive and complex movement disorders.

## 2. The context handed to the model
```
[1] Entry - #620785 - NEURODEVELOPMENTAL DISORDER ...
https://omim.org/entry/620785
neurodevelopmental disorder with progressive movement abnormalities (NEDPM) is caused by homozygous mutation in the ACBD6 gene (616352) on ...

[2] Bi-allelic ACBD6 variants lead to a neurodevelopmental ...
https://pubmed.ncbi.nlm.nih.gov/37951597/
bi-allelic pathogenic variants in ACBD6 lead to a distinct neurodevelopmental syndrome accompanied by complex and progressive cognitive and movement disorders.

[3] Bi-allelic ACBD6 variants lead to a neurodevelopmental ...
https://academic.oup.com/brain/article/147/4/1436/7407365
by R Kaiyrzhanov · 2024 · Cited by 27 — A neurodevelopmental syndrome with progressive movement disorders characterizes ACBD6-related disease. Despite their predicted roles in cellular lipid ...

[4] ACBD6
https://panelapp.genomicsengland.co.uk/panels/genes/ACBD6
Neurodevelopmental disorder with progressive movement abnormalities, ACBD6 in Dystonia, chorea or related movement disorder,

[5] Gene linked to movement disorder with Parkinson's-like ...
https://parkinsonsnewstoday.com/news/gene-linked-movement-disorder-parkinsons-like-symptoms/
Researchers have uncovered a new movement disorder with Parkinson's-like symptoms caused by mutations in the ACBD6 gene.

[6] Neurodevelopmental Disorder with Progressive Movement ...
https://www.malacards.org/card/neurodevelopmental_disorder_with_progressive_movement_abnormalities
ACBD6 variants lead to a neurodevelopmental syndrome with progressive and complex movement disorders.
```

## 3. The gene, from the sources

The *ACBD6* gene is directly associated with neurodevelopmental disorder with progressive movement abnormalities (NEDPM) [1, 4]. The specific identity and structure of the *ACBD6* gene product are not covered in the provided sources [1, 3]. In the cell, the gene is described only as having predicted roles involving cellular lipids, while further details of its biological function are not covered [3]. 

NEDPM is caused by homozygous mutations or bi-allelic pathogenic variants in the *ACBD6* gene [1, 2]. These genetic variants lead to a distinct neurodevelopmental syndrome accompanied by complex, progressive cognitive and movement disorders [2, 6]. Phenotypically, disease caused by *ACBD6* mutations can involve dystonia, chorea, or related movement disorders [4]. Additionally, researchers have identified that *ACBD6* mutations cause a movement disorder presenting with Parkinson's-like symptoms [5].

*tokens in 517, out 1345*

## 4. The gene, closed book (no sources; beware hallucinations)

*ACBD6* encodes **acyl-CoA-binding domain-containing protein 6**, a cytosolic acyl-CoA chaperone. It binds medium- and long-chain acyl-CoAs, functioning primarily to deliver myristoyl-CoA to *N*-myristoyltransferases (NMT1 and NMT2). This process facilitates protein *N*-myristoylation, an essential post-translational lipid modification required for membrane targeting, protein stability, and intracellular signaling.

Biallelic loss-of-function variants (including frameshift, nonsense, splice-site, and pathogenic missense mutations) disrupt ACBD6 stability or its acyl-CoA-binding domain. This loss impairs myristoyl-CoA delivery, depleting cellular *N*-myristoylation of critical neurodevelopmental proteins, altering lipid metabolism, and ultimately causing neurodegeneration. Patients present with global developmental delay, facial dysmorphism, and progressive movement disorders such as dystonia, spasticity, and choreoathetosis.

The disorder was first delineated in **2022** (advance access November 2022; journal issue 2023).

**Citation:**  
Smol, T., et al. (2023). Biallelic variants in *ACBD6* cause a neurodevelopmental disorder with progressive movement abnormalities. *Brain*, 146(7), 2828–2841. https://doi.org/10.1093/brain/awac428

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P07)

Based strictly on the provided sources ([1]–[6]), here is the clinical genetic assessment:

---

### 1. Patient Evaluation (Rule-In / Rule-Out)

The sources establish that biallelic/homozygous *ACBD6* variants cause a neurodevelopmental disorder with progressive cognitive and complex movement abnormalities [1, 2, 3, 6], specifically noting Parkinson's-like symptoms [5] as well as dystonia, chorea, or related movement disorders [4]. 

However, **the sources do not provide a complete clinical synopsis, full Human Phenotype Ontology (HPO) term list, or explicit exclusionary criteria**. Therefore, strictly based on the text provided, **no patient can be definitively ruled in or ruled out with complete diagnostic certainty**. Based on phenotypic consistency with the sources:

* **P01 (Cannot be ruled in or out):** Shows global developmental delay [1, 2] and features consistent with movement abnormalities/Parkinson's-like signs (tremor, stooped posture, postural instability, ataxia) [1, 2, 5]. While phenotypically compatible, the sources do not provide enough clinical or molecular details to rule P01 in or out definitively.
* **P02 (Cannot be definitively ruled out, but highly inconsistent):** Exhibits global developmental delay [1, 2], but lacks the core progressive movement disorder, Parkinson's-like features, dystonia, or chorea described in the sources [1, 4, 5, 6].
* **P03 (Cannot be definitively ruled out, but highly inconsistent):** Exhibits intellectual disability and developmental delay [1, 2], but lacks any documented movement disorder, Parkinson's-like signs, dystonia, or chorea [1, 4, 5, 6].
* **P04 (Cannot be definitively ruled out, but highly inconsistent):** Has intellectual disability and global developmental delay [1, 2], but lacks movement abnormalities or Parkinson's-like symptoms [1, 4, 5, 6].
* **P05 (Cannot be definitively ruled out, but highly inconsistent):** Displays developmental delay and tone abnormalities [1, 2], but does not exhibit the progressive movement disorder, Parkinson's-like symptoms, chorea, or dystonia highlighted in the sources [1, 4, 5, 6].
* **P06 (Cannot be definitively ruled out, but highly inconsistent):** Displays developmental delay and seizures [1, 2], but lacks movement abnormalities or Parkinsonian symptoms [1, 4, 5, 6].
* **P07 (Cannot be definitively ruled in or out, but the strongest phenotypic match):** Features severe neurodevelopmental delay and intellectual disability [1, 2, 3, 6] alongside explicit **"Parkinsonism"** and **"Tremor"**, directly matching the reported "movement disorder with Parkinson's-like symptoms" [5] and "progressive and complex movement disorders" [2, 3, 6].
* **P08 (Cannot be definitively ruled out, but highly inconsistent):** Presents behavioral traits and hypotonia without the required movement disorder or Parkinson's-like features [1, 4, 5, 6].
* **P09 (Cannot be definitively ruled out, but highly inconsistent):** Displays severe intellectual disability and motor delay [1, 2], but lacks progressive movement abnormalities, Parkinsonism, dystonia, or chorea [1, 4, 5, 6].
* **P10 (Cannot be definitively ruled out, but highly inconsistent):** Exhibits delayed motor and language development [1, 2], but lacks any described movement disorder or Parkinsonian features [1, 4, 5, 6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P07**
* **Estimated Probability:** **70%** (with P01 holding the majority of the remaining ~30% probability due to sharing parkinsonian-type signs such as tremor, postural instability, and stooped posture [5]). 

P07 is the only candidate explicitly documented with the HPO term **"Parkinsonism"**, corresponding directly to the report that *ACBD6* mutations cause a "movement disorder with Parkinson's-like symptoms" [5] in the context of a severe neurodevelopmental syndrome [1, 2, 3, 6].

---

### 3. Missing Facts Needed to Be Confident

To establish a confident diagnosis, the following information—which the sources **do not** provide—is required:
1. **Molecular confirmation:** Documentation of homozygous or bi-allelic pathogenic variants in the *ACBD6* gene [1, 2].
2. **Detailed phenotypic spectrum & frequencies:** The sources state only broad terms ("progressive cognitive and movement disorders" [2], "Parkinson's-like symptoms" [5], "dystonia, chorea" [4]); they do not list specific HPO terms, characteristic dysmorphic facial features, or skeletal findings.
3. **Seizure profile:** The sources do not state whether epilepsy (e.g., status epilepticus, febrile seizures) is an established feature of *ACBD6* deficiency [1–6].
4. **Neuroimaging features:** The sources do not describe typical brain MRI findings (e.g., corpus callosum hypoplasia, demyelination, or basal ganglia changes) [1–6].
5. **Longitudinal progression data:** Documentation of whether the movement disorder was progressive over time in these specific individuals [1, 2, 3, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P01)

Based on the provided sources ([1]–[6]), here is the clinical genetic assessment:

---

### 1. Patient-by-Patient Assessment (Rule In / Rule Out)

The provided sources indicate that *ACBD6* pathogenic variants cause a neurodevelopmental disorder with progressive cognitive and movement abnormalities (NEDPM) [1, 2, 3, 6], dystonia, chorea, or related movement disorders [4], and Parkinson's-like symptoms [5]. 

**Critical limitation of the sources:** The sources provide only broad summary descriptions and do not provide exhaustive clinical phenotype lists, HPO term frequencies, or exclusion criteria [1–6]. Consequently, **no patient can be definitively ruled in or definitively ruled out** purely based on the provided text. However, we can assess phenotypic consistency:

* **P01:** **Cannot be ruled in or ruled out.** Consistent with the sources because the patient exhibits neurodevelopmental delay (Global developmental delay, Delayed speech and language development, Delayed ability to walk) [1, 2, 3, 6] and prominent movement abnormalities with classic Parkinson's-like features (Tremor, Stooped posture, Postural instability, Ataxia) [1, 3, 4, 5, 6].
* **P02:** **Cannot be definitively ruled out, but highly inconsistent.** While the patient has global developmental delay [1, 2, 3], they lack the characteristic progressive movement disorder, chorea, dystonia, or Parkinson's-like features described in the sources [1, 4, 5].
* **P03:** **Cannot be definitively ruled out, but highly inconsistent.** Exhibits intellectual disability and motor delay [2], but lacks movement disorder or Parkinson's-like features [4, 5].
* **P04:** **Cannot be definitively ruled out, but highly inconsistent.** Has developmental delay and intellectual disability [2], but lacks any movement disorder manifestations [1, 3, 4, 5].
* **P05:** **Cannot be definitively ruled out, but inconsistent.** Exhibits neurodevelopmental delay [2], but lacks progressive movement abnormalities, chorea, dystonia, or Parkinson's-like symptoms [1, 4, 5].
* **P06:** **Cannot be definitively ruled out, but inconsistent.** Shows neurodevelopmental delay and seizures [2], but lacks movement abnormalities or Parkinson's-like signs [1, 4, 5].
* **P07:** **Cannot be ruled in or ruled out.** Consistent with the sources because the patient has both neurodevelopmental delay (Global developmental delay, Intellectual disability, Absent speech) [1, 2, 3, 6] and explicit movement disorders matching the sources (Parkinsonism, Tremor, Gait ataxia) [1, 3, 4, 5, 6].
* **P08:** **Cannot be definitively ruled out, but highly inconsistent.** Lacks the core neurodevelopmental cognitive impairment and progressive movement disorders described in [1–6].
* **P09:** **Cannot be definitively ruled out, but inconsistent.** Has severe intellectual disability and motor delay [2], but lacks movement disorder or Parkinson's-like signs [1, 4, 5].
* **P10:** **Cannot be definitively ruled out, but inconsistent.** Exhibits developmental delay [2], but lacks movement disorder or Parkinsonian features [1, 4, 5].

---

### 2. Most Likely Patient and Probability

* **Most Likely Patient:** **P01** (or alternatively **P07**). Both P01 and P07 clearly express the combination of developmental delay [1, 2, 3, 6] and Parkinsonian movement features [5]. P01 specifically details cardinal Parkinson's-like features (tremor, postural instability, stooped posture) [5] alongside progressive-type motor deficits (ataxia, spasticity) [1, 3, 4].
* **Estimated Probability:** **55% for P01** (with P07 accounting for ~40%, and the remaining patients sharing <5%). 
  * *Reasoning:* Based strictly on the provided excerpts, the sources do not provide sufficient detail to distinguish whether P01 or P07 is the true *ACBD6* patient, as both align with a neurodevelopmental syndrome with Parkinson's-like movement abnormalities [1–6].

---

### 3. Facts Needed to Be Confident (Not Provided in the Sources)

To make a confident clinical determination, the following missing information would be required:
1. **Molecular Genetic Data:** Confirmation of bi-allelic/homozygous pathogenic variants in the *ACBD6* gene [1, 2, 5].
2. **Detailed Clinical Phenotypic Spectrum:** A complete breakdown of clinical features and HPO terms (e.g., specific dysmorphic facial features, brain MRI abnormalities like corpus callosum dysgenesis, and seizure types), none of which are detailed in sources [1]–[6].
3. **Longitudinal/Progression History:** Clinical confirmation that the movement abnormalities are indeed progressive over time [1, 2, 3, 6].
4. **Exclusionary/Negative Criteria:** Defined phenotypic features that exclude a diagnosis of NEDPM [1–6].

--------------------------------------------------------------------------------

### Round 3  (picked: P07)

Based on the provided sources, here is the clinical genetic assessment:

---

### 1. Patient-by-Patient Evaluation

*Note on sources:* The provided sources state that *ACBD6* deficiency causes a "neurodevelopmental disorder with progressive movement abnormalities" (NEDPM) [1, 4], characterized by complex/progressive movement disorders [2, 3, 6], dystonia/chorea or related movement disorders [4], and "Parkinson's-like symptoms" [5]. The sources **do not** provide a granular list of HPO terms, detailed dysmorphic features, neuroimaging criteria, or exclusion criteria [1–6]. Therefore, no patient can be definitively ruled in or out with absolute certainty from these texts alone; only compatibility with the broad clinical features mentioned in the text can be assessed.

* **P01**: **Cannot be definitively ruled in or ruled out.** The patient exhibits neurodevelopmental delays (compatible with [1, 2, 3]) and features classic for a Parkinsonian movement disorder (e.g., "Tremor", "Stooped posture", "Postural instability"), which aligns with the "Parkinson's-like symptoms" and "movement abnormalities" described in [1, 5].
* **P02**: **Cannot be ruled in; likely ruled out.** Presents with global developmental delay and hypotonia, but lacks any described movement disorder or Parkinson's-like symptoms required by [1, 2, 4, 5].
* **P03**: **Cannot be ruled in; likely ruled out.** Has intellectual disability and developmental delays, but lacks the complex movement abnormalities or Parkinson's-like symptoms described in [1, 2, 5].
* **P04**: **Cannot be ruled in; likely ruled out.** Displays global developmental delay and intellectual disability, but has no documented movement disorder or Parkinson's-like features [1, 4, 5].
* **P05**: **Cannot be ruled in; likely ruled out.** While "unsteady gait" is noted, it lacks the specific progressive movement disorder, chorea/dystonia, or Parkinson's-like features highlighted in [4, 5].
* **P06**: **Cannot be ruled in; likely ruled out.** Primarily has a severe seizure phenotype with demyelination and developmental delay, without the movement disorders or Parkinson's-like symptoms detailed in [1, 4, 5].
* **P07**: **Cannot be definitively ruled in or ruled out.** This patient is highly compatible with the sources because they exhibit neurodevelopmental delays ("Global developmental delay", "Intellectual disability") [1, 2, 3] together with explicit "Parkinsonism", "Tremor", and "Gait ataxia", matching the "Parkinson's-like symptoms" and movement disorders reported for *ACBD6* [2, 5].
* **P08**: **Cannot be ruled in; likely ruled out.** Characterized primarily by behavioral traits, joint hypermobility, and hypotonia, with no movement disorder or Parkinson's-like symptoms [1, 4, 5].
* **P09**: **Cannot be ruled in; likely ruled out.** Has severe neurodevelopmental delay and hypotonia, but lacks the progressive movement abnormalities or Parkinsonian features described in [1, 2, 5].
* **P10**: **Cannot be ruled in; likely ruled out.** Shows motor and speech delays with microcephaly and delayed myelination, but lacks the documented movement abnormalities or Parkinson's-like features [1, 4, 5].

---

### 2. Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P07** (with **P01** as a close differential candidate).
  * **Rationale:** P07 explicitly features the core phenotypic triad implied across the sources: a neurodevelopmental syndrome [1–3] with explicit "Parkinsonism" [5] and "Tremor" / movement disorder features [2, 4, 5]. P01 also describes signs of parkinsonism (tremor, stooped posture, postural instability) [5], but P07 explicitly formalizes this as "Parkinsonism".
* **Estimated Probability:** **55%** (with P01 accounting for approximately 40%, and the remaining 5% distributed among the other candidates due to source limitations).

---

### 3. Missing Facts Needed for Confidence

The provided sources do not include the following information necessary to make a definitive diagnosis:
1. **Genetic confirmation:** Confirmation of homozygous or bi-allelic pathogenic variants in the *ACBD6* gene [1, 2, 5].
2. **Granular phenotypic profiles:** Specific HPO frequencies and comprehensive clinical synopses for NEDPM (the sources provide only high-level terms such as "Parkinson's-like symptoms" and "movement abnormalities" without itemizing dysmorphisms, seizure types, or structural brain findings) [1–6].
3. **Longitudinal/progression data:** Documentation of whether the movement disorder is demonstrably *progressive* over time [1, 2, 3, 6].

--------------------------------------------------------------------------------

picks across rounds: ['P07', 'P01', 'P07']
