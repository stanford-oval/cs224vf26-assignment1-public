# Plain RAG on Jaberi-Elahi syndrome (GTPBP2, OMIM:617988)
model: gemini-3.8-flash   generated: 2026-09-28 20:45

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `GTPBP2 gene Jaberi-Elahi syndrome`

[1] **P340: Jaberi-Elahi syndrome caused by maternal UPD 6 ...**  
    https://www.gimopen.org/article/S2949-7744(24)00380-7/fulltext  
    by G Perry · 2024 · Cited by 1 — This condition exhibits an autosomal recessive inheritance pattern, characterized by biallelic inactivation of GTPBP2. GTP Binding Protein 2, the encoded ...

[2] **Entry - #617988 - JABERI-ELAHI SYNDROME; JABELS**  
    https://omim.org/entry/617988  
    Biallelic inactivating variants in the GTPBP2 gene cause a neurodevelopmental disorder with severe intellectual disability. Europ. J. Hum. Genet. 26: 592 ...

[3] **Jaberi-Elahi syndrome: Exploring a novel GTPBP2 ...**  
    https://www.sciencedirect.com/science/article/pii/S1769721224000454  
    by J Manoochehri · 2024 · Cited by 3 — Jaberi-Elahi syndrome is an extremely rare genetic disease caused by pathogenic variants in GTPBP2. The core symptoms of this disease are intellectual ...

[4] **A Novel Homozygous Frameshift GTPBP2 Variant in Jaberi ...**  
    https://karger.com/msy/article/doi/10.1159/000552675/949444/A-Novel-Homozygous-Frameshift-GTPBP2-Variant-in  
    Jaberi-Elahi syndrome is a rare autosomal recessive neurodevelopmental disorder caused by biallelic loss-of-function variants in GTPBP2. The ...

[5] **GTPBP2 | Jaberi-Elahi syndrome | Autosomal recessive by ...**  
    https://thegencc.org/submissions/SGC-107075.2  
    The GTPBP2 (guanosine triphosphate binding protein 2) gene is located on chromosome 6 at 6p21 and encodes a member of the GTP-binding superfamily.

[6] **Abstract Details**  
    https://www.aan.com/msa/Public/Events/AbstractDetails/64411  
    Nearly 20 mutations of the GTPBP2 gene have been associated with JABELS, and more variants continue to be described. This case demonstrates a novel missense ...

## 2. The context handed to the model
```
[1] P340: Jaberi-Elahi syndrome caused by maternal UPD 6 ...
https://www.gimopen.org/article/S2949-7744(24)00380-7/fulltext
by G Perry · 2024 · Cited by 1 — This condition exhibits an autosomal recessive inheritance pattern, characterized by biallelic inactivation of GTPBP2. GTP Binding Protein 2, the encoded ...

[2] Entry - #617988 - JABERI-ELAHI SYNDROME; JABELS
https://omim.org/entry/617988
Biallelic inactivating variants in the GTPBP2 gene cause a neurodevelopmental disorder with severe intellectual disability. Europ. J. Hum. Genet. 26: 592 ...

[3] Jaberi-Elahi syndrome: Exploring a novel GTPBP2 ...
https://www.sciencedirect.com/science/article/pii/S1769721224000454
by J Manoochehri · 2024 · Cited by 3 — Jaberi-Elahi syndrome is an extremely rare genetic disease caused by pathogenic variants in GTPBP2. The core symptoms of this disease are intellectual ...

[4] A Novel Homozygous Frameshift GTPBP2 Variant in Jaberi ...
https://karger.com/msy/article/doi/10.1159/000552675/949444/A-Novel-Homozygous-Frameshift-GTPBP2-Variant-in
Jaberi-Elahi syndrome is a rare autosomal recessive neurodevelopmental disorder caused by biallelic loss-of-function variants in GTPBP2. The ...

[5] GTPBP2 | Jaberi-Elahi syndrome | Autosomal recessive by ...
https://thegencc.org/submissions/SGC-107075.2
The GTPBP2 (guanosine triphosphate binding protein 2) gene is located on chromosome 6 at 6p21 and encodes a member of the GTP-binding superfamily.

[6] Abstract Details
https://www.aan.com/msa/Public/Events/AbstractDetails/64411
Nearly 20 mutations of the GTPBP2 gene have been associated with JABELS, and more variants continue to be described. This case demonstrates a novel missense ...
```

## 3. The gene, from the sources

The *GTPBP2* gene is located on chromosome 6 at 6p21 and encodes GTP Binding Protein 2 (guanosine triphosphate binding protein 2), which belongs to the GTP-binding superfamily [1, 5]. The specific cellular functions of this protein are not covered in the provided sources [1, 5]. 

Pathogenic variants in *GTPBP2* cause Jaberi-Elahi syndrome, an extremely rare neurodevelopmental disorder with an autosomal recessive inheritance pattern [1, 3, 4]. The condition is caused by biallelic loss-of-function or inactivating variants in *GTPBP2*, resulting in biallelic inactivation of the gene [1, 2, 4]. Reported disease-causing mechanisms include homozygous frameshift variants, missense mutations, and maternal uniparental disomy of chromosome 6 [1, 4, 6]. Nearly 20 different mutations in *GTPBP2* have been associated with the syndrome, and their inactivation of the gene product results in core clinical manifestations including severe intellectual disability [2, 3, 6].

*tokens in 643, out 1867*

## 4. The gene, closed book (no sources; beware hallucinations)

*GTPBP2* encodes GTP-binding protein 2, a cytosolic GTPase homologous to translation elongation/release factors. Functioning alongside the release factor-like protein Pelota (PELO), GTPBP2 mediates ribosome rescue during mRNA translation surveillance (ribosome-associated quality control). It dissociates subunits of stalled ribosomes on defective mRNAs, recycling the translation machinery and preventing the accumulation of toxic nascent peptides—a process vital for neuronal survival. 

Biallelic loss-of-function variants (e.g., nonsense or frameshift mutations) disrupt this rescue mechanism, leading to persistent ribosome stalling, impaired protein synthesis, neuroinflammation, and neurodegeneration. This causes Jaberi-Elahi syndrome (autosomal recessive intellectual developmental disorder-54), characterized by profound intellectual disability, microcephaly, spasticity, and motor dysfunction. 

The disorder was first described in **2016**.

**Citation:**  
Jaberi, E., Rohani, M., Shahidi, G. A., Nafissi, S., Soleimani, M., Faghihi, M. A., & Elahi, E. (2016). Identification of a mutation in *GTPBP2* in patients of a family with severe intellectual disability and motor dysfunction. *European Journal of Medical Genetics*, 59(9), 452–456.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P09)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule-In / Rule-Out)

The sources establish only that Jaberi-Elahi syndrome (JABELS) is an autosomal recessive neurodevelopmental disorder caused by biallelic inactivating/loss-of-function variants in *GTPBP2* [1, 2, 4], and that its core feature is severe intellectual disability [2, 3]. The sources do not provide a detailed clinical synopsis, specific HPO terms, dysmorphic features, or neuroimaging criteria [1–6].

* **P01**: **Cannot be ruled in or ruled out.** The patient has intellectual disability, which aligns broadly with a neurodevelopmental disorder [2, 4], but the sources do not provide sufficient phenotypic detail (e.g., regarding microcephaly or intrauterine growth retardation) to rule P01 in or out [1–6].
* **P02**: **Cannot be ruled in or ruled out.** The patient has severe intellectual disability, which matches the description in the sources [2, 3], but the sources do not report whether findings like joint contractures, thin corpus callosum, or exaggerated startle response occur in JABELS [1–6].
* **P03**: **Cannot be ruled in or ruled out.** The patient has intellectual disability and global developmental delay, consistent with a neurodevelopmental disorder [2, 4], but the sources provide no data to confirm or exclude this presentation [1–6].
* **P04**: **Cannot be ruled in or ruled out.** The patient has profound intellectual disability and global developmental delay [2, 4], but the sources do not provide information on the extensive dysmorphic, neuromuscular, or neuroimaging features to rule P04 in or out [1–6].
* **P05**: **Cannot be ruled in or ruled out.** The patient has severe intellectual disability [2, 3], but the sources do not mention whether cerebellar hypoplasia, hypertelorism, or strabismus are features of JABELS [1–6].
* **P06**: **Cannot be ruled in or ruled out.** While intellectual disability is not explicitly listed, the patient has severe neurodevelopmental signs (absent speech, poor head control) [2, 4]; however, the sources do not provide the clinical criteria needed to include or exclude P06 [1–6].
* **P07**: **Cannot be ruled in or ruled out.** Intellectual disability is not specified, but the sources do not provide phenotypic exclusion criteria to definitively rule P07 in or out [1–6].
* **P08**: **Cannot be ruled in or ruled out.** The patient has intellectual disability and developmental delays consistent with a neurodevelopmental disorder [2, 4], but the sources do not list specific skeletal or facial features of JABELS to rule P08 in or out [1–6].
* **P09**: **Cannot be ruled in or ruled out.** The patient has severe intellectual disability [2, 3] and global developmental delay [2, 4], but the sources do not describe specific neuroimaging findings (cerebellar atrophy, thin corpus callosum) or dysmorphic features to confirm or exclude this profile [1–6].
* **P10**: **Cannot be ruled in or ruled out.** The patient has severe intellectual disability [2, 3], but the sources do not mention whether lower limb amyotrophy or dental abnormalities are associated with *GTPBP2* [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most likely patient:** **P09** (tied with P02, P05, and P10)
* **Estimated probability based strictly on the provided sources:** **~20%** (1 in 5)

**Reasoning:** 
The sources explicitly state that JABELS is characterized by "severe intellectual disability" [2, 3]. Among the 10 candidates, exactly five patients (P02, P04, P05, P09, P10) exhibit severe or profound intellectual disability [2]. Because the provided sources do not describe any other distinguishing clinical, facial, or neuroimaging features [1–6], they do not permit differentiation among these candidates. Selecting P09 yields a probability of approximately 20% among the matching candidates (or ~10% across all 10 unselected patients).

---

### 3. Facts Needed to Be Confident (Missing from Sources)

To establish a confident clinical or molecular diagnosis, the following information—not provided in the sources—is required:
1. **Molecular genetic data:** Demonstration of biallelic pathogenic/inactivating variants in *GTPBP2* (or uniparental disomy of chromosome 6 involving *GTPBP2*) in the patient [1, 2, 4, 5].
2. **Comprehensive phenotypic spectrum / HPO profile:** A detailed delineation of characteristic JABELS features (e.g., whether secondary microcephaly, cerebellar atrophy, thin corpus callosum, specific seizures, or distinct facial dysmorphisms are canonical) [1–6].
3. **Exclusionary criteria:** Clear knowledge of atypical or exclusionary features that rule out *GTPBP2*-related disease [1–6].

--------------------------------------------------------------------------------

### Round 2  (picked: P09)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluations (Rule In / Rule Out)

The provided sources define Jaberi-Elahi syndrome (JABELS) as an autosomal recessive [1, 4] neurodevelopmental disorder caused by biallelic loss-of-function or inactivating variants in *GTPBP2* [1, 2, 4], characterized by "severe intellectual disability" [2] (with core symptoms including "intellectual..." [3]). 

Critically, **the sources do not provide a detailed clinical phenotypic spectrum, specific HPO terms, or exclusionary criteria** [1–6]. Consequently:

* **P01:** **Cannot rule in or rule out.** The patient has "Intellectual disability," but the sources do not provide sufficient clinical detail or severity criteria to confirm or exclude this profile [1–6].
* **P02:** **Cannot rule in or rule out.** The patient has "Severe intellectual disability," which matches the descriptor in [2], but the sources do not mention whether features such as joint contractures, kyphosis, or thin corpus callosum are part of or exclusionary for JABELS [1–6].
* **P03:** **Cannot rule in or rule out.** The patient has "Intellectual disability," but the text provides no information regarding ocular (myopia) or otologic manifestations to confirm or exclude [1–6].
* **P04:** **Cannot rule in or rule out.** The patient has "Profound intellectual disability" and extensive multisystem involvement; the sources state JABELS causes "severe intellectual disability" [2], but they do not state whether profound presentations or these systemic anomalies are consistent with or exclude JABELS [1–6].
* **P05:** **Cannot rule in or rule out.** The patient has "Severe intellectual disability" [2], but the sources provide no information to evaluate the specific craniofacial, ocular, or cerebellar findings [1–6].
* **P06:** **Cannot rule in or rule out.** The patient lacks an explicit designation of intellectual disability, but has neurodevelopmental delay signs; the sources do not provide sufficient phenotypic criteria to definitively exclude this patient [1–6].
* **P07:** **Cannot rule in or rule out.** The patient does not have intellectual disability explicitly listed; however, the sources do not provide negative diagnostic criteria to formally rule them out [1–6].
* **P08:** **Cannot rule in or rule out.** The patient has "Intellectual disability," but the sources lack dysmorphology and musculoskeletal details needed to confirm or exclude [1–6].
* **P09:** **Cannot rule in or rule out.** The patient presents with "Severe intellectual disability" [2] and central nervous system features, but the sources do not list specific neuroradiological or facial features to confirm or exclude JABELS [1–6].
* **P10:** **Cannot rule in or rule out.** The patient has "Severe intellectual disability" [2], but the sources do not describe neuromuscular features (e.g., lower limb amyotrophy) to confirm or exclude [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P09** (tied with **P02**, **P05**, and **P10**). 
* **Probability:** **~25% (0.25)**.

**Reasoning:**
The only specific clinical feature provided by the sources is that JABELS is a "neurodevelopmental disorder with severe intellectual disability" [2]. Exactly four patients explicitly carry the term "Severe intellectual disability" (P02, P05, P09, and P10). Because the sources provide no further clinical differentiating criteria [1–6], each of these four candidates is equally supported by the text, yielding a probability of approximately 25% (or 10% if considering all 10 uninformative cases equally). P09 is selected as a representative candidate among those matching this criterion.

---

### 3. Facts Needed to Be Confident (Not Provided in Sources)

To establish a definitive diagnosis, the following information is required:
1. **Molecular Genetic Data:** Confirmation of biallelic pathogenic, loss-of-function, or inactivating variants in *GTPBP2* [1, 2, 4], or uniparental disomy (UPD 6) involving *GTPBP2* [1, 5].
2. **Comprehensive Phenotypic Spectrum:** A detailed description of core, recurrent, or pathognomonic clinical features (e.g., specific neuroimaging findings such as cerebellar or corpus callosum anomalies, seizure types, or dysmorphic features) [1–6].
3. **Exclusionary Criteria:** Clear negative diagnostic criteria or atypical features that rule out JABELS [1–6].
4. **Family / Segregation History:** Evidence demonstrating an autosomal recessive pattern of inheritance consistent with *GTPBP2* loss of function [1, 4].

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources define Jaberi-Elahi syndrome (JABELS) as an autosomal recessive neurodevelopmental disorder caused by biallelic loss-of-function/inactivating variants in *GTPBP2* [1, 2, 4, 5] characterized by "severe intellectual disability" [2] (with core symptoms including "intellectual..." [3]). 

Crucially, **the sources do not provide any detailed phenotypic spectrum, clinical diagnostic criteria, neuroimaging findings, dysmorphic features, or exclusion criteria** [1–6]. As a result, **none of the patients can be definitively ruled in or ruled out** based solely on the provided texts:

* **P01**: **Cannot be ruled in or ruled out.** Features "intellectual disability" [2, 3], but the sources do not specify whether non-severe forms occur, nor do they confirm or exclude microcephaly, strabismus, constipation, or intrauterine growth retardation [1–6].
* **P02**: **Cannot be ruled in or ruled out.** Displays "severe intellectual disability" [2], but the sources do not mention seizures, joint contractures, thin corpus callosum, cerebral atrophy, or progressive microcephaly [1–6].
* **P03**: **Cannot be ruled in or ruled out.** Features "intellectual disability" [2, 3], but severity is unspecified, and the sources do not mention myopia, feeding issues, or recurrent otitis media [1–6].
* **P04**: **Cannot be ruled in or ruled out.** Displays "profound intellectual disability" rather than "severe" [2]; the sources do not document any of the extensive neurological, skeletal, or dysmorphic findings listed [1–6].
* **P05**: **Cannot be ruled in or ruled out.** Exhibits "severe intellectual disability" [2], but the sources provide no data on facial morphology, strabismus, cerebellar hypoplasia, or hypotonia [1–6].
* **P06**: **Cannot be ruled in or ruled out.** Does not explicitly list intellectual disability [2], though it shows developmental deficits (absent speech); the sources do not mention seizures, corpus callosum anomalies, or tone abnormalities [1–6].
* **P07**: **Cannot be ruled in or ruled out.** Lacks an explicit mention of intellectual disability [2]; the sources do not confirm or refute facial features, short stature, or seizures [1–6].
* **P08**: **Cannot be ruled in or ruled out.** Has "intellectual disability" [2, 3], but the severity is not stated, and the sources do not report on cerebellar atrophy, facial dysmorphisms, or skeletal findings [1–6].
* **P09**: **Cannot be ruled in or ruled out.** Exhibits "severe intellectual disability" [2], but the sources make no mention of cerebellar atrophy, ventricular dilatation, thin corpus callosum, seizures, or specific facial features [1–6].
* **P10**: **Cannot be ruled in or ruled out.** Exhibits "severe intellectual disability" [2], but the sources provide no information regarding lower limb amyotrophy, dental anomalies, or dysarthria [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Candidate:** **P09** (tied with **P02, P05, and P10**)
* **Estimated Probability:** **~25% (0.25)** among the subset matching the specific textual descriptor, or **10% (0.10)** across all 10 patients.

**Justification:** 
The only specific clinical term supplied in the text is "severe intellectual disability" [2]. Four patients explicitly carry this exact term (**P02, P05, P09, and P10**). Because the provided sources contain zero differentiating phenotypic, radiological, or dysmorphic details [1–6], they do not permit a distinction among these four. If forced to nominate one, **P09** can be selected, but from the sources alone, it has an equal ~25% likelihood among the 4 candidates matching the explicit "severe intellectual disability" descriptor [2] (or a baseline 10% uniform probability if non-severe intellectual disability profiles cannot be formally excluded [1–6]).

---

### 3. Facts Needed to Establish Confidence

To make a definitive and confident diagnosis, the following information is required but missing from the provided sources:

1. **Molecular Genetic Data:** 
   * Confirmation of biallelic pathogenic/loss-of-function variants in *GTPBP2* [1, 2, 4, 6] or maternal uniparental disomy of chromosome 6 (UPD 6) [1, 5] for the patient.
2. **Comprehensive Phenotypic and Imaging Spectrum:**
   * Specific clinical features typically associated with JABELS (e.g., whether microcephaly, cerebellar atrophy, thin corpus callosum, seizures, or particular dysmorphic features are established features of this syndrome) [1–6].
3. **Exclusionary Criteria:**
   * Knowledge of which clinical or radiological findings are inconsistent with or exclusionary for JABELS [1–6].

--------------------------------------------------------------------------------

picks across rounds: ['P09', 'P09', 'P01']
