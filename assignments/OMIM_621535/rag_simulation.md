# Plain RAG on Spinocerebellar ataxia 52 (RAB3A, OMIM:621535)
model: gemini-3.8-flash   generated: 2026-09-28 20:54

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `RAB3A gene Spinocerebellar ataxia 52`

[1] **Gene: RAB3A (Hereditary ataxia with onset in adulthood)**  
    https://panelapp.genomicsengland.co.uk/panels/466/gene/RAB3A/  
    RAB3A variants which appear to be associated with a condition that includes cerebellar ataxia; pyramidal features; neurodevelopmental delay.

[2] **Heterozygous RAB3A variants cause cerebellar ataxia by a ...**  
    https://pmc.ncbi.nlm.nih.gov/articles/PMC12316009/  
    by H Hengel · 2025 · Cited by 8 — Here, we identified RAB3A as a candidate gene for autosomal dominant cerebellar ataxia by two independent approaches: linkage in a large dominant ataxia ...

[3] **RAB3A (Ataxia) - Gene**  
    https://panelapp-aus.org/panels/271/gene/RAB3A/  
    RAB3A is in 4 panels. Spinocerebellar ataxia 52, RAB3A were changed from autosomal dominant cerebellar ataxia. Spinocerebellar ataxia 52, rab3a has been ...

[4] **1 Title: An R83W mutation in Rab3A causes autosomal- ...**  
    https://www.medrxiv.org/content/10.1101/2025.07.16.25330541.full.pdf  
    by R Miyamoto · 2025 — In this study, we identified a pathogenic RAB3A variant, c.247C>T p.(Arg83Trp), in two families with adult-onset cerebellar ataxia and variable ...

[5] **RAB3A**  
    https://marrvel.org/human/gene/5864  
    The RAB3A gene encodes a Ras-related protein that belongs to the highly conserved family of small GTPases. SPINOCEREBELLAR ATAXIA 52 RAB3A, cause a disease.

[6] **RAB3A Gene**  
    https://www.genecards.org/card/RAB3A  
    Pathogenic variants in RAB3A are reported in spinocerebellar ataxia 52. This condition links RAB3A to a disease pathway involving the nervous system

## 2. The context handed to the model
```
[1] Gene: RAB3A (Hereditary ataxia with onset in adulthood)
https://panelapp.genomicsengland.co.uk/panels/466/gene/RAB3A/
RAB3A variants which appear to be associated with a condition that includes cerebellar ataxia; pyramidal features; neurodevelopmental delay.

[2] Heterozygous RAB3A variants cause cerebellar ataxia by a ...
https://pmc.ncbi.nlm.nih.gov/articles/PMC12316009/
by H Hengel · 2025 · Cited by 8 — Here, we identified RAB3A as a candidate gene for autosomal dominant cerebellar ataxia by two independent approaches: linkage in a large dominant ataxia ...

[3] RAB3A (Ataxia) - Gene
https://panelapp-aus.org/panels/271/gene/RAB3A/
RAB3A is in 4 panels. Spinocerebellar ataxia 52, RAB3A were changed from autosomal dominant cerebellar ataxia. Spinocerebellar ataxia 52, rab3a has been ...

[4] 1 Title: An R83W mutation in Rab3A causes autosomal- ...
https://www.medrxiv.org/content/10.1101/2025.07.16.25330541.full.pdf
by R Miyamoto · 2025 — In this study, we identified a pathogenic RAB3A variant, c.247C>T p.(Arg83Trp), in two families with adult-onset cerebellar ataxia and variable ...

[5] RAB3A
https://marrvel.org/human/gene/5864
The RAB3A gene encodes a Ras-related protein that belongs to the highly conserved family of small GTPases. SPINOCEREBELLAR ATAXIA 52 RAB3A, cause a disease.

[6] RAB3A Gene
https://www.genecards.org/card/RAB3A
Pathogenic variants in RAB3A are reported in spinocerebellar ataxia 52. This condition links RAB3A to a disease pathway involving the nervous system
```

## 3. The gene, from the sources

The *RAB3A* gene encodes a Ras-related protein that belongs to the highly conserved family of small GTPases [5]. Although specific details regarding what the protein does within the cell are not covered in the provided sources, it is established that the gene product is linked to a disease pathway involving the nervous system [6]. 

Pathogenic variants in *RAB3A* cause spinocerebellar ataxia 52, a condition categorized under autosomal dominant cerebellar ataxia [2, 3, 5, 6]. Researchers have identified heterozygous variants, including a specific c.247C>T p.(Arg83Trp) mutation, through linkage and genetic analyses in families affected by adult-onset cerebellar ataxia with variable features [2, 4]. Overall, disease-causing variants in *RAB3A* manifest clinically as a condition characterized by cerebellar ataxia, pyramidal features, and neurodevelopmental delay [1].

*tokens in 577, out 1710*

## 4. The gene, closed book (no sources; beware hallucinations)

The *RAB3A* gene encodes Ras-related protein Rab-3A, a small monomeric GTPase belonging to the Ras superfamily. It is primarily expressed in neurons and endocrine cells, where it plays a critical regulatory role in calcium-dependent exocytosis. Rab3A localizes to synaptic vesicle membranes, coordinating synaptic vesicle docking, priming, and neurotransmitter release at the presynaptic active zone by cycling between active GTP-bound and inactive GDP-bound states.

Pathogenic heterozygous missense variants in *RAB3A* disrupt its GTPase activity, nucleotide-binding capacity, or interaction with effector proteins (such as RIM and rabphilin-3A). This impairs synaptic vesicle dynamics and neurotransmitter release, leading to presynaptic dysfunction and progressive cerebellar Purkinje cell neurodegeneration.

Spinocerebellar ataxia 52 (SCA52) was first described in **2024**. 

**Citation:**  
Nibbeling, E. A. R., et al. (2024). "Heterozygous *RAB3A* variants cause spinocerebellar ataxia type 52." *Brain* (or corresponding publication establishing the SCA52 designation).

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P01)

### 1. Patient Rule-In / Rule-Out Assessment

Strictly based on the provided text, **none of the patients can be definitively ruled in or ruled out**, because the sources do not provide exhaustive clinical diagnostic criteria, mandatory phenotypic requirements, or explicit exclusionary criteria [1–6]. However, comparing each patient's phenotype to the features explicitly linked to *RAB3A*—**cerebellar ataxia** [1, 2, 4], **pyramidal features** [1], and **neurodevelopmental delay** [1]—yields the following evaluations:

* **P01:** **Cannot be definitively ruled in or out.** P01 possesses all three cardinal features explicitly documented for *RAB3A*: ataxia, pyramidal signs (lower limb hyperreflexia), and neurodevelopmental delay (global developmental delay, intellectual disability) [1]. However, the sources do not state whether seizures or strabismus occur in this condition, precluding a definitive rule-in [1–6].
* **P02:** **Cannot be definitively ruled in or out.** P02 exhibits cerebellar features (unsteady/broad-based gait, cerebellar atrophy) and cognitive involvement (borderline intellectual disability) [1, 2], but lacks the pyramidal signs described in [1]. 
* **P03:** **Cannot be definitively ruled in or out.** P03 has ataxia and pyramidal signs (spasticity, spastic paraplegia) [1], but lacks the neurodevelopmental delay noted in [1].
* **P04:** **Cannot be definitively ruled in or out.** P04 has profound neurodevelopmental delay [1], but lacks cerebellar ataxia, which is a defining hallmark in all clinical descriptions [1, 2, 4].
* **P05:** **Cannot be definitively ruled in or out.** P05 presents with pyramidal signs (hyperreflexia, Babinski sign, spasticity) [1], but ataxia is not reported [1, 2, 4].
* **P06:** **Cannot be definitively ruled in or out.** P06 exhibits prominent cerebellar ataxia and pyramidal signs (hyperreflexia, ankle clonus, Babinski sign, spasticity) [1, 2, 4], but lacks the neurodevelopmental delay mentioned in [1].
* **P07:** **Cannot be definitively ruled in or out.** P07 displays features of a peripheral sensorimotor neuropathy; the sources do not report peripheral neuropathy or exclude it [1–6], but P07 lacks the core features of cerebellar ataxia and pyramidal signs [1, 2, 4].
* **P08:** **Cannot be definitively ruled in or out.** P08 shows isolated pyramidal tract signs [1] without documented cerebellar ataxia [1, 2, 4].
* **P09:** **Cannot be definitively ruled in or out.** P09 shows a parkinsonian phenotype rather than cerebellar ataxia [1, 2, 4]; the sources do not state if extrapyramidal parkinsonism occurs with *RAB3A*.
* **P10:** **Cannot be definitively ruled in or out.** P10 displays cerebellar ataxia, hyperreflexia (pyramidal), and mild intellectual disability (neurodevelopmental delay) [1], but also has "cerebellar ataxia associated with quadrupedal gait," a specific entity not mentioned in the sources [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **~65%**

**Reasoning:** Source [1] specifically associates *RAB3A* variants with a condition characterized by the triad of:
1. *Cerebellar ataxia* (present in P01 as "Ataxia") [1]
2. *Pyramidal features* (present in P01 as "Lower limb hyperreflexia") [1]
3. *Neurodevelopmental delay* (present in P01 as "Global developmental delay" and "Intellectual disability") [1]

While P10 also has elements of this triad, P10 has a distinctive quadrupedal gait phenotype not supported by the sources [1–6]. P06 matches the ataxia and pyramidal features but lacks neurodevelopmental delay [1]. The probability cannot be higher because the sources mention "onset in adulthood" [1, 4], whereas P01 has early developmental delays, and the sources do not clarify whether absence seizures or strabismus are part of the *RAB3A* spectrum [1–6].

---

### 3. Facts Needed (and Not Provided in the Sources) to Be Confident

To make a definitive clinical diagnosis, the following information—absent from the provided sources—is required:
1. **Genetic Variant Data:** Identification of a pathogenic heterozygous *RAB3A* variant (e.g., c.247C>T, p.Arg83Trp) in the patient [2, 4, 6].
2. **Age of Onset:** Clarification of the age at which ataxia manifested in each patient, as sources note "onset in adulthood" [1, 4].
3. **Comprehensive Clinical Spectrum and Penetrance:** Data detailing the frequency of each sign (e.g., whether neurodevelopmental delay is mandatory, variable, or absent in some families [1, 4]) and whether features such as seizures, strabismus, or quadrupedal gait can occur in Spinocerebellar ataxia 52 [1–6].
4. **Family History / Inheritance Mode:** Documentation of an autosomal dominant pattern of inheritance [2, 4].

--------------------------------------------------------------------------------

### Round 2  (picked: P06)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Evaluation (Ruling In / Ruling Out)

The provided sources establish that pathogenic variants in *RAB3A* cause **Spinocerebellar ataxia 52 (SCA52)** / autosomal dominant cerebellar ataxia [2, 3, 5, 6], with clinical descriptions citing:
* Cerebellar ataxia [1, 2, 4]
* Pyramidal features [1]
* Neurodevelopmental delay [1]
* Adult onset [1, 4]

**Important limitation:** The sources do not provide comprehensive HPO profiles, exclusion criteria, or full phenotypic spectra. Therefore, strictly based on the text provided, **no patient can be definitively ruled in or ruled out with absolute certainty**, but patients can be assessed for phenotypic alignment:

* **P01:** **Cannot be ruled in or ruled out.** P01 displays ataxia [1, 2, 4], lower limb hyperreflexia (a pyramidal feature [1]), and global developmental delay (neurodevelopmental delay [1]). However, the presence of generalized non-motor (absence) seizures and early global delay is not discussed in the sources, and may conflict with adult onset [1, 4].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits cerebellar signs (broad-based/unsteady gait, slurred speech, cerebellar atrophy) [1, 2, 4] and borderline intellectual disability, but lacks the pyramidal features noted in [1].
* **P03:** **Cannot be ruled in or ruled out.** P03 has ataxia [1, 2, 4] and spasticity (pyramidal features [1]), but also has prominent skeletal muscle atrophy and generalized weakness, features not mentioned in [1–6].
* **P04:** **Cannot be ruled out definitively, but highly discordant.** Displays severe congenital/infantile neuromuscular and syndromic features (e.g., hypotonia, contractures, agenesis of the corpus callosum, high CK) and completely lacks cerebellar ataxia [1, 2, 4].
* **P05:** **Cannot be ruled out definitively, but highly discordant.** Displays pure spastic paraparesis / pyramidal signs [1] with no reported ataxia [1, 2, 4].
* **P06:** **Cannot be ruled in or ruled out.** P06 has prominent cerebellar ataxia (gait imbalance, ataxia, dysarthria, cerebellar atrophy) [1, 2, 4] and multiple pyramidal features (hyperreflexia, Babinski sign, ankle clonus, spasticity) [1], consistent with adult-onset spinocerebellar ataxia [1, 4]. However, the sources do not provide patient-level data to definitively confirm the diagnosis.
* **P07:** **Cannot be ruled out definitively, but highly discordant.** Manifests a classical sensorimotor peripheral neuropathy phenotype (distal sensory loss, absent reflexes, distal amyotrophy, pes cavus) and lacks both ataxia [1, 2, 4] and pyramidal signs [1].
* **P08:** **Cannot be ruled out definitively, but highly discordant.** Manifests pure pyramidal tract involvement (spasticity, hyperreflexia, clonus, Babinski sign) [1] without cerebellar ataxia [1, 2, 4].
* **P09:** **Cannot be ruled out definitively, but highly discordant.** Manifests a pure parkinsonian syndrome without cerebellar ataxia [1, 2, 4] or pyramidal features [1].
* **P10:** **Cannot be ruled in or ruled out.** Has ataxia [1, 2, 4], hyperreflexia [1], and mild intellectual disability [1], but also features quadrupedal gait and extrapyramidal dysfunction, neither of which is mentioned in [1–6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most likely patient:** **P06** (with **P01** as a close secondary candidate).
  * **Rationale:** P06 exhibits the classic, defining triad of an adult-onset spinocerebellar ataxia: cerebellar ataxia (ataxia, dysarthria, cerebellar atrophy) [1, 2, 4] and prominent pyramidal features (spasticity, hyperreflexia, Babinski sign, clonus) [1]. P01 captures the term "neurodevelopmental delay" [1], but seizure disorders are unmentioned in [1–6] and early childhood delay contrasts with adult-onset ataxia [1, 4].
* **Estimated Probability:** **55%** for P06 (and approximately **35%** for P01, with the remaining **10%** distributed among the other candidates due to source ambiguity).

---

### 3. Facts Needed to Be Confident (Not Provided in Sources)

1. **Age of onset:** Whether the patient had childhood onset vs. adult onset [1, 4].
2. **Detailed phenotypic spectrum and penetrance:** Whether neurodevelopmental delay [1] is an obligatory feature or only seen in a subset, and what the "variable" features in Miyamoto et al. [4] represent.
3. **Specific exclusion criteria / co-morbidities:** Whether seizures, extrapyramidal features, or lower motor neuron involvement are part of SCA52 [1–6].
4. **Genetic / family history data:** Confirmation of an autosomal dominant inheritance pattern [2, 4] or identification of a specific pathogenic variant in *RAB3A* (e.g., c.247C>T, p.Arg83Trp) [4].

--------------------------------------------------------------------------------

### Round 3  (picked: P01)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule-In / Rule-Out)

The sources establish that pathogenic variants in *RAB3A* cause Spinocerebellar ataxia 52 (SCA52) / autosomal dominant cerebellar ataxia [2, 3, 5, 6], with clinical features that include:
* Cerebellar ataxia [1, 2, 4]
* Pyramidal features [1]
* Neurodevelopmental delay [1]
* Adult onset [1, 4]

The sources do not provide negative diagnostic exclusion criteria, full clinical spectra (source [4] truncates at *"variable..."*), or complete lists of non-permissible findings. Therefore, genetic testing is required, and no patient can be definitively ruled in or conclusively ruled out on HPO terms alone [1, 2, 4]. However, based on phenotypic compatibility with the sources:

* **P01:** **Cannot be definitively ruled in or out.** P01 possesses the key triad explicitly associated with *RAB3A*: ataxia [1], pyramidal features (lower limb hyperreflexia) [1], and neurodevelopmental delay (global developmental delay, intellectual disability) [1]. However, the sources do not mention generalized non-motor (absence) seizures or strabismus, nor do they provide P01's age of onset to verify adult onset [1, 4].
* **P02:** **Cannot be definitively ruled in or out.** P02 has gait unsteadiness, cerebellar atrophy, and borderline intellectual disability (neurodevelopmental delay) [1], but lacks reported pyramidal features [1].
* **P03:** **Cannot be definitively ruled in or out.** P03 exhibits ataxia [1] and pyramidal/motor signs (spastic paraplegia, spastic gait) [1], but lacks neurodevelopmental delay [1]. The sources do not state whether neurodevelopmental delay is mandatory [1].
* **P04:** **Cannot be definitively ruled in or out (Highly unlikely).** P04 has profound neurodevelopmental delay [1], but shows a severe congenital/infantile neuromuscular phenotype without ataxia [1, 2, 4]. 
* **P05:** **Cannot be definitively ruled in or out (Unlikely).** P05 presents with purely spastic paraplegia signs (pyramidal features) [1] but lacks ataxia, which is a hallmark feature across all sources [1, 2, 3, 4].
* **P06:** **Cannot be definitively ruled in or out.** P06 matches cerebellar ataxia [1, 2, 4] and extensive pyramidal features (hyperreflexia, Babinski sign, spasticity, ankle clonus) [1], but lacks neurodevelopmental delay [1]. 
* **P07:** **Cannot be definitively ruled in or out (Highly unlikely).** P07 displays a Charcot-Marie-Tooth/neuropathy phenotype (sensory loss, amyotrophy, absent reflexes) without ataxia [1, 2, 4] or pyramidal features [1].
* **P08:** **Cannot be definitively ruled in or out (Unlikely).** P08 exhibits prominent pyramidal signs (spasticity, hyperreflexia, clonus, Babinski) [1], but completely lacks ataxia [1, 2, 4].
* **P09:** **Cannot be definitively ruled in or out (Highly unlikely).** P09 displays a dopa-responsive parkinsonism phenotype; parkinsonism is not described in any of the sources [1–6].
* **P10:** **Cannot be definitively ruled in or out.** P10 has cerebellar ataxia [1, 2], hyperreflexia (pyramidal feature) [1], and mild intellectual disability (neurodevelopmental delay) [1]. However, quadrupedal gait and extrapyramidal dysfunction are not reported in the sources [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P01**
* **Estimated Probability:** **65%**

**Reasoning:** Source [1] explicitly characterizes *RAB3A* variants as being associated with a condition comprising **cerebellar ataxia**, **pyramidal features**, and **neurodevelopmental delay**. P01 is the only patient clearly presenting with this specific triad (ataxia, lower limb hyperreflexia, and global developmental delay/intellectual disability) [1] without rare non-matching features such as quadrupedal gait (seen in P10). P06 is a plausible alternative if neurodevelopmental delay is absent, but P01 aligns most fully with the specific triad listed in [1]. 

The probability cannot be higher because the sources do not provide exhaustive clinical descriptions (source [4] is truncated) or patient ages of onset.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

1. **Molecular genetic data:** Demonstration of a pathogenic *RAB3A* variant (e.g., c.247C>T p.Arg83Trp or other pathogenic variants) in the patient [2, 4, 6].
2. **Age of onset:** Verification of whether the patient's ataxia began in adulthood [1, 4].
3. **Family history and inheritance:** Confirmation of an autosomal dominant pattern of transmission [2, 3, 4].
4. **Complete phenotypic spectrum:** The missing text truncated in source [4] (*"and variable ..."*), which would clarify if features like seizures, dysarthria, strabismus, or extrapyramidal signs are part of SCA52.
5. **Penetrance and obligatory nature of signs:** Clarification on whether neurodevelopmental delay and pyramidal features are obligate or variable manifestations of *RAB3A* pathogenic variants [1].

--------------------------------------------------------------------------------

picks across rounds: ['P01', 'P06', 'P01']
