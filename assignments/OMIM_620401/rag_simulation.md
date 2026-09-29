# Plain RAG on Intellectual developmental disorder, autosomal recessive 84 (SGSM3, OMIM:620401)
model: gemini-3.8-flash   generated: 2026-09-28 20:47

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `SGSM3 gene Intellectual developmental disorder, autosomal recessive 84`

[1] **Intellectual Developmental Disorder, Autosomal Recessive ...**  
    https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_recessive_84  
    Autosomal recessive intellectual developmental disorder-84 (MRT84) is characterized by developmental delay, short stature, and dysmorphic facial features.

[2] **610440 - SMALL G PROTEIN SIGNALING MODULATOR 3; ...**  
    https://omim.org/entry/610440  
    .0001 INTELLECTUAL DEVELOPMENTAL DISORDER, AUTOSOMAL RECESSIVE 84 ... In 13 patients from 8 families of Ashkenazi Jewish origin with mild to moderate intellectual ...

[3] **SGSM3**  
    https://panelapp-aus.org/panels/entities/SGSM3  
    Phenotypes. Intellectual developmental disorder, autosomal recessive 84, MIM# 620401. Tags. founder. Green SGSM3 in Intellectual disability syndromic and non- ...

[4] **SGSM3 gene Small G Protein Signaling Modulator 3**  
    https://www.genecards.org/card/SGSM3  
    Diseases associated with SGSM3 include Intellectual Developmental Disorder, Autosomal Recessive 84 and Warburg Micro Syndrome 4. Among its related pathways ...

[5] **SGSM3-associated disorder · Issue #537**  
    https://github.com/OD4RD/Main-Help-Desk/issues/537  
    ... Gene for Nonsyndromic Intellectual Disability Phenotype: SGSM3 ... • OMIM: 620401 – Intellectual developmental disorder, autosomal recessive 84.

[6] **Birnbaum-et-al-2023-SGSM3.pdf**  
    https://doryeshorim.org/wp-content/uploads/2025/03/Birnbaum-et-al-2023-SGSM3.pdf  
    In this paper, we highlight SGSM3 as a candidate disease gene for autosomal recessive mild to moderate intellectual disability. We identified a founder ...

## 2. The context handed to the model
```
[1] Intellectual Developmental Disorder, Autosomal Recessive ...
https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_recessive_84
Autosomal recessive intellectual developmental disorder-84 (MRT84) is characterized by developmental delay, short stature, and dysmorphic facial features.

[2] 610440 - SMALL G PROTEIN SIGNALING MODULATOR 3; ...
https://omim.org/entry/610440
.0001 INTELLECTUAL DEVELOPMENTAL DISORDER, AUTOSOMAL RECESSIVE 84 ... In 13 patients from 8 families of Ashkenazi Jewish origin with mild to moderate intellectual ...

[3] SGSM3
https://panelapp-aus.org/panels/entities/SGSM3
Phenotypes. Intellectual developmental disorder, autosomal recessive 84, MIM# 620401. Tags. founder. Green SGSM3 in Intellectual disability syndromic and non- ...

[4] SGSM3 gene Small G Protein Signaling Modulator 3
https://www.genecards.org/card/SGSM3
Diseases associated with SGSM3 include Intellectual Developmental Disorder, Autosomal Recessive 84 and Warburg Micro Syndrome 4. Among its related pathways ...

[5] SGSM3-associated disorder · Issue #537
https://github.com/OD4RD/Main-Help-Desk/issues/537
... Gene for Nonsyndromic Intellectual Disability Phenotype: SGSM3 ... • OMIM: 620401 – Intellectual developmental disorder, autosomal recessive 84.

[6] Birnbaum-et-al-2023-SGSM3.pdf
https://doryeshorim.org/wp-content/uploads/2025/03/Birnbaum-et-al-2023-SGSM3.pdf
In this paper, we highlight SGSM3 as a candidate disease gene for autosomal recessive mild to moderate intellectual disability. We identified a founder ...
```

## 3. The gene, from the sources

The *SGSM3* gene encodes the Small G Protein Signaling Modulator 3 protein [2, 4]. What the gene product specifically does within the cell is not covered in the provided sources [4]. 

*SGSM3* is associated with intellectual developmental disorder, autosomal recessive 84 (MRT84, MIM# 620401) [3, 4, 5]. This disorder is characterized by developmental delay, short stature, dysmorphic facial features, and mild to moderate intellectual disability [1, 2, 6]. The condition has been documented in families of Ashkenazi Jewish origin, and researchers have identified a founder variant in *SGSM3* linked to the phenotype [2, 3, 6]. However, the precise cellular or molecular mechanisms explaining how variants in this gene cause disease are not covered in the provided sources [2, 6].

*tokens in 557, out 1118*

## 4. The gene, closed book (no sources; beware hallucinations)

domains that interacts with small GTPases (specifically RAP and RAB families). It regulates intracellular vesicular trafficking, endosomal sorting, and cytoskeletal dynamics essential for neurodevelopment.
        2. **Disease & mechanism:** Biallelic loss-of-function variants (e.g., nonsense, frameshift, or splice-site mutations) cause *Intellectual developmental disorder, autosomal recessive 84* (MRT84). These variants lead to loss of functional SGSM3, perturbing intracellular transport and neuronal signaling, which manifests clinically as severe developmental delay, microcephaly, spasticity, and seizures.
        3. **Discovery & Citation:** The disorder was first described in **2022** by [Author et al.] / (Citation).
        Wait,

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P03)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient-by-Patient Assessment (Rule-In / Rule-Out)

*Note on clinical limitations from the sources:* The provided sources define autosomal recessive intellectual developmental disorder-84 (MRT84) as being characterized by developmental delay, short stature, and dysmorphic facial features [1], with mild to moderate intellectual disability observed in a founder cohort [2, 6]. Some sources mention it under nonsyndromic intellectual disability [5] or both syndromic and nonsyndromic panels [3]. However, the sources do **not** provide complete penetrance statistics, an exhaustive list of associated dysmorphic features, exclusion criteria, or molecular test results for any patient. Consequently, **no patient can be definitively ruled in** (as none have molecular genetic confirmation of *SGSM3* variants [2, 3, 4, 5, 6]), and **no patient can be definitively ruled out with 100% certainty** because the sources do not state that any clinical feature is strictly obligate or exclusionary.

* **P01**: **Cannot rule in or definitively rule out.** The patient has mild global developmental delay and mild intellectual disability, which aligns with the mild-to-moderate severity noted in [2, 6]. However, the patient lacks short stature and dysmorphic facial features, which are characteristic of MRT84 [1].
* **P02**: **Cannot rule in or definitively rule out.** The patient has intellectual disability and global developmental delay [1, 2, 6]. This presentation could align with a "nonsyndromic intellectual disability phenotype" mentioned for *SGSM3* [5], but the patient lacks short stature and dysmorphic facial features described as characteristic in [1].
* **P03**: **Cannot rule in or definitively rule out.** The patient exhibits all three core features specified in [1]: developmental delay (motor, speech, and global delay), short stature, and multiple dysmorphic facial features (microtia, protruding ear, prominent nasal bridge, upslanted palpebral fissure, hypertelorism) [1]. However, the patient has "severe intellectual disability," which conflicts with the "mild to moderate intellectual disability" documented in [2, 6]. 
* **P04**: **Cannot rule in or definitively rule out.** The patient has developmental delay, intellectual disability, and short stature [1, 2, 6]. However, the patient does not have dysmorphic facial features listed [1], the severity of intellectual disability is unspecified [2, 6], and the sources do not mention whether structural renal or congenital heart defects occur in MRT84.
* **P05**: **Cannot rule in or definitively rule out.** The patient has mild intellectual disability and global developmental delay [1, 2, 6], but has macrocephaly and lacks the short stature characterized in [1].
* **P06**: **Cannot rule in or definitively rule out.** While the patient has global developmental delay [1], intellectual disability is not documented [2, 6], and the patient lacks short stature and dysmorphic facial features [1].
* **P07**: **Cannot rule in or definitively rule out.** The patient has developmental delay, intellectual disability [1, 2, 6], and dysmorphic facial features (micrognathia, retrognathia) [1], but lacks short stature [1].
* **P08**: **Cannot rule in or definitively rule out.** The patient has severe global developmental delay, but intellectual disability is not documented [2, 6], and the patient lacks short stature and dysmorphic facial features [1].
* **P09**: **Cannot rule in or definitively rule out.** The patient has moderate intellectual disability and moderate global developmental delay [2, 6]. However, the patient has "tall stature," which directly opposes the "short stature" characteristic of MRT84 [1].
* **P10**: **Cannot rule in or definitively rule out.** The patient has mild intellectual disability [2, 6], developmental delay [1], and facial dysmorphisms (mandibular prognathia, thick eyebrow) [1], but lacks short stature [1].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient**: **P03**
* **Estimated Probability**: **40%**

**Reasoning:**
Source [1] explicitly states that MRT84 is characterized by the triad of:
1. Developmental delay
2. Short stature
3. Dysmorphic facial features [1]

**P03** is the only patient in the group who displays all three cardinal features (global/motor/speech developmental delay, short stature, and multiple craniofacial dysmorphisms including microtia, protruding ears, prominent nasal bridge, upslanted palpebral fissures, and hypertelorism) [1]. 

The main discrepancy is that P03 has "severe intellectual disability," whereas sources [2] and [6] specify "mild to moderate intellectual disability" [2, 6]. However, [2] and [6] report a specific cohort of 13 patients from 8 families of Ashkenazi Jewish origin [2], and the sources do not establish that severe intellectual disability is an absolute exclusion criterion or that the full phenotypic spectrum has been completely defined. Because of this phenotypic conflict and the absence of molecular data, the probability remains modest (~40%), with **P04** (having short stature and developmental delay [1], but lacking dysmorphic features) and **P02** (fitting a purely nonsyndromic presentation [5]) remaining alternate possibilities.

---

### 3. Facts Needed to Be Confident (Not in the Sources)

To establish a definitive diagnosis, the following information is required but missing from the provided sources:
1. **Molecular Genetic Confirmation**: Identification of biallelic pathogenic or likely pathogenic variants in the *SGSM3* gene (such as the Ashkenazi Jewish founder variant mentioned in [2, 6]).
2. **Definitive Clinical Diagnostic & Exclusion Criteria**: Clarity on whether short stature and dysmorphic facial features are obligate for MRT84 [1], or whether *SGSM3* can cause purely nonsyndromic intellectual disability [5].
3. **Phenotypic Severity Spectrum**: Data on whether the intellectual disability in MRT84 can range to severe, or if it is strictly restricted to mild-to-moderate impairment [2, 6].
4. **Comprehensive Dysmorphology & Organ Involvement Data**: A complete inventory of characteristically associated dysmorphic facial features and systemic/visceral manifestations (e.g., whether cardiac, renal, or central nervous system structural anomalies are seen in MRT84) [1, 2, 3, 4, 5, 6].
5. **Ancestry / Demographic Background**: Information on whether the patient is of Ashkenazi Jewish descent, in whom the founder variant was established [2, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P04)

Based on the provided sources, here is the clinical evaluation for Intellectual Developmental Disorder, Autosomal Recessive 84 (MRT84; caused by pathogenic variants in *SGSM3*):

---

### 1. Patient Rule-In / Rule-Out Assessment

*The sources establish that MRT84 is characterized by developmental delay, short stature, and dysmorphic facial features [1], as well as mild to moderate intellectual disability [2, 6], and can present as a syndromic or non-syndromic intellectual disability phenotype [3, 5]. However, the sources do not provide complete penetrance data, mandatory diagnostic criteria, or formal exclusion criteria [1–6]. Consequently, no patient can be definitively ruled in without genetic confirmation [2–6], and strict clinical rule-outs are limited to clear phenotypic contradictions.*

* **P01:** **Cannot rule in or rule out.** The patient has mild global developmental delay and mild intellectual disability, which aligns with [1, 2, 6]. However, the sources do not specify whether the absence of short stature or dysmorphic facial features [1] excludes the diagnosis, particularly given references to non-syndromic presentations [3, 5].
* **P02:** **Cannot rule in or rule out.** The patient has intellectual disability and global developmental delay [1, 2, 6], consistent with reports of a non-syndromic phenotype [5]. However, the sources do not state whether the presence of autistic behavior or phimosis is associated with or excludes MRT84 [1–6].
* **P03:** **Likely ruled out.** Although the patient displays developmental delay, short stature, and dysmorphic facial features (microtia, protruding ear, prominent nasal bridge, hypertelorism) [1], they have *severe* intellectual disability. Sources [2] and [6] specifically characterize the disorder by *mild to moderate* intellectual disability.
* **P04:** **Cannot rule in or rule out.** The patient exhibits developmental delay, intellectual disability, and short stature [1, 2, 6]. The severity of intellectual disability is not specified, and the sources provide no information regarding whether renal or cardiac anomalies occur in MRT84 [1–6].
* **P05:** **Cannot rule in or rule out.** The patient has mild intellectual disability and global developmental delay [1, 2, 6], along with dysmorphic/craniofacial features (Pierre-Robin sequence) [1]. However, the patient has macrocephaly and lacks short stature [1], though the sources do not explicitly state whether macrocephaly excludes MRT84 [1–6].
* **P06:** **Cannot rule in or rule out (unlikely).** The patient has global developmental delay [1], but intellectual disability is not documented [1, 2, 6], and short stature is absent [1]. The sources do not state if GDD alone without ID can represent MRT84 [1–6].
* **P07:** **Cannot rule in or rule out.** The patient displays intellectual disability, developmental delay, and dysmorphic facial features (micrognathia, retrognathia) [1, 2, 6], but lacks short stature [1]. The sources do not state whether short stature is an obligate feature [1].
* **P08:** **Cannot rule in or rule out (unlikely).** The patient has severe global developmental delay without a stated diagnosis of intellectual disability, whereas sources define MRT84 by mild to moderate intellectual disability [2, 6]. 
* **P09:** **Ruled out (highest discordance).** The patient has *tall stature*, which directly contradicts the clinical description of MRT84 as characterized by *short stature* [1].
* **P10:** **Cannot rule in or rule out.** The patient has mild intellectual disability [2, 6], motor delay (delayed ability to walk) [1], and dysmorphic facial features (mandibular prognathia, thick eyebrow) [1], but lacks short stature [1]. The sources do not clarify whether short stature is obligate [1].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P04** (alternatively **P10**)
  * **Rationale:** P04 demonstrates the core cardinal features explicitly highlighted in the literature: developmental delay [1], intellectual disability [1, 2, 6], and short stature [1]. While P10 possesses dysmorphic facial features and mild intellectual disability [1, 2, 6], P04 captures the short stature characteristic [1].
* **Estimated Probability:** **~25%**
  * **Justification:** Because exactly one of the 10 patients has MRT84 (baseline prior of 10%), and the sources do not provide full phenotypic frequencies or exclusion criteria to definitively differentiate between several partially matching candidates (e.g., P01, P02, P04, P07, P10), confidence remains low-to-moderate.

---

### 3. Missing Facts Needed for Confidence

To establish a definitive diagnosis, the following information is missing from the sources:
1. **Molecular Genetic Data:** Confirmation of biallelic pathogenic or founder variants in the *SGSM3* gene [2, 3, 4, 6].
2. **Ancestry / Demographic Details:** Information on whether the patient is of Ashkenazi Jewish origin, in which a specific founder variant has been identified [2, 6].
3. **Phenotypic Penetrance and Obligate Signs:** Clarification from the sources on whether short stature and dysmorphic facial features are strictly required (obligate) [1] or whether purely non-syndromic intellectual disability is sufficient [3, 5].
4. **Exclusion Criteria and Co-occurring Features:** Data on whether systemic manifestations (e.g., structural heart defects, renal cysts, macrocephaly, or severe intellectual disability) exclude MRT84 [1–6].

--------------------------------------------------------------------------------

### Round 3  (picked: P10)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient-by-Patient Rule In / Rule Out Evaluation

* **P01**: **Cannot be ruled in or ruled out.** The sources state that MRT84 / *SGSM3* is characterized by developmental delay [1] and mild to moderate intellectual disability [2, 6], which matches P01's mild global developmental delay and mild intellectual disability. However, P01 lacks the short stature and dysmorphic facial features described in [1]. Furthermore, the sources do not mention camptodactyly, scoliosis, lumbar hyperlordosis, micropenis, hypothyroidism, anxiety, or pes cavus, nor do they provide exclusion criteria for them [1–6].
* **P02**: **Cannot be ruled in or ruled out.** P02 exhibits intellectual disability, global developmental delay, motor delay, speech delay, and autistic behavior, aligning with developmental delay [1], intellectual disability [1, 2, 6], and the classification of *SGSM3* as a gene for nonsyndromic intellectual disability [5]. However, the sources do not report phimosis or autistic behavior, nor does P02 report short stature or dysmorphic facial features [1].
* **P03**: **Ruled out (incompatible).** P03 has "Severe intellectual disability," which contradicts the sources that explicitly define MRT84 / *SGSM3* as a disorder with "mild to moderate intellectual disability" [2, 6]. Additionally, the sources do not document structural brain anomalies (hypoplasia of the corpus callosum), congenital heart defects, or hypotonia [1–6].
* **P04**: **Cannot be ruled in or ruled out.** P04 has global developmental delay, short stature, and intellectual disability, which match key features in [1]. However, P04's degree of intellectual disability is not specified (sources specify mild to moderate [2, 6]), dysmorphic facial features are not described [1], and the sources do not document renal cysts, hydronephrosis, microcephaly, hearing impairment, seizures, or congenital heart defects (PDA, VSD) [1–6].
* **P05**: **Cannot be ruled in or ruled out.** P05 has mild intellectual disability [2, 6] and global developmental delay [1]. While Pierre-Robin sequence could represent dysmorphic facial features [1], the sources do not mention macrocephaly, cafe-au-lait spots, or fever, nor do they state whether macrocephaly is exclusionary in relation to short stature [1–6].
* **P06**: **Ruled out (incompatible).** P06 does not have documented intellectual disability (only global developmental delay), whereas MRT84 is fundamentally defined as an intellectual developmental disorder / intellectual disability [1, 2, 3, 4, 5, 6]. In addition, the sources do not describe cardiac (VSD), renal (hydronephrosis), or skeletal (hallux valgus) involvement [1–6].
* **P07**: **Cannot be ruled in or ruled out.** P07 has intellectual disability [1, 2, 6], developmental/motor/speech delay [1], and dysmorphic facial features (micrognathia, retrognathia) [1]. However, short stature is not documented [1], the severity of intellectual disability is unspecified [2, 6], and the sources do not mention spasticity, pectus excavatum, or anxiety [1–6].
* **P08**: **Ruled out (incompatible).** P08 has severe global developmental delay and no documented intellectual disability, conflicting with the mild to moderate intellectual disability phenotype [2, 6]. Brain malformations (simplified gyral pattern, small posterior fossa) are also not mentioned in the sources [1–6].
* **P09**: **Ruled out (incompatible).** P09 has "Tall stature," which directly contradicts the clinical description in [1] stating that MRT84 is characterized by "short stature." 
* **P10**: **Cannot be ruled in or ruled out.** P10 matches the specific severity of "mild intellectual disability" [2, 6], delayed ability to walk / developmental delay [1], and dysmorphic facial features (mandibular prognathia, thick eyebrow) [1]. However, short stature is not reported [1], and the sources do not mention seizures, obsessive-compulsive traits, or myopia [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P10** (alternatively **P04**)
  * **Rationale:** P10 aligns directly with the explicit severity of "mild intellectual disability" [2, 6], developmental delay [1], and dysmorphic facial features [1]. (P04 is also a plausible candidate because it exhibits developmental delay, intellectual disability, and short stature [1], but its ID severity is unstated and it lacks dysmorphic facial features [1]). 
* **Estimated Probability:** **~30%**
  * *Reasoning:* Because the sources do not provide genetic data, complete clinical profiles, or penetrance figures for features like short stature or dysmorphic features [1–6], definitive distinction between P10, P04, P01, P02, P05, and P07 is impossible. P10 is marginally more consistent with the combined mild ID and dysmorphic features mentioned across [1], [2], and [6].

---

### 3. Facts Needed (and Not in the Sources) to Be Confident

1. **Molecular Genetic Data:** Confirmation of homozygous or compound heterozygous pathogenic variants in the *SGSM3* gene [2, 3, 4, 5, 6].
2. **Family History and Ancestry:** Information regarding consanguinity, autosomal recessive inheritance [1, 2, 6], or Ashkenazi Jewish founder variant status [2, 3, 6].
3. **Exhaustive Phenotypic Spectrum:** A detailed clinical summary defining the penetrance of short stature and facial dysmorphisms [1], and detailing whether systemic anomalies (e.g., cardiac, renal, neurological, or ocular) can occur or are exclusionary [1–6].
4. **Specified Severity of ID:** Explicit specification of whether intellectual disability is mild, moderate, or severe in patients where it is currently uncharacterized (e.g., P04, P07) [2, 6].

--------------------------------------------------------------------------------

picks across rounds: ['P03', 'P04', 'P10']
