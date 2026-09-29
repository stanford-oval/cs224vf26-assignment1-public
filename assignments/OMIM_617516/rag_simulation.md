# Plain RAG on Stankiewicz-Isidor syndrome (PSMD12, OMIM:617516)
model: gemini-3.8-flash   generated: 2026-09-28 20:45

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `PSMD12 gene Stankiewicz-Isidor syndrome`

[1] **Stankiewicz-Isidor syndrome: expanding the clinical and ...**  
    https://www.gimjournal.org/article/S1098-3600(21)04132-0/fulltext  
    by B Isidor · 2022 · Cited by 26 — Haploinsufficiency of PSMD12 has been reported in individuals with neurodevelopmental phenotypes, including developmental delay/intellectual disability ...

[2] **Stankiewicz-Isidor Syndrome (STISS)**  
    https://www.malacards.org/card/stankiewicz_isidor_syndrome  
    Stankiewicz-Isidor syndrome is a neurodevelopmental disorder characterized by delayed psychomotor development, intellectual disability, and behavioral ...

[3] **Stankiewicz-Isidor syndrome: expanding the clinical and ...**  
    https://pubmed.ncbi.nlm.nih.gov/34906456/  
    by B Isidor · 2022 · Cited by 26 — Purpose: Haploinsufficiency of PSMD12 has been reported in individuals with neurodevelopmental phenotypes, including developmental delay/intellectual disability ...

[4] **PSMD12**  
    https://www.simonssearchlight.org/research/what-we-study/psmd12/  
    PSMD12-related syndrome happens when there are changes in the PSMD12 gene. These changes can keep the gene from working as it should.

[5] **617516 - STANKIEWICZ-ISIDOR SYNDROME; STISS**  
    https://omim.org/entry/617516  
    ... Isidor syndrome (STISS) is caused by heterozygous mutation in the PSMD12 gene (604450) on chromosome 17q24. ▽ Description. Stankiewicz-Isidor syndrome ...

[6] **Autosomal dominant by ClinGen submission information facts**  
    https://thegencc.org/submissions/SGC-104698.2  
    In summary, there is definitive evidence supporting the relationship between PSMD12 and autosomal dominant Stankiewicz-Isidor Syndrome. This has been ...

## 2. The context handed to the model
```
[1] Stankiewicz-Isidor syndrome: expanding the clinical and ...
https://www.gimjournal.org/article/S1098-3600(21)04132-0/fulltext
by B Isidor · 2022 · Cited by 26 — Haploinsufficiency of PSMD12 has been reported in individuals with neurodevelopmental phenotypes, including developmental delay/intellectual disability ...

[2] Stankiewicz-Isidor Syndrome (STISS)
https://www.malacards.org/card/stankiewicz_isidor_syndrome
Stankiewicz-Isidor syndrome is a neurodevelopmental disorder characterized by delayed psychomotor development, intellectual disability, and behavioral ...

[3] Stankiewicz-Isidor syndrome: expanding the clinical and ...
https://pubmed.ncbi.nlm.nih.gov/34906456/
by B Isidor · 2022 · Cited by 26 — Purpose: Haploinsufficiency of PSMD12 has been reported in individuals with neurodevelopmental phenotypes, including developmental delay/intellectual disability ...

[4] PSMD12
https://www.simonssearchlight.org/research/what-we-study/psmd12/
PSMD12-related syndrome happens when there are changes in the PSMD12 gene. These changes can keep the gene from working as it should.

[5] 617516 - STANKIEWICZ-ISIDOR SYNDROME; STISS
https://omim.org/entry/617516
... Isidor syndrome (STISS) is caused by heterozygous mutation in the PSMD12 gene (604450) on chromosome 17q24. ▽ Description. Stankiewicz-Isidor syndrome ...

[6] Autosomal dominant by ClinGen submission information facts
https://thegencc.org/submissions/SGC-104698.2
In summary, there is definitive evidence supporting the relationship between PSMD12 and autosomal dominant Stankiewicz-Isidor Syndrome. This has been ...
```

## 3. The gene, from the sources

The *PSMD12* gene is located on chromosome 17q24, and definitive evidence establishes its causative link to autosomal dominant Stankiewicz-Isidor syndrome [5, 6]. Stankiewicz-Isidor syndrome is a neurodevelopmental disorder clinically characterized by delayed psychomotor development, intellectual disability, and behavioral alterations [1, 2]. 

Pathogenic variants in the gene include heterozygous mutations and alterations that prevent the gene from working as it should [4, 5]. Through these variants, haploinsufficiency of *PSMD12* leads directly to the neurodevelopmental phenotypes observed in affected individuals [1, 3]. 

However, the provided sources do not cover what the specific *PSMD12* gene product is or what functional role it performs within the cell [1, 2, 3, 4, 5, 6].

*tokens in 569, out 1586*

## 4. The gene, closed book (no sources; beware hallucinations)

The *PSMD12* gene encodes the non-ATPase regulatory subunit 12 (Rpn5), a critical structural component of the 19S regulatory lid within the 26S proteasome. This gene product plays an essential role in proteasome complex assembly and the recognition and processing of ubiquitinated proteins targeted for degradation via the ubiquitin–proteasome system (UPS).

Pathogenic heterozygous variants in *PSMD12*—primarily loss-of-function mutations including frameshift, nonsense, splice-site alterations, or microdeletions—cause disease through haploinsufficiency. Insufficient levels of functional PSMD12 impair 26S proteasome assembly and decrease proteolytic capacity. This disruption causes proteotoxic stress and interferes with normal embryonic signaling pathways, particularly affecting neurodevelopment. 

Clinically, this manifests as Stankiewicz-Isidor syndrome (STISS), characterized by intellectual disability, developmental delay, facial dysmorphisms, and various congenital anomalies.

The syndrome was first delineated in **2017**.

**Citation:** 
Küry, S., et al. (2017). "Loss-of-Function Variants in *PSMD12* Cause a Syndromic Neurodevelopmental Disorder with Congenital Defects." *The American Journal of Human Genetics*, 100(2), 352–363.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P05)

Based strictly on the provided sources [1–6], here is the clinical genetic assessment:

---

### 1. Patient Rule-In / Rule-Out Assessment

The provided sources define Stankiewicz-Isidor syndrome (STISS) as an autosomal dominant neurodevelopmental disorder caused by heterozygous mutations or haploinsufficiency of *PSMD12* [1, 3, 5, 6]. Clinically, the sources describe only a broad phenotype: **developmental delay / intellectual disability** [1, 3] and **delayed psychomotor development, intellectual disability, and behavioral [abnormalities]** [2]. 

The sources do not provide comprehensive dysmorphology, organ system manifestations, neuroimaging features, or negative/exclusion criteria [1–6]. Consequently, **no patient can be definitively ruled in or ruled out**:

* **P01**: **Cannot rule in or rule out.** Presents with motor and speech delay, partially aligning with developmental delay / psychomotor delay [1, 2, 3], but lacks documented intellectual disability or behavioral features, and the sources do not provide details on craniofacial or skeletal findings [1–6].
* **P02**: **Cannot rule in or rule out.** Exhibits global developmental delay and intellectual disability, which match the core neurodevelopmental features in [1, 2, 3], but the sources give no information about facial, oral, or orthopedic signs to confirm or exclude STISS [1–6].
* **P03**: **Cannot rule in or rule out.** Has severe global developmental delay and motor/speech delay [1, 2, 3], but the sources do not state whether extensive multisystem malformations (e.g., Pierre-Robin sequence, cardiac defects, posterior fossa malformations) occur in STISS [1–6].
* **P04**: **Cannot rule in or rule out.** Exhibits severe global developmental delay [1, 2, 3], but the sources provide no data on associated cardiac, limb, or urogenital phenotypes [1–6].
* **P05**: **Cannot rule in or rule out.** Matches all neurodevelopmental characteristics named in the sources: global developmental delay [1, 2, 3], intellectual disability [1, 2, 3], and behavioral abnormalities ("Autistic behavior") [2]. However, the sources provide no data on genital, facial, or neuroimaging features to confirm this diagnosis or exclude others [1–6].
* **P06**: **Cannot rule in or rule out.** Features global developmental delay and mild intellectual disability [1, 2, 3], but the sources lack any description of brain MRI findings, craniofacial features, or airway anomalies [1–6].
* **P07**: **Cannot rule in or rule out.** Does not report developmental delay or intellectual disability [1, 2, 3]; however, the sources do not establish penetrance or state that the absence of these features strictly excludes the syndrome [1–6].
* **P08**: **Cannot rule in or rule out.** Has autistic behavior, matching the mention of behavioral features [2], but lacks developmental delay or intellectual disability; the sources do not state whether behavioral features alone can represent STISS [1–6].
* **P09**: **Cannot rule in or rule out.** Displays global developmental delay and intellectual disability [1, 2, 3], but the sources do not discuss cleft palate, growth, digital, or immunological parameters [1–6].
* **P10**: **Cannot rule in or rule out.** Features severe muscular hypotonia but lacks developmental delay or intellectual disability; the sources do not provide exclusion criteria or non-developmental clinical profiles [1–6].

---

### 2. Most Likely Patient and Probability

* **Most Likely Patient:** **P05**
* **Estimated Probability:** **~30%**

**Rationale:**
P05 is the single patient whose profile captures every positive clinical feature explicitly specified in the excerpts:
1. "Delayed psychomotor development" / "developmental delay" [1, 2, 3] (present as *Global developmental delay*).
2. "Intellectual disability" [1, 2, 3] (present as *Intellectual disability*).
3. "Behavioral [phenotypes]" [2] (present as *Autistic behavior*).

Because multiple other patients (e.g., P02, P06, P09) share the cardinal developmental delay and intellectual disability features [1, 3], and because source [2] is truncated at "behavioral ...", certainty remains low (~30%), with remaining probability distributed primarily across the other patients sharing the core DD/ID phenotype.

---

### 3. Missing Information Needed for Confidence

To make a definitive clinical diagnosis, the following information is missing from the provided sources:
1. **Molecular and Cytogenetic Data:** Demonstration of a pathogenic heterozygous variant or deletion/haploinsufficiency in *PSMD12* on chromosome 17q24 [1, 3, 5, 6].
2. **Complete Text of Clinical Descriptions:** The full text of the truncated description in [2] (which cuts off at `"behavioral ..."`) and the full text of the clinical expansion in Isidor et al. [1, 3].
3. **Phenotypic Spectrum and Frequencies:** Specific HPO terms and recurrence rates for dysmorphic features (craniofacial, ocular, ears), structural anomalies (cardiac, renal, limb, genital), and brain imaging findings seen in *PSMD12* deficiency [1–6].
4. **Penetrance and Exclusion Criteria:** Explicit documentation of obligatory features vs. non-penetrant presentations, and malformations known to exclude or indicate alternative genetic etiologies [1–6].

--------------------------------------------------------------------------------

### Round 2  (picked: P05)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Ruling In/Out)

The sources establish that Stankiewicz-Isidor syndrome (STISS) is a neurodevelopmental disorder caused by heterozygous mutations / haploinsufficiency in *PSMD12* [1, 3, 5, 6] and is characterized broadly by developmental delay/intellectual disability [1, 2, 3], delayed psychomotor development [2], and behavioral features [2]. 

The sources **do not** provide full clinical descriptions, dysmorphic craniofacial features, organ malformations, or complete HPO profiles. Consequently:

* **P01:** **Cannot be ruled in or out.** P01 has motor and speech delays, which align with developmental/psychomotor delay [1, 2, 3], but the sources do not provide sufficient phenotypic detail (e.g., regarding obesity, scoliosis, or forehead morphology) to confirm or exclude STISS.
* **P02:** **Cannot be ruled in or out.** P02 exhibits intellectual disability, global developmental delay, and delayed walking [1, 2, 3], but the sources do not mention facial gestalt (e.g., microcephaly, prognathia) or orthopedic findings, preventing confirmation or exclusion.
* **P03:** **Cannot be ruled in or out.** P03 exhibits severe global developmental delay and delayed psychomotor milestones [1, 2, 3], but the extensive multisystem findings (cardiac, CNS hypoplasia, Pierre-Robin sequence) are neither confirmed nor excluded by the sources.
* **P04:** **Cannot be ruled in or out.** P04 has severe global developmental delay [1, 3], but cardiac, renal, and digital abnormalities are not mentioned in the sources.
* **P05:** **Cannot be ruled in or out.** P05 has global developmental delay, intellectual disability, and autistic/behavioral features, which match the core neurodevelopmental and behavioral traits in [1, 2, 3]; however, the sources do not provide information on genital, craniofacial, or neurological findings to rule P05 definitively in or out.
* **P06:** **Cannot be ruled in or out.** P06 presents with mild intellectual disability, global developmental delay, and motor/speech delays [1, 2, 3], but the sources provide no data on structural CNS anomalies, respiratory, or dysmorphic features to confirm or refute the diagnosis.
* **P07:** **Cannot be ruled in or out.** P07 does not list developmental delay or intellectual disability, which are the main characteristics mentioned [1, 2, 3]; however, the sources do not provide complete penetrance data or exclusion criteria to definitively rule P07 out.
* **P08:** **Cannot be ruled in or out.** P08 has autistic behavior, which matches "behavioral" features [2], but lacks explicit mentions of developmental delay/intellectual disability [1, 2, 3]; the sources do not state whether behavioral issues can occur in isolation.
* **P09:** **Cannot be ruled in or out.** P09 presents with intellectual disability and global developmental delay [1, 2, 3], but the sources do not document palate, immunologic, or digital features.
* **P10:** **Cannot be ruled in or out.** P10 does not explicitly list intellectual disability or developmental delay [1, 2, 3], but the sources do not provide negative criteria or complete clinical summaries sufficient to rule P10 out.

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Candidate:** **P05** (closely followed by **P06** and **P02**).
  * *Reasoning:* The provided sources specifically identify STISS as presenting with intellectual disability/developmental delay [1, 2, 3], delayed psychomotor development [2], and behavioral manifestations [2]. P05 directly reports all three of these core textual domains: "Global developmental delay", "Intellectual disability", and "Autistic behavior" [1, 2, 3]. 
* **Estimated Probability:** **~20% – 25%** (or an uninformative prior of **10%** [1 in 10]).
  * *Clinical Justification:* Because 7 of the 10 patients (P01, P02, P03, P04, P05, P06, P09) present with developmental delay and/or intellectual disability [1, 2, 3], and the snippets provide no detailed organ-system or dysmorphology data to differentiate between them, assigning a high-confidence probability to any single individual based *strictly* on these sources is not clinically or mathematically supported.

---

### 3. Facts Needed (That Are Missing) to Be Confident

1. **Specific *PSMD12* Molecular Genetic Findings:** Confirmation of a heterozygous pathogenic or likely pathogenic variant or deletion in *PSMD12* on chromosome 17q24 for the patient [5, 6].
2. **Detailed Clinical & Dysmorphology Spectrum:** The full HPO spectrum and clinical summaries from the referenced literature (e.g., Isidor et al. [1, 3] and OMIM 617516 [5]), including characteristic facial gestalt, musculoskeletal abnormalities, and neuroimaging features.
3. **Organ System Involvement and Penetrance Data:** Frequencies of congenital anomalies (e.g., congenital heart disease, renal anomalies, palate defects, microcephaly) in confirmed STISS cohorts to systematically rule out patients whose phenotypes conflict with the disorder.

--------------------------------------------------------------------------------

### Round 3  (picked: P05)

Based solely on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources only state that Stankiewicz-Isidor syndrome is characterized broadly by:
* Haploinsufficiency / heterozygous mutation in *PSMD12* [1, 3, 4, 5, 6].
* Neurodevelopmental phenotypes, including developmental delay / delayed psychomotor development [1, 2, 3].
* Intellectual disability [1, 2, 3].
* Behavioral manifestations ("behavioral ...") [2].

The sources do not provide full clinical descriptions, dysmorphic features, systemic findings, penetrance rates, or exclusionary criteria [1, 2, 3, 5]. Consequently:

* **P01:** **Cannot be ruled in or ruled out.** P01 exhibits motor and speech delay, which aligns with developmental delay / psychomotor delay [1, 2, 3], but the sources lack phenotypic detail to confirm or exclude this diagnosis [1, 2].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits intellectual disability and global developmental delay [1, 2, 3], but the sources provide no information about the dysmorphic, facial, or skeletal features needed to rule P02 in or out [1, 2, 5].
* **P03:** **Cannot be ruled in or ruled out.** P03 has severe global developmental delay [1, 2, 3], but the sources do not describe cardiac, respiratory, or CNS anomalies, preventing ruling P03 in or out [1, 2, 3].
* **P04:** **Cannot be ruled in or ruled out.** P04 has severe global developmental delay [1, 2, 3], but the sources mention nothing about renal, limb, or cardiac anomalies to confirm or exclude P04 [1, 2, 5].
* **P05:** **Cannot be ruled in or ruled out.** P05 has global developmental delay, intellectual disability, and autistic behavior, matching the text fragments in [1], [2], and [3]. However, the sources do not provide specific physical or genitourinary features to definitively confirm or exclude P05 [1, 2, 5].
* **P06:** **Cannot be ruled in or ruled out.** P06 has global developmental delay and intellectual disability [1, 2, 3], but the sources do not supply information on craniofacial, neurological, or respiratory features to rule P06 in or out [1, 2, 3].
* **P07:** **Cannot be ruled in or ruled out.** P07 does not have developmental delay or intellectual disability listed, but the sources do not state whether these features are 100% penetrant or provide exclusionary criteria [1, 2, 3].
* **P08:** **Cannot be ruled in or ruled out.** P08 has autistic behavior, which might correspond to "behavioral ..." [2], but lacks listed developmental delay/intellectual disability; the sources do not state exclusionary rules [1, 2].
* **P09:** **Cannot be ruled in or ruled out.** P09 has global developmental delay and intellectual disability [1, 2, 3], but the sources do not detail palatal, immunological, or skeletal signs to rule P09 in or out [1, 2, 5].
* **P10:** **Cannot be ruled in or ruled out.** P10 does not have explicit developmental delay or intellectual disability listed, but the sources do not supply negative diagnostic criteria or complete phenotypic spectra to rule P10 out [1, 2, 3].

---

### 2. Most Likely Patient and Probability

* **Most likely patient:** **P05**
  * *Reasoning:* P05 is the only patient whose HPO list simultaneously includes features matching all three specific clinical descriptors explicitly provided in the text: "developmental delay" [1, 3] / "delayed psychomotor development" [2], "intellectual disability" [1, 2, 3], and behavioral abnormalities ("behavioral ...", corresponding to "autistic behavior") [2].
* **Probability:** **Cannot be determined with clinical certainty from the text (estimated at ~20–30% based solely on the text, or a baseline of 10% [1 in 10])**. 
  * *Explanation:* The sources do not provide frequencies, odds ratios, or detailed diagnostic profiles [1, 2, 3]. Because several other patients (P02, P03, P04, P06, P09) also match the primary "developmental delay / intellectual disability" criteria [1, 2, 3], a reliable probability cannot be calculated from the provided excerpts alone.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a confident diagnosis, the following information is required but missing from the sources:
1. **Molecular genetic data:** Confirmed presence or absence of a pathogenic heterozygous mutation or deletion in the *PSMD12* gene (17q24) for each patient [4, 5, 6].
2. **Complete clinical phenotype spectrum:** The truncated descriptions in the sources (e.g., the ellipsis in [1], [2], [3], [5]) omit the associated craniofacial dysmorphisms, congenital malformations, and systemic involvement of Stankiewicz-Isidor syndrome.
3. **Penetrance and frequency data:** Data indicating which clinical features are mandatory for diagnosis versus rare or exclusionary [1, 2, 3].

--------------------------------------------------------------------------------

picks across rounds: ['P05', 'P05', 'P05']
