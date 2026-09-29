# Plain RAG on Intellectual developmental disorder, autosomal dominant 73 (TAF4, OMIM:620450)
model: gemini-3.8-flash   generated: 2026-09-28 20:47

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `TAF4 gene Intellectual developmental disorder, autosomal dominant 73`

[1] **620450 - INTELLECTUAL DEVELOPMENTAL DISORDER ...**  
    https://omim.org/entry/620450  
    autosomal dominant intellectual developmental disorder-73 (MRD73) is caused by heterozygous mutation in the TAF4 gene (601796) on chromosome 20q13.

[2] **Intellectual Developmental Disorder, Autosomal Dominant 73**  
    https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_73  
    The disorder has material basis in heterozygous mutation in the TAF4 gene on chromosome 20q13. Clinical presentation is described as autosomal dominant and ...

[3] **Intellectual developmental disorder, autosomal dominant 73**  
    https://www.uniprot.org/diseases/DI-06716  
    An autosomal dominant disorder characterized by intellectual disability ranging from mild to severe, developmental delay, speech delay, behavioral abnormalities ...

[4] **Diseases associated with TAF4**  
    https://platform.opentargets.org/target/ENSG00000130699/associations  
    Ranked list of diseases and phenotypes associated with TAF4. TAF4 Associated diseases Profile Europe PMC Expression Atlas IMPC Weight Include ?

[5] **autosomal dominant intellectual developmental disorder 73**  
    http://www.alliancegenome.org/disease/DOID:0061046  
    An autosomal dominant intellectual developmental disorder characterized by impaired intellectual development that ranges from mild to severe, speech delay, ...

[6] **TAF4 Gene | AI-Powered Variant Analysis Platform - RDDC**  
    https://rddc.tsinghua-gd.org/disease/INT604  
    Autosomal Dominant 73, is also known as taf4-related neurodevelopmental disorder. An important gene associated with Intellectual Developmental Disorder, ...

## 2. The context handed to the model
```
[1] 620450 - INTELLECTUAL DEVELOPMENTAL DISORDER ...
https://omim.org/entry/620450
autosomal dominant intellectual developmental disorder-73 (MRD73) is caused by heterozygous mutation in the TAF4 gene (601796) on chromosome 20q13.

[2] Intellectual Developmental Disorder, Autosomal Dominant 73
https://www.malacards.org/card/intellectual_developmental_disorder_autosomal_dominant_73
The disorder has material basis in heterozygous mutation in the TAF4 gene on chromosome 20q13. Clinical presentation is described as autosomal dominant and ...

[3] Intellectual developmental disorder, autosomal dominant 73
https://www.uniprot.org/diseases/DI-06716
An autosomal dominant disorder characterized by intellectual disability ranging from mild to severe, developmental delay, speech delay, behavioral abnormalities ...

[4] Diseases associated with TAF4
https://platform.opentargets.org/target/ENSG00000130699/associations
Ranked list of diseases and phenotypes associated with TAF4. TAF4 Associated diseases Profile Europe PMC Expression Atlas IMPC Weight Include ?

[5] autosomal dominant intellectual developmental disorder 73
http://www.alliancegenome.org/disease/DOID:0061046
An autosomal dominant intellectual developmental disorder characterized by impaired intellectual development that ranges from mild to severe, speech delay, ...

[6] TAF4 Gene | AI-Powered Variant Analysis Platform - RDDC
https://rddc.tsinghua-gd.org/disease/INT604
Autosomal Dominant 73, is also known as taf4-related neurodevelopmental disorder. An important gene associated with Intellectual Developmental Disorder, ...
```

## 3. The gene, from the sources

The *TAF4* gene is located on chromosome 20q13 and is directly associated with autosomal dominant intellectual developmental disorder-73 (MRD73), a condition also known as TAF4-related neurodevelopmental disorder [1, 2, 6]. This condition is an autosomal dominant disorder characterized by developmental delay, speech delay, behavioral abnormalities, and impaired intellectual development that ranges from mild to severe [2, 3, 5]. Genetically, the disorder is caused by and has its material basis in heterozygous mutations in the *TAF4* gene [1, 2]. 

However, the provided sources do not cover what the specific *TAF4* gene product is or what functional role it performs within the cell [1, 2, 3, 4, 5, 6]. Furthermore, beyond identifying heterozygous mutations as the cause of the disorder, the sources do not provide details on the specific cellular or biological mechanisms of how these variants cause disease [1, 2].

*tokens in 504, out 1567*

## 4. The gene, closed book (no sources; beware hallucinations)

**Gene Product and Function**  
The *TAF4* gene encodes TATA-box binding protein (TBP)-associated factor 4, an essential core subunit of the general transcription factor complex TFIID. TFIID is critical for RNA polymerase II-mediated transcription initiation across protein-coding genes. Within this complex, TAF4 forms a heterodimer with TAF12 through their conserved histone-fold domains (HFD), functioning as a structural scaffold that stabilizes TFIID core assembly and facilitates promoter recognition and enhancer–promoter communication.

**Disease Mechanism**  
Heterozygous *de novo* variants in *TAF4*—predominantly missense mutations in conserved domains (such as the HFD or TAFH domain) or loss-

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P07)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources define Intellectual developmental disorder, autosomal dominant 73 (MRD73; OMIM 620450) as being caused by heterozygous mutations in the *TAF4* gene on chromosome 20q13 [1, 2] and characterize it broadly by:
* Intellectual disability (ranging from mild to severe) [3, 5]
* Developmental delay [3]
* Speech delay [3, 5]
* Behavioral abnormalities [3]

The sources do not provide any detailed dysmorphic features, systemic findings, or negative exclusion criteria [1–6].

* **P01:** **Cannot be ruled in or definitively ruled out.** P01 lacks any documented intellectual disability, developmental delay, or speech delay (which characterize the condition [3, 5]), making it clinically inconsistent with the description; however, the sources do not state definitive exclusion criteria [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits global developmental delay, speech delay, and intellectual disability [3, 5], but the sources lack the phenotypic detail needed to confirm or exclude this specific presentation [1–6].
* **P03:** **Cannot be ruled in or definitively ruled out.** P03 lacks explicit intellectual disability, developmental delay, or speech delay [3, 5], but the sources do not provide exclusion criteria [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has global developmental delay and intellectual disability [3, 5], but the sources provide no information to confirm or exclude this complex multi-system presentation [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has intellectual disability, global developmental delay, and delayed speech [3, 5], but cannot be differentiated or confirmed using the provided sources [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 has behavioral abnormalities (ADHD, autistic behavior) [3], but lacks documented intellectual disability or speech delay [3, 5]. The sources do not provide sufficient detail to rule P06 in or out [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 possesses global developmental delay, intellectual disability, speech delay, and a behavioral abnormality (impulsivity) [3, 5]. However, the sources lack specific clinical features to confirm or exclude this patient [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 possesses intellectual disability, motor and speech delays, and behavioral abnormalities (ADHD, autistic behavior) [3, 5], but the sources provide no specific features to confirm or exclude this patient [1–6].
* **P09:** **Cannot be ruled in or definitively ruled out.** P09 shows features of a RASopathy/Noonan-like disorder with leukemia and lacks intellectual disability, developmental delay, or speech delay [3, 5]. While highly discordant with the description, the sources provide no formal exclusion criteria [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 possesses intellectual disability, motor delay, speech delay, and behavioral traits (excessive shyness) [3, 5], but the sources lack the granular phenotypic criteria necessary to confirm or exclude this patient [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P07** (tied with **P08** and **P10**)
  * *Reasoning:* P07, P08, and P10 are the only candidates who exhibit all four core features documented in the sources: intellectual disability [3, 5], developmental delay [3], speech delay [3, 5], and behavioral abnormalities [3]. Because the sources provide zero distinguishing clinical details beyond these four non-specific neurodevelopmental terms [1–6], none of these three can be prioritized over the others using the text provided.
* **Probability:** **~33%** (1 in 3) among the top clinical matches (P07, P08, P10), or **~10% to 17%** if evaluated across all patients exhibiting intellectual disability/developmental delay.

---

### 3. Missing Information Needed for Confidence

To establish a definitive diagnosis, the following information is required but missing from the sources:
1. **Molecular Genetic Data:** The presence or absence of a confirmed heterozygous pathogenic variant in the *TAF4* gene on chromosome 20q13 [1, 2].
2. **Granular Phenotypic Profile / HPO Terms:** Detailed clinical data describing the specific craniofacial dysmorphisms, central nervous system anomalies, skeletal features, and systemic manifestations associated with *TAF4*-related disorder (the text in sources [2], [3], and [5] truncates without detailing these features).
3. **Penetrance and Exclusion Criteria:** Explicit documentation of obligate clinical signs, age-dependent features, or negative findings that permit ruling out alternative neurodevelopmental conditions.

--------------------------------------------------------------------------------

### Round 2  (picked: P07)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule-In / Rule-Out)

The sources define intellectual developmental disorder, autosomal dominant 73 (MRD73 / *TAF4*-related neurodevelopmental disorder) only by broad features: heterozygous mutations in *TAF4* [1, 2], autosomal dominant inheritance [1, 2, 3, 5], intellectual disability ranging from mild to severe [3, 5], developmental delay [3], speech delay [3, 5], and behavioral abnormalities [3]. The sources provide **no** genetic test results, no comprehensive phenotypic profiles, and no exclusion criteria [1–6].

* **P01:** **Cannot be ruled in or ruled out.** P01 lacks explicit mention of intellectual disability, developmental delay, or speech delay, but the sources do not state these are strictly present in every clinical report or provide exclusion criteria [1–6].
* **P02:** **Cannot be ruled in or ruled out.** P02 exhibits intellectual disability, global developmental delay, and delayed speech and language development (consistent with [3, 5]), but the sources provide no data on dysmorphic features (eeverted lower lip vermilion, mandibular prognathia) to confirm or exclude this diagnosis [1–6].
* **P03:** **Cannot be ruled in or ruled out.** P03 lacks developmental/cognitive features listed in the sources, but the sources do not provide exclusionary rules to eliminate P03 [1–6].
* **P04:** **Cannot be ruled in or ruled out.** P04 has global developmental delay and moderate intellectual disability [3, 5], but the sources do not provide information on the extensive dysmorphic, ocular, or skeletal features to rule P04 in or out [1–6].
* **P05:** **Cannot be ruled in or ruled out.** P05 has intellectual disability, global developmental delay, and delayed speech and language development [3, 5], but the sources provide no data regarding connective tissue, skeletal, or craniofacial features to confirm or refute [1–6].
* **P06:** **Cannot be ruled in or ruled out.** P06 presents with behavioral abnormalities (ADHD, autistic behavior) [3] and learning disability, but the sources lack phenotypic detail to determine if this presentation fits MRD73 [1–6].
* **P07:** **Cannot be ruled in or ruled out.** P07 displays global developmental delay, intellectual disability, delayed speech and language development, and behavioral abnormalities (impulsivity), aligning with all features described in [3, 5]. However, the sources lack sufficient detail to definitively confirm the diagnosis [1–6].
* **P08:** **Cannot be ruled in or ruled out.** P08 has mild intellectual disability, delayed speech and language development, delayed walking, and behavioral abnormalities (ADHD, autistic behavior) [3, 5]. While matching the broad clinical synopsis, the sources lack specific clinical or genetic detail to confirm or exclude P08 [1–6].
* **P09:** **Cannot be ruled in or ruled out.** P09 shows no cognitive or developmental delay terms, but the sources provide no exclusionary criteria [1–6].
* **P10:** **Cannot be ruled in or ruled out.** P10 presents with moderate intellectual disability, delayed speech and language development, developmental motor delay, and behavioral features (excessive shyness) [3, 5], but the sources do not provide data to confirm or exclude P10 [1–6].

---

### 2. Most Likely Patient and Probability

* **Most Likely Patient:** **P07** (closely tied with **P08** and **P10**). 
  * *Reasoning:* P07 explicitly matches all core clinical descriptors provided in the sources: global developmental delay [3], intellectual disability [3, 5], delayed speech [3, 5], and behavioral abnormalities (impulsivity) [3]. 
* **Estimated Probability:** **~25–30%**.
  * *Justification:* Because the sources do not provide distinguishing dysmorphic, systemic, or molecular details [1–6], at least four patients (P02, P07, P08, P10) closely fit the non-specific triad/tetrad of intellectual disability, developmental delay, speech delay, and behavioral differences [3, 5]. Distinguishing among them from the provided text alone is impossible.

---

### 3. Missing Facts Needed for Confidence

To make a definitive diagnosis, the following information—which the sources do not provide—is required:
1. **Genotype / Molecular Data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in the *TAF4* gene (chromosome 20q13) for the patient [1, 2].
2. **Comprehensive Clinical Delineation:** A detailed clinical and phenotypic spectrum of MRD73 (including characteristic facial dysmorphisms, brain MRI findings, and neurological manifestations), which is truncated or absent in sources [1–6].
3. **Exclusionary Criteria:** Specific phenotypic features that rule out a *TAF4* diagnosis [1–6].
4. **Alternative Genetic Diagnoses:** Molecular data ruling out other well-characterized syndromic causes for the remaining patients.

--------------------------------------------------------------------------------

### Round 3  (picked: P07)

Based on the provided sources, here is the clinical genetic evaluation:

### 1. Patient Rule-In / Rule-Out Assessment

The provided sources only provide a high-level description: autosomal dominant intellectual developmental disorder-73 (MRD73 / *TAF4*-related neurodevelopmental disorder) is characterized by:
* Intellectual disability ranging from mild to severe [3, 5]
* Developmental delay [3]
* Speech delay [3, 5]
* Behavioral abnormalities [3]

The sources **do not** provide detailed dysmorphic features, systemic manifestations, penetrance rates, exclusion criteria, or patient-specific genetic testing data [1–6]. Consequently, **no patient can be definitively ruled in or ruled out** using these sources alone:

* **P01:** **Cannot rule in or rule out.** P01 lacks documented intellectual disability, developmental delay, or speech delay [3, 5]. However, the sources do not provide exclusion criteria or non-penetrance information to rule P01 out definitively [1–6].
* **P02:** **Cannot rule in or rule out.** P02 has global developmental delay, delayed speech and language development, and intellectual disability [3, 5], but lacks behavioral abnormalities [3]. The sources do not provide specific phenotypic or genetic criteria to confirm or exclude P02 [1–6].
* **P03:** **Cannot rule in or rule out.** P03 lacks explicit intellectual disability, developmental delay, or speech delay [3, 5], but the sources provide no exclusionary criteria [1–6].
* **P04:** **Cannot rule in or rule out.** P04 has global developmental delay and moderate intellectual disability [3, 5], but lacks explicit speech delay or behavioral abnormalities. The sources lack detailed discriminatory criteria [1–6].
* **P05:** **Cannot rule in or rule out.** P05 has global developmental delay, intellectual disability, and delayed speech and language development [3, 5], but the sources lack granular clinical descriptions to rule P05 in or out [1–6].
* **P06:** **Cannot rule in or rule out.** P06 has behavioral abnormalities (ADHD, autistic behavior) [3], but lacks intellectual disability, developmental delay, or speech delay [3, 5]. The sources do not specify whether intellectual disability is mandatory in 100% of cases [1–6].
* **P07:** **Cannot rule in or rule out.** P07 matches all four cardinal features reported across the sources: global developmental delay [3], intellectual disability [3, 5], speech delay ("Delayed speech and language development", "Poor speech") [3, 5], and behavioral abnormalities ("Impulsivity") [3]. However, without molecular data or detailed clinical criteria, P07 cannot be definitively ruled in [1–6].
* **P08:** **Cannot rule in or rule out.** P08 also exhibits developmental delay (delayed walking) [3], mild intellectual disability [3, 5], speech delay [3, 5], and behavioral abnormalities (ADHD, autistic behavior) [3]. The sources lack sufficient clinical detail to rule P08 in or out [1–6].
* **P09:** **Cannot rule in or rule out.** P09 does not report neurodevelopmental phenotypes [3, 5], but the sources do not specify exclusionary criteria [1–6].
* **P10:** **Cannot rule in or rule out.** P10 has developmental delay (delayed walking/sitting) [3], moderate intellectual disability [3, 5], speech delay [3, 5], and potentially behavioral features (excessive shyness) [3]. The sources lack the specific clinical details needed to rule P10 in or out [1–6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P07** (or **P08**)
  * *Reasoning:* P07 explicitly displays every feature identified in the provided sources: intellectual disability [3, 5], global developmental delay [3], delayed speech/language development [3, 5], and behavioral abnormalities (impulsivity) [3].
* **Estimated Probability:** **~25% – 30%**
  * *Context:* The provided sources do not contain specific dysmorphic or organ-system criteria that differentiate P07 from other patients presenting with neurodevelopmental and behavioral phenotypes (such as P08, P10, P02, or P05). Because at least 3–4 patients exhibit overlapping core features, confidence remains low without genetic data.

---

### 3. Facts Needed to Be Confident (Not Available in the Sources)

1. **Molecular Genetic Data:** Confirmation of a heterozygous pathogenic or likely pathogenic variant in the *TAF4* gene on chromosome 20q13 [1, 2, 6].
2. **Detailed Phenotypic Profile:** A full clinical synopsis or complete HPO profile for MRD73 describing the prevalence of craniofacial dysmorphisms, skeletal changes, and neurological/imaging abnormalities [1–6].
3. **Exclusion / Penetrance Criteria:** Clear data on whether core features (e.g., intellectual disability, speech delay) have 100% penetrance, and which features rule out the diagnosis [1–6].

--------------------------------------------------------------------------------

picks across rounds: ['P07', 'P07', 'P07']
