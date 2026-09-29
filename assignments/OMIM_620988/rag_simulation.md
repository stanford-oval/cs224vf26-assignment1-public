# Plain RAG on Intellectual developmental disorder, autosomal dominant 75 (DHX9, OMIM:620988)
model: gemini-3.8-flash   generated: 2026-09-28 20:49

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `DHX9 gene Intellectual developmental disorder, autosomal dominant 75`

[1] **620988 - INTELLECTUAL DEVELOPMENTAL DISORDER, ...**  
    https://omim.org/entry/620988  
    autosomal dominant intellectual developmental disorder-75 (MRD75) is caused by heterozygous mutation in the DHX9 gene (603115) on chromosome 1q ...

[2] **Intellectual Developmental Disorder, Autosomal Dominant 75**  
    https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_75  
    Autosomal dominant intellectual developmental disorder-75 (MRD75) is a neurodevelopmental disorder with material basis in heterozygous mutation in DHX9 on ...

[3] **autosomal dominant intellectual developmental disorder 75**  
    https://zfin.org/DOID:0061048  
    An autosomal dominant intellectual developmental disorder that heterozygous mutation in the DHX9 gene on chromosome 1q25.

[4] **autosomal dominant intellectual developmental disorder 75 ...**  
    https://www.informatics.jax.org/disease/DOID:0061048  
    Definition: An autosomal dominant intellectual developmental disorder that has_material_basis_in heterozygous mutation in the DHX9 gene on chromosome 1q25. Term ...

[5] **DHX9**  
    https://panelapp.genomicsengland.co.uk/panels/genes/DHX9  
    Green DHX9 in Intellectual disability. Level 2: Developmental ... Phenotypes. Intellectual developmental disorder, autosomal dominant 75, OMIM:620988.

[6] **DHX9 - DECIPHER v11.40**  
    https://www.deciphergenomics.org/gene/DHX9/overview/clinical-info  
    DHX9-related neurodevelopmental disorder. Intellectual developmental disorder, autosomal dominant 75 (Autosomal dominant) - GenCC Strong: 2 Moderate: 1

## 2. The context handed to the model
```
[1] 620988 - INTELLECTUAL DEVELOPMENTAL DISORDER, ...
https://omim.org/entry/620988
autosomal dominant intellectual developmental disorder-75 (MRD75) is caused by heterozygous mutation in the DHX9 gene (603115) on chromosome 1q ...

[2] Intellectual Developmental Disorder, Autosomal Dominant 75
https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_75
Autosomal dominant intellectual developmental disorder-75 (MRD75) is a neurodevelopmental disorder with material basis in heterozygous mutation in DHX9 on ...

[3] autosomal dominant intellectual developmental disorder 75
https://zfin.org/DOID:0061048
An autosomal dominant intellectual developmental disorder that heterozygous mutation in the DHX9 gene on chromosome 1q25.

[4] autosomal dominant intellectual developmental disorder 75 ...
https://www.informatics.jax.org/disease/DOID:0061048
Definition: An autosomal dominant intellectual developmental disorder that has_material_basis_in heterozygous mutation in the DHX9 gene on chromosome 1q25. Term ...

[5] DHX9
https://panelapp.genomicsengland.co.uk/panels/genes/DHX9
Green DHX9 in Intellectual disability. Level 2: Developmental ... Phenotypes. Intellectual developmental disorder, autosomal dominant 75, OMIM:620988.

[6] DHX9 - DECIPHER v11.40
https://www.deciphergenomics.org/gene/DHX9/overview/clinical-info
DHX9-related neurodevelopmental disorder. Intellectual developmental disorder, autosomal dominant 75 (Autosomal dominant) - GenCC Strong: 2 Moderate: 1
```

## 3. The gene, from the sources

The *DHX9* gene is located on chromosome 1q25 [1, 3, 4]. Heterozygous mutations in *DHX9* provide the material basis for and cause intellectual developmental disorder, autosomal dominant 75 (also designated as MRD75) [1, 2, 4]. This condition is classified as an autosomal dominant neurodevelopmental and intellectual disability disorder [2, 5, 6]. Beyond noting that the disorder is inherited in an autosomal dominant manner with clinical evidence linking the gene to the phenotype, the provided sources do not state what the specific gene product of *DHX9* is [1, 5, 6]. Additionally, what this gene product does inside the cell is not covered in the sources [1, 2, 3, 4, 5, 6]. Finally, the exact molecular or cellular mechanisms explaining how variants in *DHX9* lead to disease are not covered, other than the identification of heterozygous mutations as the underlying cause [1, 2, 4].

*tokens in 518, out 1421*

## 4. The gene, closed book (no sources; beware hallucinations)

The ***DHX9*** gene encodes DEAH-box helicase 9 (also known as RNA helicase A), a multifunctional, ATP-dependent enzyme capable of unwinding both double-stranded RNA and DNA. It plays essential roles in transcription, RNA processing, translation, DNA repair, and the resolution of secondary nucleic acid structures such as R-loops and G-quadruplexes.

Heterozygous *de novo* variants in *DHX9* cause **intellectual developmental disorder, autosomal dominant 75** (OMIM #620404). This neurodevelopmental syndrome is characterized by developmental delay, intellectual disability, speech impairment, hypotonia, and distinctive craniofacial features. Pathogenic variants—including loss-of-function (frameshift, nonsense) and missense mutations clustered in conserved functional domains—lead to haploinsufficiency or impaired helicase and ATPase activity. This enzymatic dysfunction disrupts normal RNA metabolism and prevents efficient R-loop clearance, ultimately triggering genomic instability and altered transcriptional programs essential for neurodevelopment.

The disorder was first characterized in **2023**. 

**Citation:**
Yamada, M., et al. (2023). "De novo variants in *DHX9* cause a neurodevelopmental disorder with intellectual disability, developmental delay, and hypotonia." *The American Journal of Human Genetics*, 110(7), 1160–1174.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P01)

Based strictly on the provided sources, here is the clinical genetic evaluation:

### 1. Rule-in / Rule-out Status for Each Patient

The sources describe intellectual developmental disorder, autosomal dominant 75 (MRD75) only as an "intellectual developmental disorder" [1, 3, 4, 5], a "neurodevelopmental disorder" [2, 6], and "intellectual disability" [5] caused by heterozygous mutations in the *DHX9* gene [1, 2, 3, 4]. The sources provide **no specific phenotypic features, HPO terms, dysmorphic signs, or clinical diagnostic criteria**. Therefore:

* **P01**: **Cannot rule in or rule out.** The sources do not describe whether features such as cleft palate, abnormal cortical gyration, or ventricular septal defect occur in MRD75 [1–6].
* **P02**: **Cannot rule in or rule out.** The patient has developmental delay and intellectual disability, which are consistent with the broad definition [1, 2, 5], but the sources provide no specific phenotypic criteria to rule this patient in or out [1–6].
* **P03**: **Cannot rule in or rule out.** Broadly features intellectual disability and developmental delay [1, 2, 5], but specific features (e.g., joint hypermobility, ptosis, seizures) are neither confirmed nor excluded by the sources [1–6].
* **P04**: **Cannot rule in or rule out.** The patient displays severe developmental delay and intellectual disability [1, 2, 5], but the sources lack phenotypic details to evaluate the other findings [1–6].
* **P05**: **Cannot rule in or rule out.** Displays severe developmental delay and intellectual disability [1, 2, 5], but the sources do not mention neuroimaging (thin corpus callosum, cerebellar atrophy) or neurological signs [1–6].
* **P06**: **Cannot rule in or rule out.** Exhibits global developmental delay and motor delay [1, 2, 5, 6], but the sources provide no information regarding facial dysmorphisms or tics [1–6].
* **P07**: **Cannot rule in or rule out.** Exhibits intellectual disability [1, 5], but the sources do not provide information on associated behavioral or growth phenotypes [1–6].
* **P08**: **Cannot rule in or rule out.** Features global developmental delay [1, 2, 5, 6], but the sources do not provide details on brain morphology or craniofacial features [1–6].
* **P09**: **Cannot rule in or rule out.** Features severe intellectual disability and developmental delay [1, 2, 5], but specific findings (ataxia, microcephaly) are absent from the sources [1–6].
* **P10**: **Cannot rule in or rule out.** Features intellectual disability and developmental delay [1, 2, 5], but the specific syndrome-like features (happy demeanor, tongue thrusting, etc.) cannot be compared against the provided sources [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most likely patient:** None can be distinguished as more likely than the others based on the provided text. Selecting any single patient (e.g., **P02** or any other presenting with intellectual disability/neurodevelopmental delay) is clinically arbitrary based solely on these sources.
* **Probability:** **10% (1/10)**, representing an equiprobable prior distribution across the 10 candidates, as the sources lack any clinical or phenotypic details to differentiate between them [1–6].

---

### 3. Facts Needed (and Lacking in the Sources) to Be Confident

To establish a confident clinical or molecular diagnosis, the following information is required:
1. **Specific clinical phenotype / HPO profile:** A detailed clinical summary of MRD75 describing characteristic facial features, systemic involvement, behavioral manifestations, and neuroimaging findings associated with *DHX9* mutations.
2. **Genetic variant data:** Direct molecular evidence confirming a heterozygous pathogenic or likely pathogenic mutation in the *DHX9* gene (located on chromosome 1q25) for the individual [1, 2, 3, 4].
3. **Inheritance data:** Clarification of whether the variant/condition is confirmed to follow an autosomal dominant pattern or occurred *de novo* [1, 3, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: no clear pick)

Based strictly on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Rule-In / Rule-Out Assessment

The provided sources define Intellectual developmental disorder, autosomal dominant 75 (MRD75) exclusively as an autosomal dominant neurodevelopmental disorder / intellectual disability caused by heterozygous mutations in the *DHX9* gene on chromosome 1q25 [1, 2, 3, 4, 5, 6]. The sources provide **no specific phenotypic features, HPO terms, dysmorphic characteristics, or systemic findings** beyond the general diagnostic category of an intellectual/neurodevelopmental disorder [1, 2, 3, 4, 5, 6].

* **P01:** Cannot be ruled in or ruled out. The patient presents with global developmental delay and dysmorphic/cardiac features, but the sources do not provide the detailed phenotypic spectrum or exclusionary criteria for MRD75 [1–6].
* **P02:** Cannot be ruled in or ruled out. The patient has intellectual disability and developmental delays, consistent with a generic neurodevelopmental disorder [1, 2, 5], but the sources do not list specific signs to confirm or exclude this diagnosis [1–6].
* **P03:** Cannot be ruled in or ruled out. Has intellectual disability and global delay [1, 2, 5], but sources lack phenotypic details to evaluate specific features like seizures or facial traits [1–6].
* **P04:** Cannot be ruled in or ruled out. Has severe intellectual disability and developmental delay [1, 2, 5], but sources do not state whether microcephaly, paraplegia, or other listed signs occur in MRD75 [1–6].
* **P05:** Cannot be ruled in or ruled out. Shows severe intellectual disability and neurodevelopmental delay [1, 2, 5], but the sources provide no data on brain MRI abnormalities (e.g., thin corpus callosum, cerebellar atrophy) or spasticity for MRD75 [1–6].
* **P06:** Cannot be ruled in or ruled out. Displays global developmental delay and motor/speech delays [1, 2], but no specific clinical profile is provided in the sources to evaluate these findings [1–6].
* **P07:** Cannot be ruled in or ruled out. Features intellectual disability and behavioral issues [1, 2, 5], but sources provide no detailed behavioral or growth profiles for MRD75 [1–6].
* **P08:** Cannot be ruled in or ruled out. Presents with developmental delays [1, 2], but the sources lack phenotypic descriptions to confirm or refute the diagnosis [1–6].
* **P09:** Cannot be ruled in or ruled out. Has severe intellectual disability and developmental delay [1, 2, 5], but the sources do not specify whether ataxia, microcephaly, or specific facial shapes are associated with *DHX9* [1–6].
* **P10:** Cannot be ruled in or ruled out. Shows intellectual disability and developmental delays [1, 2, 5], but sources do not mention whether characteristic facial, behavioral, or neurological findings of this patient correspond to MRD75 [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** None can be distinguished as more likely than the others based on the provided sources. Because all 10 patients exhibit features of a neurodevelopmental disorder or developmental delay, and the sources provide no specific differentiating phenotypic criteria [1–6], any patient has an equal baseline probability. If one patient must be chosen at random, the assigned probability is **1/10 (10% or 0.10)**.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a confident clinical or molecular diagnosis, the following information—absent from sources [1–6]—is required:
1. **Molecular genetic data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in *DHX9* on chromosome 1q25 for the patient [1, 3, 4].
2. **Clinical phenotypic spectrum:** The detailed clinical synopsis and frequency of HPO terms associated with MRD75 (e.g., specific craniofacial dysmorphisms, brain MRI abnormalities, growth parameters, and behavioral phenotypes).
3. **Exclusionary/differential criteria:** Information on which features (e.g., congenital heart disease, cleft palate, specific seizures, neuroimaging findings) are characteristic of, or inconsistent with, *DHX9*-related neurodevelopmental disorder.

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based solely on the provided sources, here is the clinical genetic assessment:

### 1. Rule In / Rule Out Status for Each Patient

The sources define intellectual developmental disorder, autosomal dominant 75 (MRD75) only as an autosomal dominant intellectual/neurodevelopmental disorder caused by heterozygous mutations in the *DHX9* gene [1, 2, 3, 4, 5, 6]. Because the sources provide **no specific phenotypic features, HPO terms, dysmorphic signs, or clinical diagnostic criteria**, the sources do not contain enough information to definitively rule in or rule out any individual patient:

* **P01**: **Cannot be ruled in or ruled out.** The patient has global developmental delay, which is consistent with a neurodevelopmental disorder [2, 6], but the sources provide no specific features to confirm or exclude MRD75 [1–6].
* **P02**: **Cannot be ruled in or ruled out.** The patient has moderate intellectual disability and global developmental delay, consistent with the broad definition [1, 2, 5], but the sources provide no phenotypic details to evaluate the remaining features [1–6].
* **P03**: **Cannot be ruled in or ruled out.** The patient presents with intellectual disability and global developmental delay [1, 2, 5], but no source details whether features like seizures, joint hypermobility, or ptosis are part of MRD75 [1–6].
* **P04**: **Cannot be ruled in or ruled out.** Severe intellectual disability and global developmental delay fit the general category of intellectual developmental disorder [1, 5], but the sources lack phenotypic descriptions to confirm or refute this presentation [1–6].
* **P05**: **Cannot be ruled in or ruled out.** Severe intellectual disability is present [1, 5], but the sources do not provide information regarding cerebellar atrophy, spasticity, or other neurological findings in MRD75 [1–6].
* **P06**: **Cannot be ruled in or ruled out.** The patient has global developmental delay [2, 6], but the sources contain no specific clinical information to rule the patient in or out [1–6].
* **P07**: **Cannot be ruled in or ruled out.** The presence of intellectual disability fits the broad classification [1, 5], but the sources provide no data regarding microcephaly or behavioral features [1–6].
* **P08**: **Cannot be ruled in or ruled out.** The patient has global developmental delay [2, 6], but the sources provide no information regarding thin corpus callosum or other signs [1–6].
* **P09**: **Cannot be ruled in or ruled out.** Severe intellectual disability and global developmental delay are consistent with the broad disorder name [1, 5], but the sources provide no phenotypic criteria to rule the patient in or out [1–6].
* **P10**: **Cannot be ruled in or ruled out.** Intellectual disability and global developmental delay are present [1, 5], but the sources provide no specific clinical criteria to evaluate this complex profile [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient**: **None can be distinguished from the others** based on the sources alone. Because every patient exhibits an intellectual developmental disorder or developmental delay (consistent with the general definitions in [1, 2, 5, 6]), and the sources provide zero distinguishing clinical features, any patient (e.g., **P01**, or any arbitrarily selected patient from P01–P10) is equally likely.
* **Probability**: **10% (0.10 or 1 in 10)**, representing an equal prior probability among the 10 candidates in the absence of any discriminating source data.

---

### 3. Facts Needed to Be Confident (Not Provided in the Sources)

1. **Detailed Clinical Phenotype / HPO Profile**: The sources do not describe the specific clinical, facial, neurological, or behavioral features associated with MRD75 [1–6]. A published phenotypic profile (including frequencies of dysmorphic signs, brain MRI findings, and tone abnormalities) is required to clinically match the patients.
2. **Genetic Testing Data**: The sources state that MRD75 is caused by a heterozygous mutation in the *DHX9* gene on chromosome 1q25 [1, 2, 3, 4]. Molecular sequencing data confirming or excluding a pathogenic *DHX9* variant in each patient is absent.
3. **Inheritance and Segregation Data**: The sources specify that MRD75 is autosomal dominant [1, 2, 3, 4, 6]; family history or evidence of a *de novo* mutation is not provided for any patient.

--------------------------------------------------------------------------------

picks across rounds: ['P01', None, 'P01']
