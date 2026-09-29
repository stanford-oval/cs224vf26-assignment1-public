# Plain RAG on Stolerman neurodevelopmental syndrome (KDM6B, OMIM:618505)
model: gemini-3.8-flash   generated: 2026-09-28 20:46

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `KDM6B gene Stolerman neurodevelopmental syndrome`

[1] **KDM6B**  
    https://www.simonssearchlight.org/research/what-we-study/kdm6b/  
    KDM6B-related neurodevelopmental disorder happens when there are changes to the KDM6B gene. These changes can keep the gene from working as it should.

[2] **The clinical and molecular spectrum of the KDM6B-related ...**  
    https://www.sciencedirect.com/science/article/pii/S0002929723001325  
    by D Rots · 2023 · Cited by 36 — Neurodevelopmental abnormalities were present in all individuals with likely pathogenic KDM6B variants. Developmental delay (speech-language, ...

[3] **Stolerman Neurodevelopmental Syndrome (NEDSST)**  
    https://www.malacards.org/card/stolerman_neurodevelopmental_syndrome  
    Stolerman neurodevelopmental syndrome (NEDSST) is a highly variable neurodevelopmental disorder caused by heterozygous mutation in KDM6B on chromosome 17p13.

[4] **Neurodevelopmental disorder with coarse facies and mild ...**  
    http://www.ncbi.nlm.nih.gov/medgen/1682403  
    Stolerman neurodevelopmental syndrome (NEDSST) is a highly variable disorder characterized by developmental delay, often with motor and speech delay,

[5] **The KDM6B mutation: Phenotype and clinical ...**  
    https://www.elsevier.es/es-revista-revista-psiquiatria-salud-mental--286-articulo-the-kdm6b-mutation-phenotype-clinical-S188898912100001X  
    Genetic variants in the KDM6B gene are associated with neurodevelopmental delays and dysmorphic features.

[6] **Stolerman neurodevelopmental syndrome**  
    https://flybase.org/reports/FBhh0001523  
    KDM6B encodes a demethylase that specifically demethylates lysine 27 of histone H3, and thus plays a key role in epigenetic processes controlling chromatin ...

## 2. The context handed to the model
```
[1] KDM6B
https://www.simonssearchlight.org/research/what-we-study/kdm6b/
KDM6B-related neurodevelopmental disorder happens when there are changes to the KDM6B gene. These changes can keep the gene from working as it should.

[2] The clinical and molecular spectrum of the KDM6B-related ...
https://www.sciencedirect.com/science/article/pii/S0002929723001325
by D Rots · 2023 · Cited by 36 — Neurodevelopmental abnormalities were present in all individuals with likely pathogenic KDM6B variants. Developmental delay (speech-language, ...

[3] Stolerman Neurodevelopmental Syndrome (NEDSST)
https://www.malacards.org/card/stolerman_neurodevelopmental_syndrome
Stolerman neurodevelopmental syndrome (NEDSST) is a highly variable neurodevelopmental disorder caused by heterozygous mutation in KDM6B on chromosome 17p13.

[4] Neurodevelopmental disorder with coarse facies and mild ...
http://www.ncbi.nlm.nih.gov/medgen/1682403
Stolerman neurodevelopmental syndrome (NEDSST) is a highly variable disorder characterized by developmental delay, often with motor and speech delay,

[5] The KDM6B mutation: Phenotype and clinical ...
https://www.elsevier.es/es-revista-revista-psiquiatria-salud-mental--286-articulo-the-kdm6b-mutation-phenotype-clinical-S188898912100001X
Genetic variants in the KDM6B gene are associated with neurodevelopmental delays and dysmorphic features.

[6] Stolerman neurodevelopmental syndrome
https://flybase.org/reports/FBhh0001523
KDM6B encodes a demethylase that specifically demethylates lysine 27 of histone H3, and thus plays a key role in epigenetic processes controlling chromatin ...
```

## 3. The gene, from the sources

The *KDM6B* gene is located on chromosome 17p13 [3]. It encodes a demethylase that specifically demethylates lysine 27 of histone H3 [6]. Within the cell, this gene product plays a key role in epigenetic processes that control chromatin [6]. 

Changes or genetic variants in *KDM6B* can keep the gene from working properly [1]. Specifically, heterozygous mutations in *KDM6B* cause Stolerman neurodevelopmental syndrome (NEDSST), a highly variable disorder [3, 4]. Individuals harboring likely pathogenic *KDM6B* variants consistently present with neurodevelopmental abnormalities [2]. The syndrome is characterized by developmental delays, which frequently affect motor and speech-language skills [2, 4]. Additionally, genetic variants in *KDM6B* are associated with dysmorphic features alongside these neurodevelopmental delays [5].

*tokens in 566, out 1676*

## 4. The gene, closed book (no sources; beware hallucinations)

The *KDM6B* gene encodes **lysine-specific demethylase 6B** (also known as JMJD3), an epigenetic enzyme that removes repressive di- and trimethyl marks from histone H3 lysine 27 (H3K27me2/3). By demethylating H3K27, it relaxes chromatin into an active transcriptional state, regulating gene expression programs crucial for neural differentiation, brain development, and synaptic plasticity.

Stolerman neurodevelopmental syndrome (also known as NEDDFAS) is caused by heterozygous *de novo* loss-of-function variants (e.g., nonsense, frameshift, or catalytic missense mutations) in *KDM6B*. These mutations cause haploinsufficiency or impair demethylase activity, leading to aberrant histone methylation and dysregulated expression of neurodevelopmental target genes. This failure of transcriptional regulation results in intellectual disability, speech and motor delays, dysmorphic facial features, and variable seizures.

The condition was first described in **2019**.

**Citation:** 
Stolerman, E. S., et al. (2019). Variants in *KDM6B* are associated with a neurodevelopmental delay with dysmorphic features and variable seizures. *The American Journal of Human Genetics*, 105(3), 613–620.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P08)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Rule-in / Rule-out Evaluation for Each Patient

The sources establish that Stolerman neurodevelopmental syndrome (NEDSST) is caused by heterozygous mutations in *KDM6B* [3] and is a "highly variable" neurodevelopmental disorder [3, 4] associated with developmental delay—particularly motor and speech/language delay [2, 4]—as well as dysmorphic features [5] and potentially coarse facies [4]. Crucially, the sources do **not** provide complete diagnostic criteria, phenotype frequency tables, or any exclusionary clinical criteria [1–6]. 

Because the condition is explicitly "highly variable" [3, 4] and genetic confirmation is required to define it [1, 3], **no patient can be definitively ruled in or ruled out based solely on these sources**:

* **P01:** Cannot be ruled in or ruled out. The patient exhibits speech and language delay and delayed walking (motor delay), consistent with reported developmental delays [2, 4], as well as dysmorphic features [5]. However, the sources provide no molecular data to rule them in [1, 3] and no exclusionary criteria to rule them out [1–6].
* **P02:** Cannot be ruled in or ruled out. The patient has speech and language delay [2, 4] and neurodevelopmental features [1, 2, 5]. The sources do not provide genetic confirmation to rule them in [1, 3] nor exclusionary criteria to rule them out [1–6].
* **P03:** Cannot be ruled in or ruled out. The patient exhibits facial dysmorphisms (e.g., thick eyebrow, thick lower lip vermilion, wide nose) which could correspond to dysmorphic features [5] or coarse facies [4], alongside speech delay [2, 4]. However, the sources do not provide enough clinical specificity to rule them in, nor exclusionary criteria to rule them out [1–6].
* **P04:** Cannot be ruled in or ruled out. The patient shows delayed walking and delayed speech and language development [2, 4] with dysmorphic features [5]. Definitive rule-in is impossible without molecular testing [1, 3], and the sources provide no basis to rule them out [1–6].
* **P05:** Cannot be ruled in or ruled out. The patient presents with motor and speech delay [2, 4] and dysmorphic features [5]. The sources lack molecular data to rule them in [1, 3] and provide no clinical exclusionary rules to rule them out [1–6].
* **P06:** Cannot be ruled in or ruled out. The patient exhibits mild intellectual disability (aligning with the partial title "coarse facies and mild ..." [4]) and speech/language delay [2, 4]. However, the sources do not give specific criteria to rule them in [1–6], nor exclusionary rules to rule them out [1–6].
* **P07:** Cannot be ruled in or ruled out. The patient has motor delay (delayed ability to walk) and speech delay [2, 4], along with neurodevelopmental features [1, 2, 5]. The sources do not provide molecular confirmation to rule them in [1, 3] nor exclusionary features to rule them out [1–6].
* **P08:** Cannot be ruled in or ruled out. The patient displays motor delay (delayed walking) [4], speech and language delay [2, 4], mild intellectual disability (matching the fragment "mild ..." [4]), and dysmorphic features [5]. However, the sources provide no genetic testing data to rule them in [1, 3] and no criteria to rule them out [1–6].
* **P09:** Cannot be ruled in or ruled out. The patient presents with motor delay (delayed walking), absent speech [2, 4], and dysmorphic features [5]. There is no genetic data to rule them in [1, 3] and no exclusionary criteria to rule them out [1–6].
* **P10:** Cannot be ruled in or ruled out. The patient has motor delay and neurodevelopmental abnormalities [1, 2, 4]. Without molecular testing, they cannot be ruled in [1, 3], and without exclusionary criteria, they cannot be ruled out [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P08**
  * *Reasoning:* Source [4] identifies the condition as a disorder characterized by "developmental delay, often with motor and speech delay" [4] with a title referencing "coarse facies and mild [intellectual disability]..." [4], and source [5] associates it with "dysmorphic features." Patient P08 exhibits the specific triad of **delayed ability to walk** (motor delay) [4], **delayed speech and language development** [2, 4], and **mild intellectual disability** [4], combined with prominent craniofacial dysmorphic features [5].
* **Estimated Probability:** **~15%**
  * *Justification:* Because exactly one patient in the cohort of 10 has the condition, the prior baseline probability for any individual patient is 10%. Since the sources state the disorder is "highly variable" [3, 4] and all 10 patients exhibit neurodevelopmental delays [1, 2], the distinguishing clinical power of the provided text is extremely weak. P08 is only marginally favored over other candidates (such as P06 or P01) due to textual overlap with the fragmented phrases in [2], [4], and [5].

---

### 3. Missing Facts Needed for Confidence

To make a confident diagnosis, the following information—which the sources do not provide—is required:
1. **Molecular Genetic Data:** The sources do not include sequencing or copy-number variant data for any patient to identify a heterozygous pathogenic variant in *KDM6B* on chromosome 17p13, which is the defining etiology of Stolerman neurodevelopmental syndrome [1, 3].
2. **Complete Clinical Spectrum & HPO Frequencies:** The sources state the phenotype is "highly variable" [3, 4] and truncate the list of features (e.g., "speech-language, ..." [2]; "mild ..." [4]; "motor and speech delay, ..." [4]). The sources do not provide a full, untruncated phenotypic description or frequency statistics for individual HPO terms.
3. **Exclusionary Criteria:** The sources provide no negative predictors, contraindicated features, or differential diagnosis criteria that would allow clinical exclusion of any of the 10 patients [1–6].

--------------------------------------------------------------------------------

### Round 2  (picked: P08)

Based solely on the provided sources, here is the clinical genetic assessment:

---

### 1. Patient Rule-In / Rule-Out Assessment

The provided sources describe Stolerman neurodevelopmental syndrome as a "highly variable" disorder [3, 4] characterized by "developmental delay (speech-language, ...)" [2], "motor and speech delay" [4], "neurodevelopmental abnormalities" [2], and "dysmorphic features" [5]. 

Because the sources do not provide an exhaustive phenotypic spectrum, specific HPO frequencies, or exclusionary clinical criteria, **none of the patients can be definitively ruled in or ruled out** using these sources alone:

* **P01**: **Cannot rule in or out.** The patient displays delayed speech and language development and delayed ability to walk, which are consistent with the speech and motor delay described in [2, 4], as well as dysmorphic features [5]. However, the sources do not mention whether specific features like microtia or pulmonic stenosis occur in the syndrome, nor do they give criteria to rule this patient out [1–6].
* **P02**: **Cannot rule in or out.** The patient has delayed speech and language development and developmental delay, matching [2, 4]. The sources state the condition is "highly variable" [3, 4], but they do not provide specific data regarding features such as macrocephaly or tall stature [1–6].
* **P03**: **Cannot rule in or out.** Displays speech delay (absent speech) and severe global developmental delay [2, 4]. Source [4] hints at "coarse facies" in its title, which might align with thick eyebrows, thick lips, and a wide nose, but the sources do not provide enough clinical criteria to confirm or exclude this presentation [1–6].
* **P04**: **Cannot rule in or out.** Exhibits delayed walking, delayed speech/language development [2, 4], and dysmorphic features [5]. The sources do not document whether postaxial polydactyly or hypoplasia of the corpus callosum are consistent with or exclusionary for *KDM6B* mutations [1–6].
* **P05**: **Cannot rule in or out.** Presents with delayed speech and language development, delayed ability to walk [2, 4], and dysmorphic features [5]. The sources do not contain sufficient granular phenotypic data to confirm or exclude these findings [1–6].
* **P06**: **Cannot rule in or out.** Displays global developmental delay, delayed speech and language development [2, 4], and "mild intellectual disability," which overlaps with the truncated title in [4] ("Neurodevelopmental disorder with coarse facies and mild..."). However, the sources do not provide sufficient clinical detail to rule the patient in or out [1–6].
* **P07**: **Cannot rule in or out.** Has delayed ability to walk and delayed speech/language development [2, 4]. The sources state the disorder is highly variable [3, 4] but do not provide specific details on joint hypermobility or pes planus to rule the patient in or out [1–6].
* **P08**: **Cannot rule in or out.** Exhibits motor delay (delayed walking), speech delay [2, 4], dysmorphic features [5], and mild intellectual disability [4]. Nevertheless, the provided excerpts omit cardiac and systemic features necessary to confirm or exclude this diagnosis [1–6].
* **P09**: **Cannot rule in or out.** Exhibits delayed ability to walk and speech delay (absent speech) [2, 4]. The sources provide no information regarding renal agenesis or congenital heart defects in relation to *KDM6B* [1–6].
* **P10**: **Cannot rule in or out.** Exhibits motor delay and neurodevelopmental traits [2, 4]. However, the sources lack detail regarding drooling or anxiety to confirm or exclude the syndrome [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P08** (or alternatively **P06**)
* **Estimated Probability:** **10% (0.10)**

**Rationale:**
Based strictly on the provided text, every patient shares core broad features described in the sources (developmental delay involving speech and/or motor skills [2, 4]). Source [4] is titled *"Neurodevelopmental disorder with coarse facies and mild..."* and specifically highlights "developmental delay, often with motor and speech delay" [4], alongside "dysmorphic features" [5]. Both P08 and P06 have explicitly documented "Delayed speech and language development," "Delayed ability to walk" (motor delay), and "Mild intellectual disability" [4]. 

However, because the disorder is explicitly identified as "highly variable" [3, 4] and the text cuts off without specific diagnostic criteria, statistical weighting, or complete clinical profiles [2, 4], **the sources do not provide discriminatory evidence to favor any single patient over the others**. Therefore, strictly under the provided sources, each of the 10 candidates has an equal prior probability of **10% (1/10)**.

---

### 3. Facts Needed (and Missing from the Sources) to Be Confident

To establish a definitive diagnosis, the following information is missing from sources [1]–[6]:
1. **Molecular Genetic Data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in the *KDM6B* gene (chromosome 17p13) for the patient [2, 3].
2. **Complete Clinical Spectrum and Frequency Data:** The complete text of source [2] (which cuts off mid-sentence: *"Developmental delay (speech-language, ...)"*) and source [4] (which cuts off at *"often with motor and speech delay,"* and has an incomplete title) detailing the specific frequencies of craniofacial, skeletal, cardiac, and neurological features.
3. **Exclusionary Criteria:** Specific phenotypic features that are known *not* to occur with *KDM6B* mutations.
4. **Differential Diagnostic Data:** Features that distinguish Stolerman syndrome from overlapping syndromic neurodevelopmental disorders presenting with motor/speech delay and dysmorphisms.

--------------------------------------------------------------------------------

### Round 3  (picked: P08)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources define Stolerman neurodevelopmental syndrome (NEDSST) as a **"highly variable"** disorder [3, 4] associated with **heterozygous mutations in *KDM6B*** [1, 3], characterized broadly by **neurodevelopmental abnormalities/delays**, especially **speech and motor delay** [2, 4], and **dysmorphic features** [5]. 

The sources provide **no specific diagnostic criteria, frequency data, or exclusionary features**. Therefore, the sources do **not** provide enough information to definitively rule in or rule out any of the 10 patients:

* **P01:** Cannot be ruled in or out. Shows delayed speech and language development, delayed walking (motor delay), and dysmorphic features, which are consistent with the general features in [2], [4], and [5], but the sources provide no specific exclusionary or confirmatory criteria.
* **P02:** Cannot be ruled in or out. Exhibits delayed speech and language development and global developmental delay [2, 4], but NEDSST's high variability [3, 4] and lack of detailed phenotypic profiles in the sources prevent confirmation or exclusion.
* **P03:** Cannot be ruled in or out. Exhibits severe global developmental delay, absent speech, and dysmorphic features [2, 4, 5], but the sources do not specify whether severe phenotypes or these specific dysmorphisms are typical or exclusionary.
* **P04:** Cannot be ruled in or out. Features delayed walking, fine motor delay, speech delay, and dysmorphic features [2, 4, 5]; however, the sources do not provide sufficient phenotypic detail to distinguish P04 from other syndromes.
* **P05:** Cannot be ruled in or out. Displays speech delay, delayed walking, and dysmorphic features [2, 4, 5], but cannot be confirmed or excluded based on the provided text.
* **P06:** Cannot be ruled in or out. Shows global developmental delay, speech delay, mild intellectual disability, and dysmorphic features [2, 4, 5], but lacks genetic or specific phenotypic confirmation in the sources.
* **P07:** Cannot be ruled in or out. Has delayed walking, speech delay, and intellectual disability [2, 4], but these broad neurodevelopmental delays are non-specific without further criteria.
* **P08:** Cannot be ruled in or out. Features motor delay (delayed walking), speech delay, dysmorphic features, and mild intellectual disability [2, 4, 5], but the text lacks specific criteria to confirm Stolerman syndrome or exclude alternatives.
* **P09:** Cannot be ruled in or out. Features delayed walking, absent speech, and hypotonia [2, 4], but cannot be confirmed or excluded using the limited source descriptions.
* **P10:** Cannot be ruled in or out. Presents with motor delay and intellectual disability [2, 4], but the broad description in the sources does not permit a definitive determination.

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P08** (or alternatively **P06**)
  * *Reasoning:* While none can be confirmed, the title in source [4] notes *"Neurodevelopmental disorder with coarse facies and mild..."*, and sources [2] and [4] highlight developmental delay encompassing motor and speech delays, alongside dysmorphic features [5]. Both **P08** and **P06** explicitly feature *"Delayed speech and language development"*, developmental/motor delay, and *"Mild intellectual disability"*. P08 explicitly includes both *"Delayed ability to walk"* (motor delay) and *"Delayed speech and language development"* alongside dysmorphic features [2, 4, 5].
* **Probability:** **~10% (0.10)**
  * *Reasoning:* Because the condition is described as *"highly variable"* [3, 4] and all 10 patients present with overlapping neurodevelopmental, speech, and/or motor delays [2, 4], the provided sources do not offer clinically discriminative features. Given that exactly one patient has the condition and the sources cannot distinguish among them, the baseline probability for any single candidate remains approximately **1 in 10 (10%)**.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To make a confident diagnosis, the following information is required:
1. **Molecular / Genetic Data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in the *KDM6B* gene (chromosome 17p13) for the patient [1, 2, 3].
2. **Specific Phenotypic Spectrum & Frequencies:** A detailed clinical profile of Stolerman syndrome, including specific craniofacial hallmarks, systemic/organ involvement, and behavioral phenotypes, as opposed to high-level descriptors like "highly variable" [3, 4] and "dysmorphic features" [5].
3. **Differential Diagnoses & Exclusion Criteria:** Phenotypic descriptions or molecular findings for the alternative syndromes represented by the other 9 patients to rule them out (the sources describe only *KDM6B*).
4. **Complete Source Text:** Un-truncated clinical information (e.g., the full text truncated in citations [2] and [4]).

--------------------------------------------------------------------------------

picks across rounds: ['P08', 'P08', 'P08']
