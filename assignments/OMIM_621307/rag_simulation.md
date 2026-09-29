# Plain RAG on Alsahan-Harris syndrome (TBC1D32, OMIM:621307)
model: gemini-3.8-flash   generated: 2026-09-28 20:52

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `TBC1D32 gene Alsahan-Harris syndrome`

[1] **Entry - #621307 - ALSAHAN-HARRIS SYNDROME; ALHAS**  
    https://omim.org/entry/621307  
    Alsahan-Harris syndrome (ALHAS) is caused by homozygous or compound heterozygous mutation in the TBC1D32 gene (615867) on chromosome 6q22.

[2] **TBC1D32 gene TBC1 Domain Family Member 32**  
    https://www.genecards.org/card/TBC1D32  
    Diseases associated with TBC1D32 include Orofaciodigital Syndrome Ix and Alsahan-Harris Syndrome. Among its related pathways is Ciliopathies.

[3] **Diagnosis of TBC1D32-associated conditions - PMC - NIH**  
    https://pmc.ncbi.nlm.nih.gov/articles/PMC10204718/  
    by SC Harris · 2023 · Cited by 11 — TBC1D32, encoding TBC1 domain family member 32, as a candidate causal gene in a simplex patient associated with a severe ciliopathy phenotype. ...

[4] **TBC1D32**  
    https://panelapp.genomicsengland.co.uk/panels/entities/TBC1D32  
    TBC1D32-related ciliopathy · Orofaciodigital syndrome IX, OMIM:258865 · orofaciodigital syndrome IX, MONDO:0009795 · Alsahan-Harris syndrome, OMIM:621307 · Alsahan- ...

[5] **615867 - TBC1 DOMAIN FAMILY, MEMBER 32; TBC1D32**  
    https://omim.org/entry/615867  
    TBC1D32 is predicted to play a role in ciliary morphology. ALSAHAN-HARRIS SYNDROME TBC1D32, died immediately after birth with hydrocephaly, anophthalmia, ...

[6] **Diagnosis of TBC1D32‐associated conditions: Expanding ...**  
    https://onlinelibrary.wiley.com/doi/abs/10.1002/ajmg.a.63150  
    by SC Harris · 2023 · Cited by 11 — TBC1D32 is involved in the development and function of cilia and is expressed in the developing hypothalamus and pituitary gland.

## 2. The context handed to the model
```
[1] Entry - #621307 - ALSAHAN-HARRIS SYNDROME; ALHAS
https://omim.org/entry/621307
Alsahan-Harris syndrome (ALHAS) is caused by homozygous or compound heterozygous mutation in the TBC1D32 gene (615867) on chromosome 6q22.

[2] TBC1D32 gene TBC1 Domain Family Member 32
https://www.genecards.org/card/TBC1D32
Diseases associated with TBC1D32 include Orofaciodigital Syndrome Ix and Alsahan-Harris Syndrome. Among its related pathways is Ciliopathies.

[3] Diagnosis of TBC1D32-associated conditions - PMC - NIH
https://pmc.ncbi.nlm.nih.gov/articles/PMC10204718/
by SC Harris · 2023 · Cited by 11 — TBC1D32, encoding TBC1 domain family member 32, as a candidate causal gene in a simplex patient associated with a severe ciliopathy phenotype. ...

[4] TBC1D32
https://panelapp.genomicsengland.co.uk/panels/entities/TBC1D32
TBC1D32-related ciliopathy · Orofaciodigital syndrome IX, OMIM:258865 · orofaciodigital syndrome IX, MONDO:0009795 · Alsahan-Harris syndrome, OMIM:621307 · Alsahan- ...

[5] 615867 - TBC1 DOMAIN FAMILY, MEMBER 32; TBC1D32
https://omim.org/entry/615867
TBC1D32 is predicted to play a role in ciliary morphology. ALSAHAN-HARRIS SYNDROME TBC1D32, died immediately after birth with hydrocephaly, anophthalmia, ...

[6] Diagnosis of TBC1D32‐associated conditions: Expanding ...
https://onlinelibrary.wiley.com/doi/abs/10.1002/ajmg.a.63150
by SC Harris · 2023 · Cited by 11 — TBC1D32 is involved in the development and function of cilia and is expressed in the developing hypothalamus and pituitary gland.
```

## 3. The gene, from the sources

The *TBC1D32* gene, located on chromosome 6q22, encodes the protein TBC1 domain family member 32 [1, 2, 3]. In the cell, TBC1D32 is involved in the development and function of cilia and is predicted to play a role in ciliary morphology [5, 6]. The gene is also expressed in the developing hypothalamus and pituitary gland, and its related cellular pathways include ciliopathies [2, 6]. 

Variants in *TBC1D32* disrupt these normal functions, acting as causal factors in severe ciliopathy phenotypes [3, 4]. Specifically, homozygous or compound heterozygous mutations in *TBC1D32* cause Alsahan-Harris syndrome [1]. In cases of Alsahan-Harris syndrome, these genetic changes can lead to severe developmental defects, including hydrocephaly and anophthalmia, and can result in death immediately after birth [5]. Additionally, *TBC1D32* mutations are associated with another ciliopathy termed orofaciodigital syndrome IX [2, 4].

*tokens in 646, out 1916*

## 4. The gene, closed book (no sources; beware hallucinations)

and Harris..." or "Al-Sahan and Harris"?
            Wait! What if the year was 2004?
            Wait, let's think about: Is there a paper by Al-Sahan and Harris?
            Wait, what if it's "Al-Sahan, L. D., Harris, D. J."? No, what about "Al-Sahan, L."?
            Let's search: Is there a paper titled: "New syndrome..." or similar?
            Wait, what if the paper is:
            Al-Sahan, ... Harris, ... (year)?
            Could it be: "Al-Sahan and Harris (2004)"?
            Wait,

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P08)

Based on the provided sources, here is the clinical genetic assessment:

### 1. Patient Evaluation (Rule-In / Rule-Out)

The sources establish that Alsahan-Harris syndrome (ALHAS) is caused by homozygous or compound heterozygous mutations in *TBC1D32* [1], is part of the ciliopathy spectrum [2, 3, 4], has been described with neonatal death, hydrocephaly, and anophthalmia [5], and involves a gene expressed in the developing hypothalamus and pituitary gland [6]. 

Because the provided excerpts do not provide an exhaustive clinical synopsis, universal diagnostic criteria, or negative exclusion criteria for ALHAS, **the sources do not contain enough information to definitively rule in or rule out any single patient with certainty** [1–6]. However, comparing their presentations against the limited facts in the sources yields the following:

* **P01:** Cannot be definitively ruled in or out. The sources do not mention brachydactyly, hemivertebrae, or microtia in ALHAS [1–6], and P01 lacks anophthalmia or hydrocephaly [5] as well as hypothalamic/pituitary involvement [6].
* **P02:** Cannot be definitively ruled in or out. P02 presents with features of a ciliopathy (molar tooth sign, polydactyly, rod-cone dystrophy) [2, 3], but lacks anophthalmia or hydrocephaly [5] and hypothalamic/pituitary findings [6].
* **P03:** Cannot be definitively ruled in or out. P03 lacks any of the specific ALHAS features mentioned in the text (such as anophthalmia or hydrocephaly [5], or pituitary/hypothalamic involvement [6]).
* **P04:** Cannot be definitively ruled in or out. Camptodactyly, osteosclerosis, and hearing loss are not mentioned in connection with ALHAS [1–6], and P04 lacks anophthalmia, hydrocephaly [5], or pituitary involvement [6].
* **P05:** Cannot be definitively ruled in or out. Shows midline and limb defects (encephalocele, bifid nose, polydactyly) consistent with a ciliopathy [2, 3], but lacks anophthalmia [5] or pituitary/hypothalamic findings [6].
* **P06:** Cannot be definitively ruled in or out. P06 has extensive hypothalamic and pituitary deficiencies, an absent pituitary stalk, and an ectopic posterior pituitary, which align with *TBC1D32* expression in the developing hypothalamus and pituitary gland [6]. However, P06 has prominent orofaciodigital features (lobulated tongue, accessory frenulum, polydactyly) which align with Orofaciodigital syndrome IX (another *TBC1D32*-associated condition [2, 4]) and lacks anophthalmia [5].
* **P07:** Cannot be definitively ruled in or out. P07 exhibits oral and digital/cranial features of an orofaciodigital ciliopathy [2, 3, 4], but lacks anophthalmia or hydrocephaly [5] and hypothalamic/pituitary features [6].
* **P08:** Cannot be definitively ruled in or out. However, P08 has **anophthalmia**, which is explicitly documented in ALHAS [5], **abnormal sella turcica morphology**, which corresponds to the pituitary/hypothalamic localization of *TBC1D32* [6], and **situs inversus totalis**, a classic severe ciliopathy phenotype [2, 3]. It lacks documented hydrocephaly [5].
* **P09:** Cannot be definitively ruled in or out. Displays molar tooth sign and respiratory irregularities indicative of a ciliopathy [2, 3], but lacks anophthalmia, hydrocephaly [5], or hypothalamic/pituitary defects [6].
* **P10:** Cannot be definitively ruled in or out. P10 has **hydrocephalus**, which is explicitly documented in ALHAS [5], but lacks anophthalmia [5] and pituitary/hypothalamic findings [6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P08**
* **Estimated Probability:** **80%** (with P06 and P10 being the primary alternatives at ~10% each).
  * *Reasoning:* P08 is the only patient presenting with **anophthalmia** (a specific feature highlighted for ALHAS in [5]) alongside **abnormal sella turcica morphology** (the sella turcica houses the pituitary gland, aligning directly with *TBC1D32* expression in the pituitary/hypothalamus [6]) and **situs inversus totalis** (consistent with a severe ciliopathy [2, 3]). While P10 has hydrocephalus [5] and P06 has pituitary hormone deficiencies [6], P08 has the most specific combination of ALHAS features referenced in the sources [5, 6].

---

### 3. Facts Needed to Be Confident (Not Provided in the Sources)

1. **Genetic Confirmation:** Information on whether the patient carries homozygous or compound heterozygous mutations in *TBC1D32* [1].
2. **Complete Clinical Spectrum and Diagnostic Criteria:** The full list of clinical signs defining Alsahan-Harris syndrome (ALHAS), as the sources only mention hydrocephaly and anophthalmia in a single patient who died immediately after birth [5].
3. **Phenotypic Differentiation Between Related Conditions:** Explicit clinical criteria to distinguish ALHAS from Orofaciodigital syndrome IX, both of which are associated with *TBC1D32* [2, 4].
4. **Additional Clinical History for P08:** Whether P08 had hydrocephaly, central endocrine/pituitary dysfunction, or early neonatal lethality [5, 6].

--------------------------------------------------------------------------------

### Round 2  (picked: P06)

Based on the provided sources, here is the clinical genetic assessment:

---

### 1. Rule In / Rule Out Evaluation for Each Patient

Strictly using the provided sources, **no patient can be definitively ruled in or ruled out**. The sources do not provide full clinical diagnostic criteria, exclusion criteria, or the genetic test results required to confirm or exclude Alsahan-Harris syndrome (which requires homozygous or compound heterozygous mutations in *TBC1D32*) [1]. 

* **P01**: **Cannot rule in or rule out.** The patient exhibits oral anomalies (bifid tongue), which is seen in orofaciodigital spectrum disorders related to *TBC1D32* [2], but lacks specific features noted in [5] (hydrocephaly, anophthalmia) or [6] (hypothalamic-pituitary defects). The sources do not establish mandatory features or rule-out criteria [1–6].
* **P02**: **Cannot rule in or rule out.** Exhibits ciliopathy features (molar tooth sign, rod-cone dystrophy, polydactyly) consistent with *TBC1D32* being involved in ciliary function/pathways [2, 3, 5], but lacks genetic confirmation [1] and specific features from [5, 6].
* **P03**: **Cannot rule in or rule out.** Presents with non-specific neurodevelopmental symptoms; the sources do not provide information to confirm or exclude this presentation [1–6].
* **P04**: **Cannot rule in or rule out.** Has craniofacial and digital findings, but the sources provide no data to link or exclude these specific features [1–6].
* **P05**: **Cannot rule in or rule out.** Shows structural brain/cranial defects (encephalocele) and polydactyly broadly consistent with ciliopathies [2, 3], but lacks specific genetic or clinical data matching [1, 5, 6].
* **P06**: **Cannot rule in or rule out (Strongest candidate).** Shows extensive hypothalamic and pituitary deficiencies (absent stalk, ectopic posterior pituitary, multiple hormone deficiencies), aligning directly with *TBC1D32* expression in the developing hypothalamus and pituitary gland [6]. In addition, the patient exhibits polydactyly and oral features (lobulated tongue, accessory oral frenulum, cleft palate), aligning with *TBC1D32*-associated Orofaciodigital Syndrome and ciliopathies [2, 3, 4]. However, definitive rule-in is not possible without genetic testing [1] or complete diagnostic criteria [1–6].
* **P07**: **Cannot rule in or rule out.** Shows oral anomalies (lobulated/bifid tongue, accessory frenulum) consistent with the orofaciodigital spectrum [2], but lacks genetic data [1] and the specific features mentioned in [5, 6].
* **P08**: **Cannot rule in or rule out.** Has anophthalmia (explicitly reported in an individual with Alsahan-Harris syndrome in [5]) and abnormal sella turcica morphology (consistent with pituitary region involvement [6]), but hydrocephaly [5] is absent, and genetic confirmation is lacking [1].
* **P09**: **Cannot rule in or rule out.** Displays molar tooth sign and respiratory irregularities characteristic of ciliopathies [2, 3], but the sources do not mention these features for *TBC1D32* specifically [1–6].
* **P10**: **Cannot rule in or rule out.** Displays hydrocephalus, which is noted in Alsahan-Harris syndrome [5], but lacks anophthalmia [5] and genetic confirmation [1].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P06**
* **Estimated Probability:** **~65%** 
  * *Rationale:* Source [6] explicitly highlights that *TBC1D32* is expressed in the developing hypothalamus and pituitary gland [6], explaining the profound congenital hypopituitarism present in P06 (absent pituitary stalk, ectopic posterior pituitary, multi-axis hormone deficiencies). Furthermore, *TBC1D32* is associated with Orofaciodigital Syndrome [2, 4] and severe ciliopathies [3], matching P06’s polydactyly, lobulated tongue, cleft palate, and accessory frenula. (P08 is an alternative candidate due to anophthalmia [5] and sella turcica abnormality [6], accounting for much of the remaining probability).

---

### 3. Facts Needed (and Missing) to Be Confident

1. **Molecular Genetic Data:** Confirmation of biallelic (homozygous or compound heterozygous) pathogenic variants in the *TBC1D32* gene on chromosome 6q22 for the candidate patient [1].
2. **Complete Phenotypic Spectrum & Diagnostic Criteria:** The provided sources only provide fragmented mentions (e.g., text truncations ending in ellipses for hydrocephaly and anophthalmia [5], and brief mentions of pituitary/hypothalamic expression [6]). A complete clinical description of Alsahan-Harris syndrome is absent.
3. **Phenotypic Delineation between *TBC1D32* Alleles:** Clarification on how Alsahan-Harris syndrome clinically differs from or overlaps with Orofaciodigital Syndrome IX, both of which are linked to *TBC1D32* [2, 4].
4. **Alternative Diagnoses:** Genetic and clinical details to definitively exclude the other 9 patients from having *TBC1D32* mutations [1].

--------------------------------------------------------------------------------

### Round 3  (picked: P06)

### 1. Patient Evaluation (Rule-In / Rule-Out)

Under the provided sources, Alsahan-Harris syndrome (ALHAS) is caused by homozygous or compound heterozygous mutations in *TBC1D32* [1], which is implicated in ciliopathies [2, 3, 4], expressed in the developing hypothalamus and pituitary gland [6], and reported in a patient who died immediately after birth with hydrocephaly and anophthalmia [5]. 

**Important limitation across all patients:** None of the patient descriptions include genetic variant data (homozygous or compound heterozygous *TBC1D32* mutations [1]), nor do the sources provide a complete list of necessary, sufficient, or exclusionary clinical criteria [1–6]. Therefore, **no patient can be definitively ruled in, and no patient can be definitively ruled out** based solely on these sources [1–6].

* **P01:** Cannot be ruled in or ruled out. The source mentions TBC1D32 is associated with orofaciodigital syndrome IX and ciliopathies [2, 4], which share oral/skeletal features (e.g., bifid tongue), but the sources do not list specific criteria to rule P01 in or out [1–6].
* **P02:** Cannot be ruled in or ruled out. The patient has ciliopathy features (molar tooth sign, polydactyly) [2, 3], but the sources do not specify whether Joubert/cerebellar vermis features exclude or include ALHAS [1–6].
* **P03:** Cannot be ruled in or ruled out. Lacks specific features noted in the sources such as hydrocephaly, anophthalmia [5], or pituitary/hypothalamic defects [6], but the sources do not provide exclusionary criteria to rule P03 out [1–6].
* **P04:** Cannot be ruled in or ruled out. Features oral/craniofacial and digital anomalies [2], but lacks genetic or definitive clinical criteria in the sources to rule in or out [1–6].
* **P05:** Cannot be ruled in or ruled out. Displays ciliopathy-like features (encephalocele, polydactyly) [2, 3], but lacks the specific findings mentioned in [5] or [6], and no exclusionary criteria are provided [1–6].
* **P06:** Cannot be ruled in or ruled out. Demonstrates extensive hypothalamic and pituitary abnormalities (absent stalk, ectopic posterior pituitary, multiple hormone deficiencies), which strongly aligns with *TBC1D32* expression in the developing hypothalamus and pituitary gland [6], along with polydactyly and oral anomalies compatible with ciliopathy/orofaciodigital syndrome spectrum [2, 3, 4]. However, the sources do not confirm whether these specific features suffice to diagnose ALHAS [1–6].
* **P07:** Cannot be ruled in or ruled out. Presents with oral features (lobulated/bifid tongue, accessory frenulum) consistent with orofaciodigital spectrum disorders [2, 4], but the sources do not supply criteria to rule P07 in or out [1–6].
* **P08:** Cannot be ruled in or ruled out. Features **anophthalmia**, matching the description in [5], and **abnormal sella turcica morphology**, consistent with pituitary/hypothalamic involvement [6]. However, hydrocephaly is not mentioned, the description in [5] is truncated ("..."), and no genetic confirmation is provided [1, 5].
* **P09:** Cannot be ruled in or ruled out. Shows ciliopathy features (molar tooth sign) [2, 3], but the sources do not provide data to confirm or exclude ALHAS [1–6].
* **P10:** Cannot be ruled in or ruled out. Features **hydrocephalus**, matching the description in [5], but lacks anophthalmia [5] and genetic data [1].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P06** (or alternatively **P08**)
  * *P06* is the most biologically cohesive candidate under [6], [2], and [4]: P06 exhibits severe multi-lineage hypothalamic-pituitary dysfunction (absent stalk, ectopic posterior pituitary, LHRH, ACTH, GH, and TSH deficiencies), directly matching the specific finding that *TBC1D32* is expressed in the developing hypothalamus and pituitary gland [6], combined with postaxial/preaxial polydactyly, lobulated tongue, and oral frenula consistent with *TBC1D32*-related orofaciodigital/ciliopathy phenotypes [2, 3, 4].
  * *P08* is also a strong candidate due to the explicit mention of **anophthalmia** in ALHAS [5] and **abnormal sella turcica** (pituitary fossa) [6].
* **Estimated Probability:** **~45% for P06** (and ~40% for P08, with ~15% distributed across other candidates).
  * *Reasoning:* A higher certainty is not clinically justifiable because the sources do not provide complete clinical criteria, do not distinguish whether ALHAS is defined strictly by the neonatal lethal presentation in [5] versus the broader endocrine/ciliary phenotype in [6], and omit molecular confirmation for all patients [1].

---

### 3. Missing Facts Needed for Confidence

To establish a definitive diagnosis, the following information (not provided in the sources) is required:
1. **Molecular Genetic Confirmation:** Identification of biallelic (homozygous or compound heterozygous) pathogenic variants in *TBC1D32* in the patient [1].
2. **Complete Clinical Definition of ALHAS:** The complete, untruncated phenotype of Alsahan-Harris syndrome (entry #621307) beyond the truncated snippet in [5] ("died immediately after birth with hydrocephaly, anophthalmia, ...").
3. **Phenotypic Delineation vs. Related Ciliopathies:** Criteria delineating Alsahan-Harris syndrome from Orofaciodigital Syndrome IX and other *TBC1D32*-related ciliopathies [2, 4], including whether survival past birth and pituitary hormone deficiencies are formal components of ALHAS [5, 6].
4. **Patient Natural History:** Age at examination and survival status of the patients (e.g., whether death occurred immediately after birth [5]).

--------------------------------------------------------------------------------

picks across rounds: ['P08', 'P06', 'P06']
