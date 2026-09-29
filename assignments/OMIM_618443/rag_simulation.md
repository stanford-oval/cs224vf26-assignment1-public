# Plain RAG on Neurodevelopmental disorder with or without variable brain abnormalities (MAPK8IP3, OMIM:618443)
model: gemini-3.8-flash   generated: 2026-09-28 20:46

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `MAPK8IP3 gene Neurodevelopmental disorder with or without variable brain abnormalities`

[1] **About MAPK8IP3 - TheCUREMAPK8IP3 Foundation**  
    https://curemapk8ip3.org/about-mapk8ip3/  
    De novo variants in MAPK8IP3 cause intellectual disability with variable brain anomalies · Recurrent de novo MAPK8IP3 variants cause neurological phenotypes ...

[2] **Entry - #618443 - NEURODEVELOPMENTAL DISORDER ...**  
    https://omim.org/entry/618443  
    neurodevelopmental disorder with or without variable brain abnormalities (NEDBA) is caused by heterozygous mutation in the MAPK8IP3 gene ( ...

[3] **Article De Novo Variants in MAPK8IP3 Cause Intellectual ...**  
    https://www.sciencedirect.com/science/article/pii/S0002929718304592  
    by K Platzer · 2019 · Cited by 84 — , we implicate de novo variants in MAPK8IP3 as a cause of a neurodevelopmental disorder with intellectual disability and variable brain ...

[4] **MAPK8IP3-Related Neurodevelopmental Disorder**  
    https://rarediseases.org/rare-diseases/mapk8ip3-related-neurodevelopmental-disorder/  
    MAPK8IP3-related neurodevelopmental disorder is a rare genetic condition caused by changes (variants) in the MAPK8IP3 gene, leading to ...

[5] **Characterization of a novel inherited splice-site variant in ...**  
    https://pmc.ncbi.nlm.nih.gov/articles/PMC13101558/  
    In humans, de novo heterozygous variants in the MAPK8IP3 gene have been associated with neurodevelopmental disorder with or without variable brain abnormalities ...

[6] **C206532 - Neurodevelopmental Disorder with ... - EVS Explore**  
    https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/C206532  
    An autosomal dominant condition caused by mutation(s) in the MAPK8IP3 gene, It is commonly characterized by global developmental delay, intellectual disability ...

## 2. The context handed to the model
```
[1] About MAPK8IP3 - TheCUREMAPK8IP3 Foundation
https://curemapk8ip3.org/about-mapk8ip3/
De novo variants in MAPK8IP3 cause intellectual disability with variable brain anomalies · Recurrent de novo MAPK8IP3 variants cause neurological phenotypes ...

[2] Entry - #618443 - NEURODEVELOPMENTAL DISORDER ...
https://omim.org/entry/618443
neurodevelopmental disorder with or without variable brain abnormalities (NEDBA) is caused by heterozygous mutation in the MAPK8IP3 gene ( ...

[3] Article De Novo Variants in MAPK8IP3 Cause Intellectual ...
https://www.sciencedirect.com/science/article/pii/S0002929718304592
by K Platzer · 2019 · Cited by 84 — , we implicate de novo variants in MAPK8IP3 as a cause of a neurodevelopmental disorder with intellectual disability and variable brain ...

[4] MAPK8IP3-Related Neurodevelopmental Disorder
https://rarediseases.org/rare-diseases/mapk8ip3-related-neurodevelopmental-disorder/
MAPK8IP3-related neurodevelopmental disorder is a rare genetic condition caused by changes (variants) in the MAPK8IP3 gene, leading to ...

[5] Characterization of a novel inherited splice-site variant in ...
https://pmc.ncbi.nlm.nih.gov/articles/PMC13101558/
In humans, de novo heterozygous variants in the MAPK8IP3 gene have been associated with neurodevelopmental disorder with or without variable brain abnormalities ...

[6] C206532 - Neurodevelopmental Disorder with ... - EVS Explore
https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/C206532
An autosomal dominant condition caused by mutation(s) in the MAPK8IP3 gene, It is commonly characterized by global developmental delay, intellectual disability ...
```

## 3. The gene, from the sources

Neurodevelopmental disorder with or without variable brain abnormalities (NEDBA) is a rare genetic condition caused by heterozygous mutations or variants in the *MAPK8IP3* gene [2, 4, 5]. The disorder follows an autosomal dominant pattern and is commonly characterized by global developmental delay, intellectual disability, and variable brain anomalies [1, 3, 6]. Studies identify de novo and recurrent variants in *MAPK8IP3* as the cause of these distinct neurological phenotypes [1, 3, 5]. 

However, the provided sources do not state what the gene product of *MAPK8IP3* is [1, 2, 3, 4, 5, 6]. In addition, details regarding what the gene or its product does in the cell are not covered in the text [1, 2, 3, 4, 5, 6]. Finally, while the sources explicitly establish that genetic changes and mutations in *MAPK8IP3* cause this condition, the precise biological mechanisms of how these variants cause disease are not covered [2, 4, 6].

*tokens in 560, out 1553*

## 4. The gene, closed book (no sources; beware hallucinations)

The ***MAPK8IP3*** gene encodes **JNK-interacting protein 3 (JIP3)**, a neuron-enriched scaffold protein that functions as a critical motor adaptor. JIP3 mediates bidirectional axonal transport by physically linking intracellular cargo (such as vesicles and JNK signaling complexes) to molecular motors—specifically kinesin-1 for anterograde transport and the dynein-dynactin complex for retrograde transport—supporting axon elongation, guidance, and synaptic maintenance.

Pathogenic variants in *MAPK8IP3* cause **neurodevelopmental disorder with or without variable brain abnormalities** (NEDVBA; OMIM #618443). Primarily occurring as *de novo* heterozygous missense changes (and occasionally biallelic variants), these alterations act via dominant-negative or loss-of-function mechanisms. They disrupt cargo binding and motor-protein interactions, impairing axonal trafficking and neuronal connectivity. This manifests clinically as intellectual disability, developmental delay, hypotonia, spasticity, and cerebral or cerebellar atrophy.

The disorder was first reported in **2019**.

**Citation:**  
Platzer, K., et al. (2019). *De Novo* Variants in *MAPK8IP3* Cause an Intellectual Disability Syndrome with Variable Brain Anomalies. *The American Journal of Human Genetics*, 104(6), 1216–1224.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P04)

Based on the provided sources ([1]–[6]), here is the clinical genetic assessment:

---

### 1. Patient-by-Patient Evaluation (Rule-In / Rule-Out)

* **P01:** **Cannot be ruled in or ruled out.** The patient presents with global developmental delay [6] and hypotonia (a neurological phenotype [1]), but the sources provide insufficient clinical detail to confirm or exclude MAPK8IP3-related disorder [1–6].
* **P02:** **Cannot be ruled in or ruled out.** The patient has severe intellectual disability [1, 3, 6] and a brain abnormality (cerebellar hypoplasia) [1, 2, 3, 5], which fit the broad description, but the sources do not provide enough granular phenotypic data to confirm or exclude [1–6].
* **P03:** **Cannot be ruled in or ruled out.** The patient has global developmental delay [6] and brain abnormalities (ventriculomegaly, inferior cerebellar vermis hypoplasia) [1, 2, 3, 5], consistent with the disorder name, but cannot be definitively ruled in or out [1–6].
* **P04:** **Cannot be ruled in or ruled out.** The patient exhibits both global developmental delay and intellectual disability [6], along with multiple brain abnormalities (delayed CNS myelination, reduced cerebral white matter volume, thin corpus callosum) [1, 2, 3, 5]. However, the sources lack detailed feature frequencies to confirm or exclude [1–6].
* **P05:** **Cannot be ruled in or ruled out.** The patient has intellectual disability [1, 3, 6] and a brain abnormality (enlarged cisterna magna) [1, 2, 3, 5], but the sources lack the specificity needed to rule them in or out [1–6].
* **P06:** **Cannot be ruled in or ruled out.** The patient has global developmental delay, intellectual disability [6], and cerebellar atrophy [1, 2, 3, 5]. The provided sources do not permit definitive confirmation or exclusion [1–6].
* **P07:** **Cannot be ruled in or ruled out.** The patient has intellectual disability [1, 3, 6] and cerebellar atrophy [1, 2, 3, 5], but cannot be ruled in or out from the provided text [1–6].
* **P08:** **Ruled out (highest confidence of exclusion).** This patient presents entirely with isolated renal and congenital heart malformations and exhibits neither intellectual disability [1, 3, 6], global developmental delay [6], neurological phenotypes [1], nor brain abnormalities [1, 2, 3, 5].
* **P09:** **Cannot be ruled in or ruled out.** The patient demonstrates global developmental delay, intellectual disability [6], and multiple structural brain anomalies (cerebellar hypoplasia, ventriculomegaly, white matter atrophy, thin corpus callosum) [1, 2, 3, 5]. The text does not provide sufficient detail to definitively confirm or exclude [1–6].
* **P10:** **Cannot be ruled in or ruled out.** The patient exhibits intellectual disability [1, 3, 6] and brain abnormalities (periventricular cysts, ventriculomegaly, thin corpus callosum) [1, 2, 3, 5], but cannot be ruled in or out based on the limited sources [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Candidate:** **P04** (or alternatively **P09** / **P06**). 
  * *Reasoning:* Source [6] explicitly defines the condition as "commonly characterized by global developmental delay, intellectual disability" [6], alongside "variable brain abnormalities" [1, 2, 3, 5]. P04, P06, and P09 are the candidates that explicitly document all three cardinal descriptors.
* **Estimated Probability:** **~15–20%**. 
  * *Justification:* Because the provided excerpts [1–6] contain only broad diagnostic labels rather than specific clinical case descriptions or HPO feature frequencies, they do not distinguish P04 from other neurodevelopmentally affected candidates with brain anomalies (such as P09, P06, P02, P03, P10). With 9 viable candidates matching the general description, no individual patient can be assigned high probability solely from these texts.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a definitive diagnosis, the following information—which is absent from sources [1]–[6]—is required:
1. **Molecular genetic data:** Demonstration of a pathogenic or likely pathogenic heterozygous (often *de novo*) variant in the *MAPK8IP3* gene [1, 2, 3, 5, 6].
2. **Detailed phenotypic spectrum and frequencies:** Specific prevalence of non-neurological features (e.g., dysmorphisms, limb contractures, seizures) in MAPK8IP3-related disorder cohorts.
3. **Specific neuroimaging signatures:** Which specific brain abnormalities (e.g., thin corpus callosum, vermis hypoplasia, myelination defects) are characteristic versus incidental in this condition.
4. **Full text/clinical tables of primary studies:** The actual patient tables and case reports from cited literature (e.g., Platzer et al., 2019 [3]), which are not included in the snippets.

--------------------------------------------------------------------------------

### Round 2  (picked: P04)

Based on the provided sources, here is the clinical genetic assessment:

### 1. Patient Evaluation (Rule-In / Rule-Out)

* **P01:** Cannot be ruled in or ruled out. The patient has global developmental delay, which commonly characterizes *MAPK8IP3*-related neurodevelopmental disorder [6]. However, the sources do not provide detailed phenotypic criteria or exclusionary rules to confirm or exclude this profile [1, 2, 3, 4, 5, 6].
* **P02:** Cannot be ruled in or ruled out. The patient has severe intellectual disability [1, 3, 6], a brain anomaly (cerebellar hypoplasia) [1, 2, 3, 5], and neurological phenotypes (seizure, spasticity) [1]. The sources do not describe whether arthrogryposis multiplex congenita or elevated creatinine are compatible or incompatible [1, 2, 3, 4, 5, 6].
* **P03:** Cannot be ruled in or ruled out. The patient presents with global developmental delay [6], brain abnormalities (ventriculomegaly, inferior cerebellar vermis hypoplasia) [1, 2, 3, 5], and neurological phenotypes (ataxia, dystonia, spasticity) [1]. The sources do not provide sufficient detail to determine whether this specific clinical presentation fits *MAPK8IP3* [1, 2, 3, 4, 5, 6].
* **P04:** Cannot be ruled in or ruled out. The patient manifests global developmental delay [6], severe intellectual disability [1, 3, 6], neurological phenotypes (generalized-onset motor seizure, unsteady gait) [1], and brain abnormalities (thin corpus callosum, reduced cerebral white matter volume, delayed CNS myelination) [1, 2, 3, 5]. However, the sources lack full clinical descriptions to definitively rule the patient in [1, 2, 3, 4, 5, 6].
* **P05:** Cannot be ruled in or ruled out. The patient has mild intellectual disability [1, 3, 6], neurological phenotypes (seizures, spasticity) [1], and a structural brain finding (enlarged cisterna magna) [1, 2, 3, 5]. The sources do not provide enough clinical data to confirm or exclude this case [1, 2, 3, 4, 5, 6].
* **P06:** Cannot be ruled in or ruled out. The patient exhibits global developmental delay [6], moderate intellectual disability [1, 3, 6], a brain abnormality (cerebellar atrophy) [1, 2, 3, 5], and neurological features (ataxia) [1]. The sources do not provide specific phenotypic profiles to rule the patient in or out [1, 2, 3, 4, 5, 6].
* **P07:** Cannot be ruled in or ruled out. The patient has intellectual disability [1, 3, 6] and a brain abnormality (cerebellar atrophy) [1, 2, 3, 5]. The sources provide no information regarding dysmorphic features or limb contractures to rule this patient in or out [1, 2, 3, 4, 5, 6].
* **P08:** **Ruled out.** *MAPK8IP3* causes a neurodevelopmental disorder characterized by intellectual disability [1, 3, 6], global developmental delay [6], neurological phenotypes [1], and variable brain abnormalities [1, 2, 3, 5]. P08 has exclusively congenital heart and renal defects without any neurodevelopmental delay, intellectual impairment, or brain anomalies [1, 2, 3, 4, 5, 6].
* **P09:** Cannot be ruled in or ruled out. The patient exhibits profound global developmental delay [6], intellectual disability [1, 3, 6], multiple variable brain abnormalities (cerebellar hypoplasia, ventriculomegaly, cerebral white matter atrophy, reduced cerebral white matter volume, thin corpus callosum) [1, 2, 3, 5], and neurological phenotypes (seizures, spasticity, dystonia) [1]. The sources do not provide the detailed multi-system phenotype needed to confirm or exclude this patient [1, 2, 3, 4, 5, 6].
* **P10:** Cannot be ruled in or ruled out. The patient has severe intellectual disability [1, 3, 6], spasticity [1], and brain abnormalities (ventriculomegaly, periventricular cysts, thin corpus callosum) [1, 2, 3, 5]. The sources do not state whether the extensive craniofacial and growth phenotype is compatible or incompatible with *MAPK8IP3* [1, 2, 3, 4, 5, 6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P04**
* **Estimated Probability:** **~25–30%**

**Reasoning:** 
P04 exhibits all core hallmarks mentioned across the sources: global developmental delay [6], intellectual disability [1, 3, 6], neurological signs [1], and variable structural brain anomalies (delayed CNS myelination, reduced cerebral white matter volume, thin corpus callosum) [1, 2, 3, 5], without the extensive multi-organ involvement (e.g., profound contractures, endocrinopathies, or distinct non-neural syndromic patterns) found in cases like P09 or P10. However, because the sources provide only brief, high-level summaries [1, 2, 3, 4, 5, 6] and multiple patients share neurodevelopmental delay and brain anomalies (e.g., P04, P06, P09), confidence is strictly constrained, keeping the probability low.

---

### 3. Missing Facts Needed for Confidence

To establish a definitive diagnosis, the following information—which is not present in the provided sources—would be required:
1. **Genotypic data:** Sequencing results identifying whether a heterozygous, likely de novo pathogenic variant in the *MAPK8IP3* gene is present in the patient [1, 2, 3, 5, 6].
2. **Detailed clinical spectrum and HPO frequencies:** Cohort-level frequencies of specific brain anomalies (e.g., thin corpus callosum, cerebellar hypoplasia, ventriculomegaly) and neurological features in *MAPK8IP3* patients, which the sources mention only generally as "variable brain abnormalities" and "neurological phenotypes" [1, 2, 3, 5].
3. **Information on non-neurological features:** Data indicating whether dysmorphic features, visual impairment, feeding difficulties, or skeletal findings are established components of *MAPK8IP3*-related neurodevelopmental disorder [1, 2, 3, 4, 5, 6].
4. **Explicit exclusion criteria:** Specific clinical signs or organ involvements that would definitively exclude an individual from having an *MAPK8IP3* variant [1, 2, 3, 4, 5, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P04)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources define *MAPK8IP3*-related disease as an autosomal dominant neurodevelopmental disorder with or without variable brain abnormalities (NEDBA) characterized by intellectual disability [1, 3, 6], global developmental delay [6], neurological phenotypes [1], and variable brain anomalies [1, 2, 3, 5]. The sources provide only broad descriptions and do not contain detailed diagnostic criteria, individual case profiles, or frequency tables for specific Human Phenotype Ontology (HPO) terms.

* **P01:** **Cannot rule in or rule out.** The patient has global developmental delay and motor/speech delays [6], but lacks documentation of brain anomalies or intellectual disability. The sources do not provide detailed phenotypic limits to determine whether this profile is sufficient [1–6].
* **P02:** **Cannot rule in or rule out.** Shows severe intellectual disability [1, 3, 6] and brain abnormalities (cerebellar hypoplasia) [1, 2, 3, 5], which fit the high-level description; however, the sources do not give specific criteria to confirm or exclude this patient [1–6].
* **P03:** **Cannot rule in or rule out.** Displays global developmental delay [6] and brain abnormalities (ventriculomegaly, inferior cerebellar vermis hypoplasia) [1, 2, 3, 5], fitting general descriptions, but the sources lack distinguishing details to confirm or exclude [1–6].
* **P04:** **Cannot rule in or rule out.** Features severe global developmental delay [6], severe intellectual disability [1, 3, 6], and brain abnormalities (thin corpus callosum, reduced cerebral white matter volume, delayed CNS myelination) [1, 2, 3, 5]. These match the generalized features, but the sources do not provide sufficient specifics to rule in or out [1–6].
* **P05:** **Cannot rule in or rule out.** Exhibits mild intellectual disability [1, 3, 6] and an enlarged cisterna magna [1, 2, 3, 5], but the sources lack granular phenotypic details to rule this patient in or out [1–6].
* **P06:** **Cannot rule in or rule out.** Has global developmental delay [6], moderate intellectual disability [1, 3, 6], and cerebellar atrophy [1, 2, 3, 5]. This matches the broad syndrome definition, but cannot be ruled in or out based solely on the sources [1–6].
* **P07:** **Cannot rule in or rule out.** Presents with intellectual disability [1, 3, 6] and cerebellar atrophy [1, 2, 3, 5], matching the general description, but cannot be confirmed or excluded using the sources [1–6].
* **P08:** **Rule out.** This patient has isolated renal and congenital heart defects with no intellectual disability, global developmental delay, or neurological phenotypes. Because the sources define the condition as a neurodevelopmental disorder characterized by intellectual disability and global developmental delay [1, 2, 3, 5, 6], P08 lacks the core defining features of the condition.
* **P09:** **Cannot rule in or rule out.** Demonstrates profound intellectual disability [1, 3, 6], profound global developmental delay [6], and multiple brain anomalies (cerebellar hypoplasia, ventriculomegaly, thin corpus callosum, cerebral white matter atrophy) [1, 2, 3, 5]. While consistent with the broad definition, the sources do not provide case-level data to rule this patient in or out [1–6].
* **P10:** **Cannot rule in or rule out.** Demonstrates severe intellectual disability [1, 3, 6], motor delay [6], and brain abnormalities (thin corpus callosum, ventriculomegaly) [1, 2, 3, 5]. However, the sources lack specific clinical checklists to rule this patient in or out [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P04** (or alternatively **P09**, **P03**, or **P02**). 
  * *Reasoning:* P04 exhibits all core characteristics mentioned across the sources: global developmental delay [6], intellectual disability [1, 3, 6], and variable structural brain anomalies (delayed myelination, thin corpus callosum, reduced white matter volume) [1, 2, 3, 5], accompanied by neurological signs (seizures, hypotonia) [1]. 
* **Estimated Probability:** **~12–15%** (essentially near an equal split of ~1/8 or ~1/9 among the candidate neurodevelopmental patients).
  * *Explicit limitation:* Strictly using sources [1–6], there is no textual evidence or statistical data distinguishing P04 from other patients with intellectual disability, developmental delay, and brain anomalies (e.g., P02, P03, P06, P07, P09, P10). Any assignment above an equal distribution cannot be justified by the provided texts alone.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To definitively identify the correct patient, the following missing information is required:
1. **Genetic / Molecular Data:** Confirmation of a heterozygous, typically de novo, pathogenic variant in the *MAPK8IP3* gene for the specific individual [1, 2, 3, 4, 5, 6].
2. **Detailed Phenotypic Spectrum and Frequencies:** An explicit HPO term breakdown indicating which specific brain anomalies (e.g., corpus callosum hypoplasia vs. cerebellar vermis hypoplasia vs. atrophy) and dysmorphic or systemic features correlate specifically with *MAPK8IP3* mutations.
3. **Differential / Exclusion Criteria:** Criteria distinguishing NEDBA from overlapping autosomal dominant or recessive neurodevelopmental syndromes presenting with intellectual disability, hypotonia, microcephaly, and brain malformations.

--------------------------------------------------------------------------------

picks across rounds: ['P04', 'P04', 'P04']
