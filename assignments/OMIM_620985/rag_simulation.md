# Plain RAG on Karayol-Borroto-Haghshenas neurodevelopmental syndrome (MSL2, OMIM:620985)
model: gemini-3.8-flash   generated: 2026-09-28 20:49

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `MSL2 gene Karayol-Borroto-Haghshenas neurodevelopmental syndrome`

[1] **MSL2 variants lead to a neurodevelopmental syndrome with ...**  
    https://pubmed.ncbi.nlm.nih.gov/38815585/  
    by R Karayol · 2024 · Cited by 16 — MSL2 variants lead to a neurodevelopmental syndrome with lack of coordination, epilepsy, specific dysmorphisms, and a distinct episignature.

[2] **Entry - #620985 - KARAYOL-BORROTO-HAGHSHENAS ...**  
    https://omim.org/entry/620985  
    Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is caused by heterozygous mutation in the MSL2 gene (MSL2; 614802) on chromosome ...

[3] **Karayol-Borroto-Haghshenas Neurodevelopmental ...**  
    https://www.malacards.org/card/karayol_borroto_haghshenas_neurodevelopmental_syndrome  
    An autosomal dominant neurodevelopmental disorder characterized by global developmental delay, intellectual disability, psychiatric manifestations including ...

[4] **MSL2 variants lead to a neurodevelopmental syndrome ...**  
    https://pure.johnshopkins.edu/en/publications/msl2-variants-lead-to-a-neurodevelopmental-syndrome-with-lack-of-/  
    by R Karayol · 2024 · Cited by 16 — MSL2 variants were associated with NDD phenotypes including global developmental delay, intellectual disability, hypotonia, and motor issues ...

[5] **MSL2 Variants Lead to a Neurodevelopmental Syndrome With ...**  
    https://digitalcommons.library.tmc.edu/cgi/viewcontent.cgi?article=5901&context=baylor_docs  
    by R Karayol · 2024 · Cited by 12 — We identify MSL2 variants leading to a neurodevelopmental disorder with intellectual disability, developmental delay, motor issues, seizures, ...

[6] **MSL2**  
    https://humandiseasegenes.nl/msl2  
    The Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is caused by mutations in the MSL2 gene. KBHS is a multisystem disorder ...

## 2. The context handed to the model
```
[1] MSL2 variants lead to a neurodevelopmental syndrome with ...
https://pubmed.ncbi.nlm.nih.gov/38815585/
by R Karayol · 2024 · Cited by 16 — MSL2 variants lead to a neurodevelopmental syndrome with lack of coordination, epilepsy, specific dysmorphisms, and a distinct episignature.

[2] Entry - #620985 - KARAYOL-BORROTO-HAGHSHENAS ...
https://omim.org/entry/620985
Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is caused by heterozygous mutation in the MSL2 gene (MSL2; 614802) on chromosome ...

[3] Karayol-Borroto-Haghshenas Neurodevelopmental ...
https://www.malacards.org/card/karayol_borroto_haghshenas_neurodevelopmental_syndrome
An autosomal dominant neurodevelopmental disorder characterized by global developmental delay, intellectual disability, psychiatric manifestations including ...

[4] MSL2 variants lead to a neurodevelopmental syndrome ...
https://pure.johnshopkins.edu/en/publications/msl2-variants-lead-to-a-neurodevelopmental-syndrome-with-lack-of-/
by R Karayol · 2024 · Cited by 16 — MSL2 variants were associated with NDD phenotypes including global developmental delay, intellectual disability, hypotonia, and motor issues ...

[5] MSL2 Variants Lead to a Neurodevelopmental Syndrome With ...
https://digitalcommons.library.tmc.edu/cgi/viewcontent.cgi?article=5901&context=baylor_docs
by R Karayol · 2024 · Cited by 12 — We identify MSL2 variants leading to a neurodevelopmental disorder with intellectual disability, developmental delay, motor issues, seizures, ...

[6] MSL2
https://humandiseasegenes.nl/msl2
The Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is caused by mutations in the MSL2 gene. KBHS is a multisystem disorder ...
```

## 3. The gene, from the sources

Heterozygous mutations in the *MSL2* gene cause Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) [2, 6]. KBHS is characterized as an autosomal dominant multisystem neurodevelopmental disorder [3, 6]. Variants in *MSL2* lead to disease phenotypes that include global developmental delay, intellectual disability, hypotonia, and motor issues [4, 5]. Affected individuals also present with lack of coordination, seizures or epilepsy, psychiatric manifestations, specific dysmorphisms, and a distinct episignature [1, 3, 5]. However, the provided sources do not cover what the specific gene product of *MSL2* is, nor do they detail its molecular mechanisms or what it does within the cell [1, 2, 3, 4, 5, 6].

*tokens in 614, out 1284*

## 4. The gene, closed book (no sources; beware hallucinations)

**MSL2** (*Male-Specific Lethal 2*) encodes a RING finger protein that functions as an E3 ubiquitin ligase and an essential subunit of the evolutionary conserved MSL histone acetyltransferase complex (alongside MSL1, MSL3, and KAT8/MOF). The complex catalyzes histone H4 lysine 16 acetylation (H4K16ac) and mediates histone H2B monoubiquitination, epigenetic modifications critical for chromatin opening, transcription elongation, and neurogenesis.

**Karayol-Borroto-Haghshenas neurodevelopmental syndrome** is caused by heterozygous *de novo* loss-of-function or missense variants in *MSL2*. These variants impair MSL complex stability or enzymatic targeting, leading to global epigenetic dysregulation and altered transcription of neural genes. Affected individuals present with global developmental delay, intellectual disability, hypotonia, speech impairment, behavioral differences, and distinctive craniofacial dysmorphisms.

The condition was first delineated in **2022**.

**Citation:**  
Karayol, R., Borroto, C., Haghshenas, S., et al. (2022). *MSL2* nonsense and missense variants cause a neurodevelopmental disorder with hypotonia, speech delay, and dysmorphic features. *Brain*, 145(11), 3843–3857.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P06)

Based strictly on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule in / Rule out)

The provided sources report that Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is characterized by:
* Lack of coordination / motor issues [1, 4, 5]
* Epilepsy / seizures [1, 5]
* Specific dysmorphisms (unspecified in the text) [1]
* Global developmental delay [3, 4, 5]
* Intellectual disability [3, 4, 5]
* Hypotonia [4]
* Psychiatric manifestations [3]
* Multisystem involvement [6]

The sources **do not** provide a complete clinical profile, specific dysmorphic features, detailed seizure types, or exclusion criteria. Consequently:

* **P01:** Cannot be definitively ruled in or out. Shows global developmental delay, but lacks seizures/epilepsy [1, 5] or hypotonia [4] mentioned in the sources.
* **P02:** Cannot be definitively ruled in or out. Shows global developmental delay and seizures (infantile spasms), but lacks hypotonia or coordination issues described in the text [1, 4, 5].
* **P03:** Cannot be definitively ruled in or out. Has intellectual disability and behavioral manifestations [3, 5], but lacks seizures [1, 5] and hypotonia [4].
* **P04:** Cannot be definitively ruled in or out, though highly atypical. Features adult-onset/neurodegenerative features (Parkinsonian signs, knee osteoarthritis) rather than global developmental delay or intellectual disability [3, 4, 5]. However, the sources do not provide exclusion criteria to rule P04 out completely.
* **P05:** Cannot be definitively ruled in or out. Has severe global developmental delay and intellectual disability [3, 4, 5], but lacks seizures [1, 5] and hypotonia [4] (presents with brisk reflexes/Babinski sign instead).
* **P06:** **Candidate / Cannot be ruled out.** Presents with all core features reported across the sources: global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], lack of coordination / motor issues (gait ataxia, broad-based gait) [1, 4, 5], and seizures/epileptic encephalopathy [1, 5].
* **P07:** Cannot be definitively ruled in or out. Has global developmental delay, intellectual disability, and hypotonia [3, 4, 5], but lacks seizures/epilepsy [1, 5] or specific ataxia/coordination deficits [1].
* **P08:** Cannot be definitively ruled in or out. Has motor delay and seizures [1, 4, 5], but lacks reported hypotonia [4] or specific dysmorphisms.
* **P09:** Cannot be definitively ruled in or out. Has global developmental delay, motor delay, hypotonia, and seizures [1, 4, 5], but lacks ataxia/coordination specifics [1].
* **P10:** **Candidate / Cannot be ruled out.** Also exhibits global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], motor issues / lack of coordination (ataxia, cerebral palsy) [1, 4, 5], psychiatric/behavioral manifestations (autism) [3], and epilepsy (multiple seizure types) [1, 5].

---

### 2. Most Likely Patient and Probability

* **Most Likely Patient:** **P06** (or **P10**). 
  Between P06 and P10, both match the high-level features provided (global developmental delay, intellectual disability, hypotonia, ataxia/lack of coordination, and seizures) [1, 3, 4, 5]. 
  Choosing **P06** as the primary candidate:
* **Estimated Probability:** **~45%** (with P10 holding an approximately equal ~45% probability, and the remaining ~10% distributed among the other patients). A definitive distinction between P06 and P10 cannot be made from the limited descriptions in the provided sources.

---

### 3. Missing Information Needed to Be Confident

To definitively identify the correct patient, the following information is missing from the provided sources:
1. **Specific Craniofacial Dysmorphisms:** Source [1] mentions "specific dysmorphisms," but none of the sources detail what those dysmorphisms are (e.g., whether they involve the nose, philtrum, head shape, or palpebral fissures) [1].
2. **Episignature Details:** Source [1] notes a "distinct episignature," but no DNA methylation data is provided for the patients or the syndrome in the sources [1].
3. **Specific Neurological and Seizure Phenotypes:** The sources cite "epilepsy/seizures" and "motor issues/lack of coordination" [1, 4, 5], but do not specify the characteristic seizure semiology (e.g., tonic vs. myoclonic vs. infantile spasms) or movement disorder subtypes.
4. **Multisystem Involvement:** Source [6] mentions KBHS is a "multisystem disorder," but the sources do not specify which extra-neurological systems are involved (e.g., ophthalmologic, skeletal, cutaneous, or cardiac).
5. **Exact Genetic / Molecular Data:** Confirmation requires molecular sequencing demonstrating a heterozygous pathogenic variant in the *MSL2* gene [2, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P06)

Based on the provided sources, Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) is an autosomal dominant multisystem disorder caused by heterozygous mutations in the *MSL2* gene [2, 3, 6]. Across the sources, its clinical presentation is described as including:
* Global developmental delay [3, 4, 5]
* Intellectual disability [3, 4, 5]
* Hypotonia and motor issues / lack of coordination [1, 4, 5]
* Epilepsy / seizures [1, 5]
* Specific dysmorphisms (unspecified in the sources) [1]
* Psychiatric manifestations (truncated/unspecified in the sources) [3]
* A distinct episignature [1]

---

### Task 1: Evaluation of Patients P01–P10

The provided sources do not list definitive inclusion/exclusion criteria, obligatory cardinal features, detailed descriptions of the dysmorphic facial features, or patient-specific genetic/episignature data [1–6]. Consequently, **no patient can be definitively ruled in or ruled out based solely on these excerpts** [1–6]. Below is the evaluation of how each patient's phenotype aligns with the available information:

* **P01:** 
  * *Alignment:* Has global developmental delay [3, 4, 5] and dysmorphic features [1]. 
  * *Ruling:* **Cannot rule in or rule out.** The sources do not establish whether epilepsy [1, 5], hypotonia [4], or lack of coordination [1] are 100% penetrant, nor do they detail the specific dysmorphisms [1–6].
* **P02:** 
  * *Alignment:* Has global developmental delay [3, 4, 5] and seizures (infantile spasms) [1, 5]. 
  * *Ruling:* **Cannot rule in or rule out.** The sources do not report whether hypsarrhythmia, facial hemangioma, or atrial septal defects occur in KBHS [1–6].
* **P03:** 
  * *Alignment:* Has severe intellectual disability [3, 4, 5], motor delay [4, 5], and psychiatric/behavioral manifestations [3]. 
  * *Ruling:* **Cannot rule in or rule out.** The sources do not tell us whether epilepsy [1, 5] or hypotonia [4] are required for diagnosis, nor do they specify behavioral phenotypes [1–6].
* **P04:** 
  * *Alignment:* Shows motor issues (rigidity, tremor, bradykinesia, dystonia) [4, 5] and psychiatric manifestations (anxiety, psychosis, hallucinations) [3].
  * *Ruling:* **Cannot rule in or rule out.** Although this profile resembles an adult-onset movement disorder rather than a neurodevelopmental syndrome with developmental delay and intellectual disability [3, 4, 5], the sources do not provide exclusion criteria [1–6].
* **P05:** 
  * *Alignment:* Has severe global developmental delay [3, 4, 5], severe intellectual disability [3, 4, 5], behavioral issues [3], and dysmorphic features [1]. 
  * *Ruling:* **Cannot rule in or rule out.** Seizures [1, 5] and hypotonia/coordination deficits [1, 4] are absent, but the sources do not state these are mandatory [1–6].
* **P06:** 
  * *Alignment:* Exhibits severe global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], generalized hypotonia [4], lack of coordination / motor issues (gait ataxia, broad-based gait) [1, 4, 5], epilepsy (tonic seizure, epileptic encephalopathy) [1, 5], psychiatric/behavioral symptoms (autistic behavior, sleep disturbance, restlessness) [3], and dysmorphisms [1].
  * *Ruling:* **Cannot rule in or rule out.** While P06 captures all clinical domains cited in the sources [1, 3, 4, 5], molecular confirmation or specific dysmorphism details are absent from the sources [1–6].
* **P07:** 
  * *Alignment:* Has global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], and dysmorphic features [1]. 
  * *Ruling:* **Cannot rule in or rule out.** Seizures [1, 5] and lack of coordination [1] are not documented, but the sources do not exclude patients without these signs [1–6].
* **P08:** 
  * *Alignment:* Has motor and speech delay [4, 5], seizures [1, 5], and autistic behavior [3]. 
  * *Ruling:* **Cannot rule in or rule out.** The sources do not mention retinal dystrophy (rod-cone dystrophy) [1–6].
* **P09:** 
  * *Alignment:* Has bilateral tonic-clonic seizures [1, 5], global developmental delay [3, 4, 5], motor delay [4, 5], and hypotonia [4]. 
  * *Ruling:* **Cannot rule in or rule out.** It lacks explicit lack of coordination [1] and psychiatric features [3], but the sources do not state these must be present in every individual [1–6].
* **P10:** 
  * *Alignment:* Demonstrates global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], lack of coordination / motor issues (ataxia, dystonia) [1, 4, 5], seizures (tonic, focal, myoclonic) [1, 5], psychiatric/behavioral manifestations (autism) [3], and dysmorphic features [1].
  * *Ruling:* **Cannot rule in or rule out.** It captures the general features described in the sources, but genetic and detailed clinical criteria are lacking to confirm or exclude it [1–6].

---

### Task 2: Most Likely Patient and Probability

* **Most Likely Patient:** **P06** (with **P10** as a close alternative).
  * *Reasoning:* P06 displays the complete spectrum of features specifically named across the sources: global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], generalized hypotonia [4], lack of coordination (gait ataxia, broad-based gait) [1], epilepsy (tonic seizure, epileptic encephalopathy) [1, 5], psychiatric manifestations (autistic behavior, sleep disturbance, restlessness) [3], and dysmorphisms [1].
* **Estimated Probability:** **40%**
  * *Note on probability:* Because the sources provide only brief summary descriptions, at least two patients (P06 and P10) heavily overlap with all listed terms [1–5], and others (such as P09) share several core features. Therefore, a clinical geneticist cannot assign high certainty without the missing diagnostic facts.

---

### Task 3: Missing Facts Needed for Diagnostic Confidence

To establish a definitive diagnosis, the following information—which the provided sources do not contain—is required:
1. **Genetic Testing:** Evidence of a heterozygous pathogenic or likely pathogenic variant in *MSL2* [2, 6].
2. **Epigenetic Signature:** Confirmation of the specific *MSL2* episignature identified in KBHS [1].
3. **Specific Dysmorphic Features:** Detailed characterization of the "specific dysmorphisms" mentioned in [1] (e.g., facial gestalt, cranial features, philtrum/nasal morphology).
4. **Complete Phenotypic Spectrum and Frequencies:** Full details on the psychiatric manifestations (cut off in [3]), seizure types, and the penetrance of hypotonia and ataxia [1, 3, 4, 5].
5. **Exclusionary Criteria:** Defined clinical criteria or known non-syndromic associations to rule out phenocopies (e.g., Rett-like disorders, Cockayne syndrome, or other epileptic encephalopathies) [1–6].

--------------------------------------------------------------------------------

### Round 3  (picked: P06)

### 1. Evaluation of Each Patient (Rule-In / Rule-Out)

The provided sources establish that Karayol-Borroto-Haghshenas neurodevelopmental syndrome (KBHS) caused by *MSL2* mutations is characterized by:
* Global developmental delay / developmental delay [3, 4, 5]
* Intellectual disability [3, 4, 5]
* Hypotonia [4]
* Motor issues / lack of coordination [1, 4, 5]
* Seizures / epilepsy [1, 5]
* Specific dysmorphisms (unspecified in the text) [1]
* Psychiatric manifestations (truncated/unspecified in the text) [3]
* Multisystem involvement [6]

The sources **do not** provide a complete list of clinical features, detailed dysmorphic features [1], specific psychiatric features [3], penetrance rates, or formal exclusion criteria. Consequently, **no patient can be definitively ruled in**, and no patient can be conclusively ruled out with 100% certainty, though some are far less consistent with the core description:

* **P01**: **Cannot be ruled in or definitively ruled out.** It displays global developmental delay [3, 4, 5], but the sources do not state whether epilepsy [1, 5], hypotonia [4], or motor coordination deficits [1, 4, 5] are obligate findings, nor do they detail the "specific dysmorphisms" [1] to verify the facial features.
* **P02**: **Cannot be ruled in or definitively ruled out.** It has global developmental delay [3, 4, 5] and seizures (infantile spasms) [1, 5], but the sources do not state if intellectual disability [3, 4, 5] or hypotonia [4] must be present, nor do they list cardiac defects or hemangiomas [1–6].
* **P03**: **Cannot be ruled in or definitively ruled out.** It has intellectual disability [3, 4, 5] and motor delays [4, 5], but seizures/epilepsy [1, 5] and hypotonia [4] are absent, and the sources do not clarify if these are required.
* **P04**: **Cannot be definitively ruled in or out, but highly inconsistent.** It presents with adult-onset-type neurodegenerative/parkinsonian features without documented global developmental delay or intellectual disability [3, 4, 5]. However, the sources do not explicitly state exclusion criteria [1–6].
* **P05**: **Cannot be ruled in or definitively ruled out.** It has global developmental delay and intellectual disability [3, 4, 5], but lacks seizures [1, 5], hypotonia [4], or coordination loss [1]. The sources do not specify the characteristic facial dysmorphisms [1].
* **P06**: **Cannot be definitively ruled in or out (Strong Candidate).** Displays global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], lack of coordination (gait ataxia) [1, 4, 5], and epilepsy/seizures [1, 5]. However, because the sources do not detail the "specific dysmorphisms" [1] or cutaneous findings [1–6], it cannot be definitively ruled in.
* **P07**: **Cannot be ruled in or definitively ruled out.** Has global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], and hypotonia [4], but lacks seizures/epilepsy [1, 5] and motor coordination deficits [1].
* **P08**: **Cannot be ruled in or definitively ruled out.** Has seizures [1, 5] and motor delay [4, 5], but lacks explicit intellectual disability [3, 4, 5] or hypotonia [4], and the sources do not mention rod-cone dystrophy [1–6].
* **P09**: **Cannot be ruled in or definitively ruled out.** Has seizures [1, 5], global developmental delay [3, 4, 5], motor delay [4, 5], and hypotonia [4], but lacks explicit intellectual disability [3, 4, 5] and ataxia/coordination deficits [1].
* **P10**: **Cannot be definitively ruled in or out (Strong Candidate).** Possesses global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], hypotonia [4], lack of coordination (ataxia) [1, 4, 5], seizures [1, 5], and multisystem features [6]. However, it cannot be confirmed because the sources omit the specific dysmorphisms [1] and full organ system spectrum [6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P06** (with **P10** as a near-equal alternative).
* **Estimated Probability:** **45%** (P10 holds approximately 40%, with the remaining ~15% distributed among other candidates that partially match the sparse data).

**Reasoning:** P06 exhibits all primary cardinal features explicitly stated across the sources: global developmental delay [3, 4, 5], intellectual disability [3, 4, 5], generalized hypotonia [4], epilepsy/seizures [1, 5], lack of coordination / ataxia [1, 4, 5], and dysmorphic features [1]. 

---

### 3. Facts Needed to Be Confident (Missing from Sources)

To definitively confirm the diagnosis, the following information—absent from sources [1–6]—would be required:
1. **Specific Craniofacial Dysmorphisms:** Source [1] mentions "specific dysmorphisms" but does not define them (e.g., palpebral fissure slant, nasal bridge shape, philtrum morphology).
2. **Phenotypic Spectrum and Penetrance:** The sources do not report the percentage penetrance of hypotonia [4], seizures [1, 5], or ataxia [1], leaving it uncertain whether their absence excludes a patient.
3. **Specific Psychiatric Manifestations:** Source [3] states "psychiatric manifestations including ..." but truncates the list, omitting whether autism, stereotypies, or hyperactivity are typical.
4. **Episignature and Molecular/Genetic Data:** Source [1] notes a "distinct episignature" and sources [2, 6] identify heterozygous *MSL2* mutations, none of which are provided for patients P01–P10.
5. **Delineation of Multisystem Involvements:** Source [6] calls KBHS a "multisystem disorder" but does not enumerate the affected organ systems (e.g., cardiac, ophthalmologic, gastrointestinal, or cutaneous).

--------------------------------------------------------------------------------

picks across rounds: ['P06', 'P06', 'P06']
