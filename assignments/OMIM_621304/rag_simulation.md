# Plain RAG on Developmental and epileptic encephalopathy 119 (RNU2-2, OMIM:621304)
model: gemini-3.8-flash   generated: 2026-09-28 20:52

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `RNU2-2 gene Developmental and epileptic encephalopathy 119`

[1] **Entry - #621304 - DEVELOPMENTAL AND EPILEPTIC ...**  
    https://omim.org/entry/621304  
    Developmental and epileptic encephalopathy-119 (DEE119) is characterized by global developmental delay, impaired intellectual development, ...

[2] **pathogenic variants in rnu2-2, encoding a spliceosomal rna ...**  
    https://aesnet.org/abstractslisting/pathogenic-variants-in-rnu2-2-encoding-a-spliceosomal-rna-subunit-cause-an-infantile-onset-developmental-and-epileptic-encephalopathy  
    RNU2-2 causes a distinctive severe DEE, with high rates of status epilepticus, hemiclonic seizures, multiple seizure types, hippocampal ...

[3] **Phenotypic and transcriptomic characterisation of a novel ...**  
    https://www.medrxiv.org/content/10.64898/2026.02.19.26345867v1.full-text  
    Biallelic variants in RNU2-2 cause a remarkably frequent developmental epileptic encephalopathy. Genetic and Genomic Medicine. Preprint ...

[4] **developmental and epileptic encephalopathy 119**  
    https://search.clinicalgenome.org/kb/conditions/MONDO:1060177/by-gene  
    RNU2-2 - developmental and epileptic encephalopathy 119 ; Clinicalvalidity on Gene-Disease Validity. Autosomal Dominant, Syndromic Disorders GCEP ; Lumping & ...

[5] **RNU2-2P**  
    https://panelapp.genomicsengland.co.uk/panels/entities/RNU2-2P  
    RNU2-2-related neurodevelopmental disorder with seizures and hyperventilation ... Developmental and epileptic encephalopathy 119, OMIM:621304. Tags. new-gene ...

[6] **Systematic analysis of snRNA genes reveals frequent ...**  
    https://www.nature.com/articles/s41588-026-02547-5  
    by E Leitão · 2026 · Cited by 18 — Systematic analysis of snRNA genes reveals frequent RNU2-2 variants in dominant and recessive developmental and epileptic encephalopathies.

## 2. The context handed to the model
```
[1] Entry - #621304 - DEVELOPMENTAL AND EPILEPTIC ...
https://omim.org/entry/621304
Developmental and epileptic encephalopathy-119 (DEE119) is characterized by global developmental delay, impaired intellectual development, ...

[2] pathogenic variants in rnu2-2, encoding a spliceosomal rna ...
https://aesnet.org/abstractslisting/pathogenic-variants-in-rnu2-2-encoding-a-spliceosomal-rna-subunit-cause-an-infantile-onset-developmental-and-epileptic-encephalopathy
RNU2-2 causes a distinctive severe DEE, with high rates of status epilepticus, hemiclonic seizures, multiple seizure types, hippocampal ...

[3] Phenotypic and transcriptomic characterisation of a novel ...
https://www.medrxiv.org/content/10.64898/2026.02.19.26345867v1.full-text
Biallelic variants in RNU2-2 cause a remarkably frequent developmental epileptic encephalopathy. Genetic and Genomic Medicine. Preprint ...

[4] developmental and epileptic encephalopathy 119
https://search.clinicalgenome.org/kb/conditions/MONDO:1060177/by-gene
RNU2-2 - developmental and epileptic encephalopathy 119 ; Clinicalvalidity on Gene-Disease Validity. Autosomal Dominant, Syndromic Disorders GCEP ; Lumping & ...

[5] RNU2-2P
https://panelapp.genomicsengland.co.uk/panels/entities/RNU2-2P
RNU2-2-related neurodevelopmental disorder with seizures and hyperventilation ... Developmental and epileptic encephalopathy 119, OMIM:621304. Tags. new-gene ...

[6] Systematic analysis of snRNA genes reveals frequent ...
https://www.nature.com/articles/s41588-026-02547-5
by E Leitão · 2026 · Cited by 18 — Systematic analysis of snRNA genes reveals frequent RNU2-2 variants in dominant and recessive developmental and epileptic encephalopathies.
```

## 3. The gene, from the sources

The *RNU2-2* gene is an snRNA gene whose product is a spliceosomal RNA subunit [2, 6]. Beyond its identity as a component of the spliceosome, its precise cellular functions and mechanisms are not covered in the provided texts [2]. 

Pathogenic variants in *RNU2-2* can occur as autosomal dominant, dominant, or biallelic/recessive alterations that cause developmental and epileptic encephalopathy 119 (DEE119) [3, 4, 6]. While the exact molecular mechanism of how these variants cause disease is not covered, they result in a distinctive, severe infantile-onset encephalopathy [2]. 

Clinically, DEE119 is characterized by global developmental delay and impaired intellectual development [1]. Affected individuals with *RNU2-2* pathogenic variants experience multiple seizure types, hemiclonic seizures, and high rates of status epilepticus [2]. Furthermore, the disorder has been classified as an *RNU2-2*-related neurodevelopmental disorder associated with both seizures and hyperventilation [5].

*tokens in 608, out 1853*

## 4. The gene, closed book (no sources; beware hallucinations)

The ***RNU2-2*** gene (also annotated as *RNU2-2P*) encodes **U2 small nuclear RNA (snRNA)**, a non-coding RNA that forms a catalytic core of the major spliceosome. During pre-mRNA splicing, U2 snRNA base-pairs with the intron’s branch point sequence (BPS), properly orienting the branch site adenosine for the first transesterification reaction. 

Developmental and epileptic encephalopathy 119 (DEE119; OMIM #620859) is caused by heterozygous *de novo* variants within critical functional regions of the U2 snRNA—particularly the branch-site recognition domain and key structural stem-loops. These alterations impair spliceosome assembly and splice-site fidelity, driving widespread transcriptome mis-splicing (such as aberrant exon skipping and intron retention) that disrupts early neurodevelopment and triggers severe early-onset seizures.

The disorder was first described in **2024**. 

**Citation:**  
Reuter, M. S., et al. (2024). *De novo* variants in the non-coding small nuclear RNA gene *RNU2-2P* cause a severe neurodevelopmental and epileptic encephalopathy. *American Journal of Human Genetics* / OMIM #620859.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P06)

Based strictly on the provided sources, here is the clinical genetic assessment:

---

### 1. Patient Evaluation (Ruling In or Ruling Out)

The provided sources define Developmental and epileptic encephalopathy 119 (DEE119; *RNU2-2*) as a severe developmental and epileptic encephalopathy characterized by global developmental delay, impaired intellectual development [1], and seizures (notably high rates of status epilepticus, hemiclonic seizures, and multiple seizure types [2], as well as seizures with hyperventilation [5]). The sources do **not** provide complete clinical synopses, negative exclusion criteria, or comprehensive lists of craniofacial, systemic, or neuroimaging features [1–6]. Consequently:

* **P01:** **Cannot be ruled in or ruled out.** The patient has global developmental delay and delayed walking/speech [1], but lacks seizures, status epilepticus, or epileptic encephalopathy [1, 2, 5]. While the lack of seizures makes DEE119 clinically improbable, the sources do not provide explicit penetrance data or negative exclusion criteria to rule P01 out definitively [1–6].
* **P02:** **Cannot be ruled in or ruled out.** Displays global developmental delay and severe intellectual disability [1], but no seizures are reported [2, 5]. The sources do not state whether non-epileptic neurodevelopmental phenotypes occur in DEE119 [1–6].
* **P03:** **Cannot be ruled in or ruled out.** Presents with global developmental delay and intellectual disability [1], but lacks reported seizures [2, 5]. The sources do not describe low-set ears, micrognathia, or feeding difficulties [1–6].
* **P04:** **Cannot be ruled in or ruled out.** Has severe global developmental delay, severe intellectual disability, and seizures [1, 2, 5]. However, the sources do not mention the specific systemic/neurological features present here (e.g., drooling, synophrys, paraplegia, oligohydramnios) [1–6].
* **P05:** **Cannot be ruled in or ruled out.** Demonstrates severe/profound global developmental delay, intellectual disability, seizures, and interictal epileptiform activity [1, 2, 5]. However, the sources do not document pontine hypoplasia, vermis hypoplasia, amyotrophy, or lower limb spasticity [1–6].
* **P06:** **Cannot be ruled in or ruled out.** Has global developmental delay [1] and presents with **multiple seizure types** (bilateral tonic-clonic, generalized absence, and myoclonic seizures), which matches the description in [2]. However, P06 has mild intellectual disability, whereas the sources note a "severe DEE" [2], and the excerpt provides insufficient phenotypic data to definitively rule P06 in or out [1–6].
* **P07:** **Cannot be ruled in or ruled out.** Presents with intellectual disability, global developmental delay, seizures, and EEG abnormalities [1, 2, 5]. However, major brain malformations (polymicrogyria, schizencephaly) and dysmorphic features are neither confirmed nor excluded by the sources [1–6].
* **P08:** **Cannot be ruled in or ruled out.** Displays global developmental delay [1], but no seizures or epileptic features are reported [2, 5].
* **P09:** **Cannot be ruled in or ruled out.** Has global developmental delay and severe intellectual disability [1], but has no reported seizures or epilepsy [2, 5].
* **P10:** **Cannot be ruled in or ruled out.** Exhibits severe global developmental delay, severe intellectual disability, seizures, and interictal EEG abnormalities [1, 2, 5]. The sources mention seizures and hyperventilation [5] (which may align with cyanotic episodes), but the sources do not provide facial or specific systemic criteria to rule P10 in definitively [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P06** (with **P10** as a close alternative).
  * **Rationale:** Source [2] specifically notes that *RNU2-2* causes a distinctive severe DEE featuring **"multiple seizure types"** [2]. P06 is the only patient explicitly documented with three distinct seizure semiologies (bilateral tonic-clonic, generalized absence, and myoclonic seizures). (If severity of intellectual disability is prioritized over explicit seizure semiology, P10 is also plausible due to severe global delay, tonic seizures, and interictal EEG abnormalities [1, 2, 5]).
* **Estimated Probability:** **~35%**.
  * The probability remains low to modest because 5 of the 10 patients (P04, P05, P06, P07, P10) have developmental delay and seizures [1, 2, 5], and the provided excerpts are far too brief to cleanly differentiate among them.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a definitive diagnosis, the following information missing from sources [1–6] is required:
1. **Detailed Seizure Semiology & EEG Patterns:** Full documentation of status epilepticus, hemiclonic seizures, infantile spasms, or specific interictal/ictal EEG signatures described for *RNU2-2* [2].
2. **Penetrance & Natural History:** Confirmation of whether seizures are 100% penetrant (to definitively exclude P01, P02, P03, P08, and P09).
3. **Neuroimaging Phenotype:** Complete description of the MRI findings (source [2] truncates at `"hippocampal ..."` without specifying sclerosis, atrophy, or malformation, and does not state whether callosal thinning, cerebellar hypoplasia, or cortical malformations like polymicrogyria occur).
4. **Dysmorphic and Extraneurological Features:** Clarification of characteristic facial dysmorphisms, musculoskeletal anomalies, or organ involvement.
5. **Respiratory Manifestations:** Specific diagnostic criteria regarding the `"hyperventilation"` mentioned in [5] (e.g., episodic central hyperventilation, apnea, or associated cyanosis).
6. **Genetic Variant Data:** Identification of the specific pathogenic variant(s) in *RNU2-2* and the mode of inheritance (autosomal dominant vs. biallelic/recessive) [3, 4, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P06)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources do **not** provide sufficient phenotypic detail, penetrance data, or negative/exclusionary criteria to definitively rule in or rule out any individual patient [1–6]. Specifically:

* **P01:** **Cannot be ruled in or ruled out.** While P01 has delayed development [1], no seizures or epileptic features are listed [1, 2, 5]. However, the sources do not state whether seizures are 100% penetrant or provide exclusionary criteria [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits global developmental delay and severe intellectual disability [1], but lacks seizures [1, 2, 5]. The sources do not provide negative diagnostic criteria to formally rule P02 out [1–6].
* **P03:** **Cannot be ruled in or ruled out.** P03 exhibits global developmental delay and intellectual disability [1], but has no reported seizures [1, 2, 5]. The sources do not specify whether the absence of seizures excludes DEE119 [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has severe global developmental delay, severe intellectual disability, and seizures [1, 2, 5], but the sources do not provide detailed dysmorphic or non-neurological features to confirm or exclude DEE119 [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has severe/profound intellectual disability, global developmental delay, seizures, and interictal epileptiform activity [1, 2, 5]. However, the truncated sources do not detail specific brainstem/cerebellar abnormalities to definitively rule P05 in or out [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 exhibits global developmental delay, intellectual disability [1], and three distinct seizure types matching the description of "multiple seizure types" [2]. However, P06 has "mild" intellectual disability, which may contrast with "severe DEE" [2], and the sources provide insufficient clinical criteria to confirm or exclude [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 has global developmental delay, intellectual disability, focal seizures, and EEG abnormalities [1, 2, 5]. However, the sources do not report whether structural malformations (e.g., polymicrogyria, schizencephaly) occur in DEE119 [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has global developmental delay [1], but no seizures are noted [1, 2, 5]; the sources do not provide exclusionary rules [1–6].
* **P09:** **Cannot be ruled in or ruled out.** P09 has global developmental delay and severe intellectual disability [1], but lacks seizures [1, 2, 5]; the sources do not define mandatory diagnostic criteria [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 presents with severe global developmental delay, severe intellectual disability, tonic seizures, and interictal EEG abnormalities [1, 2, 5]. However, the sources do not provide sufficient dysmorphic or systemic features to definitively confirm or rule out the diagnosis [1–6].

---

### 2. Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P06** (with **P05** and **P10** as close alternatives).
  * *Rationale:* Source [2] specifically notes that *RNU2-2* causes a distinctive severe DEE with "multiple seizure types" alongside developmental delay and intellectual impairment [1, 2]. P06 is the only patient explicitly documented with three distinct seizure categories (bilateral tonic-clonic, generalized non-motor absence, and myoclonic seizures) [2]. 
* **Estimated Probability:** **~30%**
  * *Reasoning:* Because five patients (P04, P05, P06, P07, P10) have epileptic encephalopathy/seizure phenotypes consistent with the minimal details in [1, 2, 5], and the sources do not provide enough granular phenotypic data to distinguish among them, confidence remains low.

---

### 3. Missing Information Needed for Diagnostic Confidence

To establish a definitive diagnosis, the following information—absent from the provided sources—would be required:
1. **Unabbreviated clinical descriptions:** The full phenotypic spectrum from OMIM #621304 (cut off in [1]) and the complete abstract text (cut off at "hippocampal ..." in [2]).
2. **Detailed neuroimaging and EEG data:** Specific MRI features (e.g., hippocampal, brainstem, or cortical malformations) and electroclinical patterns characteristic of *RNU2-2* variants [2].
3. **Clinical inclusion/exclusion criteria:** Known penetrance of seizures, degree of intellectual disability, presence of hyperventilation [5], and whether dysmorphic/organ features are part of DEE119.
4. **Molecular genetics:** Direct sequencing data identifying heterozygous or biallelic pathogenic variants in *RNU2-2* [2, 3, 4, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P06)

Based strictly on the provided sources, here is the clinical genetic assessment:

---

### 1. Patient-by-Patient Rule In / Rule Out Assessment

* **P01:** **Cannot definitively rule in or rule out.** The sources define DEE119 as a developmental and epileptic encephalopathy [1, 3, 4, 6] associated with seizures [2, 5]. P01 has developmental delay [1], but completely lacks seizures or interictal epileptiform activity. However, the sources do not provide non-epileptic phenotypic spectrum data or explicit exclusion criteria to rule P01 out definitively.
* **P02:** **Cannot definitively rule in or rule out.** P02 exhibits global developmental delay and severe intellectual disability [1], but lacks any documented seizures or EEG abnormalities, which are core features of DEE119 [1, 2, 5]. The sources do not state whether epilepsy has 100% penetrance, so definitive exclusion is not possible.
* **P03:** **Cannot definitively rule in or rule out.** P03 has global developmental delay and intellectual disability [1], but no seizures are listed. The sources do not describe dysmorphic features (e.g., micrognathia, low-set ears) or provide exclusion criteria to rule P03 out definitively.
* **P04:** **Cannot definitively rule in or rule out.** P04 has severe global developmental delay, severe intellectual disability [1], and seizures [2, 5]. However, the sources do not contain facial, limb, or systemic phenotypic data (e.g., paraplegia, oligohydramnios) to rule P04 in or out.
* **P05:** **Cannot definitively rule in or rule out.** P05 has global developmental delay, profound intellectual disability, seizures, and interictal epileptiform activity, which are consistent with severe DEE [1, 2]. However, the sources do not detail the neuroimaging spectrum (e.g., pontine or cerebellar vermis hypoplasia; source [2] cuts off at "hippocampal...") or neuromuscular features to confirm or refute this patient.
* **P06:** **Cannot definitively rule in or rule out.** P06 has global developmental delay, intellectual disability [1], and specifically exhibits "multiple seizure types" (bilateral tonic-clonic, absence, myoclonic), matching the clinical description in [2]. However, P06 has *mild* intellectual disability, whereas source [2] describes a "distinctive severe DEE." Because the full phenotypic spectrum is truncated in [1, 2], the sources do not permit definitive rule-in or rule-out.
* **P07:** **Cannot definitively rule in or rule out.** P07 has intellectual disability, global developmental delay, seizures, and EEG abnormalities [1, 2]. However, the sources make no mention of structural malformations of cortical development (polymicrogyria, schizencephaly) or non-neurological features, so P07 cannot be definitively ruled in or out.
* **P08:** **Cannot definitively rule in or rule out.** P08 has global developmental delay [1], but lacks seizures [1, 2, 5]. The sources do not provide exclusion criteria or full clinical descriptions to definitively rule P08 out.
* **P09:** **Cannot definitively rule in or rule out.** P09 has global developmental delay and severe intellectual disability [1], but lacks seizures [1, 2, 5]. The sources do not provide full dysmorphic or neuroimaging criteria to definitively rule P09 out.
* **P10:** **Cannot definitively rule in or rule out.** P10 displays severe global developmental delay, severe intellectual disability, tonic seizures, and interictal EEG abnormalities, consistent with a severe DEE [1, 2]. However, the sources provide no information regarding facial dysmorphisms, hirsutism, or arachnodactyly to definitively rule P10 in or out.

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P06**
* **Estimated Probability:** **35%** (Low–Moderate confidence)

**Rationale:**
* Source [2] specifically highlights that *RNU2-2* causes an encephalopathy with **"multiple seizure types"** in addition to global developmental delay and intellectual impairment [1]. P06 is the only patient in the cohort with multiple distinct seizure types explicitly cataloged (bilateral tonic-clonic, absence, and myoclonic seizures).
* However, source [2] notes a "severe DEE," whereas P06 has mild intellectual disability; alternatively, P10, P05, and P04 present with severe-to-profound impairment and seizures but lack documentation of multiple seizure types. Given the truncated and minimal text in the sources, certainty is necessarily low.

---

### 3. Missing Facts Needed to Be Confident

To establish a definitive diagnosis, the following information is required that the sources do not provide:
1. **Full OMIM Clinical Synopsis:** Source [1] truncates after "impaired intellectual development, ..." leaving out all associated cranial, facial, skeletal, and neurological criteria.
2. **Complete AESNet Abstract Data:** Source [2] truncates at "hippocampal ...", omitting the remainder of the neuroimaging, electroclinical, and phenotypic findings.
3. **Dysmorphic and Structural Spectrum:** The sources provide no information on whether *RNU2-2* variants cause dysmorphic facial features, brain malformations (such as schizencephaly or pontine hypoplasia), or systemic abnormalities.
4. **Clinical Penetrance / Seizure Spectrum:** The sources do not state whether seizures are 100% penetrant, whether mild intellectual disability is compatible with DEE119, or which specific seizure types predominate beyond the brief mention of hemiclonic and status epilepticus [2].
5. **Molecular and Genetic Data:** The provided sources do not include patient-level sequencing data to confirm a pathogenic variant in *RNU2-2*.

--------------------------------------------------------------------------------

picks across rounds: ['P06', 'P06', 'P06']
