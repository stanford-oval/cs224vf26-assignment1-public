# Plain RAG on Neuronopathy, distal hereditary motor, autosomal dominant 11 (SPTAN1, OMIM:620528)
model: gemini-3.8-flash   generated: 2026-09-28 20:47

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `SPTAN1 gene Neuronopathy, distal hereditary motor, autosomal dominant 11`

[1] **620528 - NEURONOPATHY, DISTAL HEREDITARY ...**  
    https://omim.org/entry/620528  
    autosomal dominant distal hereditary motor neuronopathy-11 (HMND11) is caused by heterozygous mutation in the SPTAN1 gene (182810) on chromosome 9q34.

[2] **Neuronopathy, Distal Hereditary Motor, Autosomal ...**  
    https://www.malacards.org/card/neuronopathy_distal_hereditary_motor_autosomal_dominant_11  
    Autosomal dominant distal hereditary motor neuronopathy 11 (HMND11) is a peripheral axonal motor neuropathy characterized by selective degeneration of motor ...

[3] **Neuronopathy, distal hereditary motor, autosomal dominant 1**  
    https://www.ncbi.nlm.nih.gov/gtr/conditions/C1866784  
    HMND11 (620528), caused by mutation in the SPTAN1 gene (182810); Finding Abnormality of the nervous system

[4] **Autosomal dominant by PanelApp Australia submission ...**  
    https://thegencc.org/submissions/SGC-121328.2  
    SPTAN1 nonsense variant causes hereditary motor neuropathy in a Chinese family. opathy to pure spastic paraplegia and ataxia. to view the public report

[5] **autosomal dominant distal hereditary motor neuronopathy 11**  
    https://xenbase.org/xenbase/showDisease.do?doId=0081400&tabId=0  
    Definition:An autosomal dominant distal hereditary motor neuronopathy that is characterized by juvenile or young-adult onset of distal limb muscle weakness

[6] **SPTAN1**  
    https://www.abcam.com/en-us/targets/sptan1/7046  
    HMND11 is an autosomal dominant form with incomplete penetrance, characterized by juvenile or young-adult onset of distal limb muscle weakness and atrophy

## 2. The context handed to the model
```
[1] 620528 - NEURONOPATHY, DISTAL HEREDITARY ...
https://omim.org/entry/620528
autosomal dominant distal hereditary motor neuronopathy-11 (HMND11) is caused by heterozygous mutation in the SPTAN1 gene (182810) on chromosome 9q34.

[2] Neuronopathy, Distal Hereditary Motor, Autosomal ...
https://www.malacards.org/card/neuronopathy_distal_hereditary_motor_autosomal_dominant_11
Autosomal dominant distal hereditary motor neuronopathy 11 (HMND11) is a peripheral axonal motor neuropathy characterized by selective degeneration of motor ...

[3] Neuronopathy, distal hereditary motor, autosomal dominant 1
https://www.ncbi.nlm.nih.gov/gtr/conditions/C1866784
HMND11 (620528), caused by mutation in the SPTAN1 gene (182810); Finding Abnormality of the nervous system

[4] Autosomal dominant by PanelApp Australia submission ...
https://thegencc.org/submissions/SGC-121328.2
SPTAN1 nonsense variant causes hereditary motor neuropathy in a Chinese family. opathy to pure spastic paraplegia and ataxia. to view the public report

[5] autosomal dominant distal hereditary motor neuronopathy 11
https://xenbase.org/xenbase/showDisease.do?doId=0081400&tabId=0
Definition:An autosomal dominant distal hereditary motor neuronopathy that is characterized by juvenile or young-adult onset of distal limb muscle weakness

[6] SPTAN1
https://www.abcam.com/en-us/targets/sptan1/7046
HMND11 is an autosomal dominant form with incomplete penetrance, characterized by juvenile or young-adult onset of distal limb muscle weakness and atrophy
```

## 3. The gene, from the sources

Autosomal dominant distal hereditary motor neuronopathy-11 (HMND11) is caused by heterozygous mutations in the *SPTAN1* gene located on chromosome 9q34 [1]. Specifically, a nonsense variant in *SPTAN1* has been shown to cause hereditary motor neuropathy [4]. HMND11 manifests as an abnormality of the nervous system and is classified as a peripheral axonal motor neuropathy characterized by selective degeneration of motor structures [2, 3]. Clinically, it is defined by juvenile or young-adult onset of distal limb muscle weakness and atrophy, occurring with incomplete penetrance [5, 6]. 

Regarding the cellular biology, the provided sources do not cover what the specific gene product of *SPTAN1* is or what functional role it performs inside the cell [1, 6]. Furthermore, the detailed biological mechanisms regarding how variants in *SPTAN1* cause disease are not covered beyond the fact that these mutations result in HMND11 [1, 4].

*tokens in 539, out 1732*

## 4. The gene, closed book (no sources; beware hallucinations)

The *SPTAN1* gene encodes **$\alpha$II-spectrin**, a structural scaffolding protein predominantly expressed in the nervous system. $\alpha$II-spectrin pairs with $\beta$-spectrins to assemble heterotetramers that form a periodic subplasmalemmal lattice. This network maintains axonal membrane integrity, stabilizes the axon initial segment and nodes of Ranvier, and facilitates axonal transport.

In **autosomal dominant distal hereditary motor neuronopathy 11 (dHMN11)**, heterozygous missense or small in-frame mutations in *SPTAN1* exert a dominant-negative effect or cause toxic gain of function. These variants impair spectrin tetramerization, disrupt cytoskeletal periodicity, and perturb axonal transport, preferentially leading to length-dependent motor axonal degeneration without primary sensory involvement. 

The disorder was first delineated in **2021**.

**Citation:**  
Beijer, D., et al. (2021). "Defects in *SPTAN1* cause severe neuropathies and distinct neurodevelopmental disorders." *Brain*, 144(9), 2697–2709. doi:10.1093/brain/awab147.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P04)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluations (Rule-In / Rule-Out)

* **P01**: **Cannot rule in, likely ruled out.** The patient shows isolated upper motor neuron/pyramidal signs (spasticity, hyperreflexia, Babinski sign, clonus). Although source [4] notes that *SPTAN1* variants can relate to a spectrum spanning from neuropathy "to pure spastic paraplegia and ataxia" [4], HMND11 itself is specifically defined as a "peripheral axonal motor neuropathy" [2] characterized by distal limb muscle weakness and atrophy [5, 6], which are absent here. The sources do not provide enough context to completely exclude spastic phenotypes under HMND11.
* **P02**: **Ruled out.** The presentation features congenital/developmental brain abnormalities (microcephaly, simplified gyral pattern, severe motor delay) and sensory axonal neuropathy. HMND11 is characterized by selective degeneration of motor neurons [2] and has a juvenile or young-adult onset [5, 6]. 
* **P03**: **Ruled out.** The patient has early developmental delay, dysmorphic/congenital features, and sensory axonal neuropathy. HMND11 is a selective motor neuropathy [2] with juvenile or young-adult onset [5, 6].
* **P04**: **Cannot rule in definitively, but highly consistent.** The patient exhibits "motor axonal neuropathy" [2], "distal limb muscle weakness" (intrinsic hand muscles and distal weakness) [5, 6], and "distal lower limb amyotrophy" [6], without sensory deficits [2]. The sources do not provide genetic data or patient age to confirm the diagnosis [1, 5, 6].
* **P05**: **Ruled out.** The patient has prominent sensory nerve involvement (impaired distal vibration, slowed sensory NCV, motor conduction blocks). HMND11 is defined as an axonal motor neuropathy characterized by selective degeneration of motor fibers [2].
* **P06**: **Ruled out.** The patient shows contractures, spinal rigidity, markedly elevated creatine kinase, and proximal weakness. HMND11 is characterized by distal limb muscle weakness and atrophy [5, 6] resulting from peripheral axonal motor neuropathy [2].
* **P07**: **Cannot rule in definitively, but consistent.** The patient has neuropathic EMG findings, decreased CMAP amplitudes (motor axonal involvement) [2], and distal lower limb muscle weakness and amyotrophy [5, 6]. However, the sources do not provide patient age or genetic confirmation [1, 5, 6].
* **P08**: **Ruled out.** The patient demonstrates widespread multi-modal sensory deficits and decreased sensory action potential amplitudes, which conflicts with HMND11 being a selective motor neuropathy [2].
* **P09**: **Cannot rule in definitively, but partially consistent.** The patient has motor axonal neuropathy [2] and distal lower limb weakness [5], but lacks the muscle atrophy highlighted in the HMND11 definition [6].
* **P10**: **Ruled out.** The patient presents with ptosis, ophthalmoplegia, dysphagia, and proximal weakness, which are inconsistent with a distal hereditary motor neuronopathy [2, 5, 6].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P04**
* **Estimated Probability:** **55%** (with **P07** as the primary differential at ~35%, and **P09** at ~10%).
  * *Reasoning:* P04 matches every defining clinical element provided in the sources: a pure "motor axonal neuropathy" [2] causing "distal limb muscle weakness" involving both upper and lower extremities [5, 6] and "atrophy" [6], without conflicting sensory or cranial nerve findings [2]. P07 is also a viable candidate, but P04 demonstrates classic distal weakness across multiple limb regions (intrinsic hands and lower limbs) alongside atrophy [5, 6].

---

### 3. Facts Needed to Be Confident (Not Provided in the Sources)

The provided sources do not contain:
1. **Genetic confirmation:** Confirmation of a heterozygous pathogenic variant in the *SPTAN1* gene on chromosome 9q34 [1, 3, 4].
2. **Age of onset:** Verification that the patient experienced juvenile or young-adult onset [5, 6].
3. **Family history and inheritance:** Documentation of an autosomal dominant inheritance pattern with possible incomplete penetrance [1, 5, 6].
4. **Disease-specific discriminating criteria:** Detailed clinical or electrophysiological criteria that distinguish HMND11 from other distal hereditary motor neuropathies (e.g., distinguishing P04 from P07 or P09).
5. **Full phenotypic spectrum data:** Complete details regarding whether upper motor neuron signs (suggested in source [4] as "...opathy to pure spastic paraplegia and ataxia") or minor sensory abnormalities can ever be present in HMND11.

--------------------------------------------------------------------------------

### Round 2  (picked: P04)

Based on the provided sources, here is the clinical evaluation of the 10 patients:

### 1. Patient Evaluation (Rule In / Rule Out)

* **P01:** **Cannot be ruled in; likely ruled out.** 
  The patient exhibits pure spasticity/upper motor neuron signs. While source [4] mentions a text fragment linking *SPTAN1* variants from "...opathy to pure spastic paraplegia and ataxia" [4], sources [2], [5], and [6] define HMND11 specifically as a "peripheral axonal motor neuropathy" [2] characterized by "distal limb muscle weakness and atrophy" [5, 6]. P01 lacks peripheral axonal motor neuropathy, muscle weakness, and amyotrophy [2, 5, 6].
* **P02:** **Ruled out.** 
  P02 presents with infantile neurodevelopmental delay, microcephaly, and sensory axonal neuropathy. Source [2] defines HMND11 as characterized by "selective degeneration of motor" neurons [2], and sources [5] and [6] specify a "juvenile or young-adult onset" [5, 6]. The presence of sensory neuropathy and infantile onset is inconsistent with these definitions [2, 5, 6].
* **P03:** **Ruled out.** 
  P03 has sensory axonal neuropathy, congenital/early pediatric manifestations, and feeding difficulties. HMND11 features "selective degeneration of motor" neurons [2] and "juvenile or young-adult onset" [5, 6].
* **P04:** **Cannot be definitively ruled in, but cannot be ruled out (Best Match).** 
  P04 possesses all key phenotypic hallmarks described in the sources: "Motor axonal neuropathy" matching the definition of a "peripheral axonal motor neuropathy" [2], "Distal muscle weakness" / "Weakness of the intrinsic hand muscles" matching "distal limb muscle weakness" [5, 6], and "Distal lower limb amyotrophy" matching "atrophy" [6]. However, the sources do not provide enough information (such as gene sequencing or age of onset) to definitively rule P04 in [1, 5, 6].
* **P05:** **Ruled out.** 
  P05 has sensory deficits ("Impaired distal vibration sensation", "Decreased sensory nerve conduction velocity") and demyelinating features ("Decreased motor nerve conduction velocity", "Motor conduction block"). HMND11 is defined specifically as an *axonal* neuropathy [2] with "selective degeneration of motor" neurons [2].
* **P06:** **Ruled out.** 
  P06 presents with "Proximal upper limb muscle weakness", spinal rigidity, and marked muscle damage (highly elevated creatine kinase), whereas HMND11 is defined by *distal* limb muscle weakness and atrophy [5, 6].
* **P07:** **Cannot be ruled in; less complete match than P04.** 
  P07 has distal lower limb weakness and amyotrophy [5, 6]. However, the sources do not provide sufficient clinical criteria to distinguish P07 definitively or rule them in, and P07 lacks the explicit diagnosis of "motor axonal neuropathy" present in source [2].
* **P08:** **Ruled out.** 
  P08 demonstrates widespread sensory loss across multiple modalities and decreased sensory action potential amplitudes, which conflicts with the "selective degeneration of motor" neurons that characterizes HMND11 [2].
* **P09:** **Cannot be ruled in; less complete match than P04.** 
  P09 has motor axonal neuropathy [2] and distal weakness [5, 6], but lacks documentation of muscle atrophy [6]. The sources do not allow a definitive rule-in.
* **P10:** **Ruled out.** 
  P10 presents with proximal limb weakness, ophthalmoplegia, ptosis, and dysphagia, which contradicts the characterization of HMND11 as a distal limb muscle weakness disorder [5, 6].

---

### 2. Single Most Likely Patient and Probability

* **Most Likely Patient:** **P04**
* **Estimated Probability:** **~75–80%**
  * *Reasoning:* Exactly one patient has HMND11. P04 is the only patient whose phenotypic profile completely aligns with every key feature explicitly mentioned in the text: a pure **motor axonal neuropathy** [2] presenting with **distal limb muscle weakness** (hands/feet) [5, 6] and **distal amyotrophy** [6], without sensory involvement [2]. P07 and P09 are the only other candidates without overt contradictory features, but their phenotypes match the source text less completely than P04.

---

### 3. Missing Facts Needed for Confidence

To be fully confident in the diagnosis, the following information—which the sources state is essential to HMND11 but the patient vignettes omit—would be required:
1. **Genetic confirmation:** Identification of a heterozygous pathogenic mutation in the *SPTAN1* gene on chromosome 9q34 [1, 3, 4].
2. **Age of onset:** Verification that the onset of symptoms occurred during the juvenile or young-adult period [5, 6].
3. **Family history and inheritance:** Documentation of an autosomal dominant pattern of transmission, accounting for potential incomplete penetrance [1, 5, 6].

--------------------------------------------------------------------------------

### Round 3  (picked: P04)

Based on the provided sources, here is the clinical evaluation for each patient:

### 1. Patient-by-Patient Rule In / Rule Out Assessment

* **P01**: **Cannot be ruled in or out definitively**, but is an unlikely presentation for HMND11. 
  * *Reasoning*: P01 exhibits pure upper motor neuron signs / spastic paraplegia without peripheral distal weakness or amyotrophy. While source [4] mentions a spectrum from neuropathy to pure spastic paraplegia and ataxia in relation to *SPTAN1*, HMND11 is specifically defined as a peripheral axonal motor neuropathy characterized by distal limb muscle weakness and atrophy [2, 5, 6], which P01 does not demonstrate.

* **P02**: **Ruled out (unlikely)**. 
  * *Reasoning*: P02 has congenital/early-developmental brain malformations (simplified gyral pattern, microcephaly) and a **sensory** axonal neuropathy. Source [2] defines HMND11 as a peripheral axonal motor neuropathy with *selective* degeneration of motor neurons, and sources [5, 6] describe juvenile or young-adult onset, contradicting early congenital brain anomalies and sensory involvement.

* **P03**: **Ruled out (unlikely)**. 
  * *Reasoning*: P03 presents with sensory axonal neuropathy, congenital onset (developmental delays, hip dysplasia), and myopathic features. HMND11 is defined as a selective motor neuronopathy [2] with juvenile/young-adult onset [5, 6].

* **P04**: **Ruled in as a strong candidate (cannot be definitively confirmed)**. 
  * *Reasoning*: P04 exhibits "Motor axonal neuropathy" [2] and both upper and lower distal limb involvement ("Weakness of the intrinsic hand muscles", "Distal muscle weakness", "Distal lower limb amyotrophy"), matching the definition of HMND11 as an axonal motor neuropathy with distal limb weakness and atrophy [2, 5, 6]. However, the sources do not provide genetic or age-of-onset data to confirm the diagnosis definitively.

* **P05**: **Ruled out (unlikely)**. 
  * *Reasoning*: P05 shows sensory conduction velocity slowing and impaired vibration sensation. HMND11 is characterized by selective motor degeneration [2].

* **P06**: **Ruled out (unlikely)**. 
  * *Reasoning*: P06 exhibits a muscular dystrophy phenotype (proximal upper limb weakness, elbow/neck contractures, rigid spine, highly elevated CK), whereas HMND11 is an axonal motor neuronopathy characterized by distal limb weakness and atrophy [2, 5, 6].

* **P07**: **Ruled in as a possible candidate (cannot be definitively confirmed)**. 
  * *Reasoning*: P07 has distal lower limb weakness, amyotrophy, and neurogenic EMG changes, which align with a distal motor neuropathy [2, 5, 6]. However, P07 lacks documented upper limb involvement, and the sources do not provide genetic confirmation.

* **P08**: **Ruled out (unlikely)**. 
  * *Reasoning*: P08 has prominent sensory axonal involvement (decreased sensory nerve action potential amplitudes, multiple modalities of sensory loss), which contradicts the selective motor neurodegeneration of HMND11 [2].

* **P09**: **Ruled in as a possible candidate (cannot be definitively confirmed)**. 
  * *Reasoning*: P09 displays "Motor axonal neuropathy" and distal lower limb weakness [2, 5]. However, amyotrophy [6] and upper limb involvement [5, 6] are not documented, and the sources provide no genetic testing data.

* **P10**: **Ruled out (unlikely)**. 
  * *Reasoning*: P10 presents with cranial nerve findings (ptosis, ophthalmoplegia, dysphagia) and proximal limb weakness, which does not fit the selective distal limb motor neuronopathy of HMND11 [2, 5, 6].

---

### 2. Single Most Likely Patient and Probability

* **Most likely patient**: **P04**
* **Estimated probability**: **~65% – 70%** (among this cohort of 10 where exactly one has HMND11).
  * *Justification*: P04 explicitly matches all core clinical features described in the sources: a pure **motor axonal neuropathy** [2] presenting with both distal upper limb weakness (intrinsic hand muscles) and distal lower limb weakness and amyotrophy [5, 6], with no sensory or systemic exclusions. While P07 and P09 also show motor neuropathy features, P04 captures the full distal limb weakness and atrophy phenotype affecting hands and legs [5, 6].

---

### 3. Missing Facts Needed to Be Confident

The provided sources do not supply several critical pieces of information needed for a definitive clinical genetic diagnosis:
1. **Genetic confirmation**: Demonstration of a heterozygous (dominant) pathogenic or nonsense variant in the *SPTAN1* gene on chromosome 9q34 [1, 3, 4].
2. **Age of onset**: Confirmation of juvenile or young-adult onset [5, 6] (none of the patient profiles list age at symptom onset).
3. **Family history / Inheritance pattern**: Evidence of autosomal dominant inheritance or family history (with consideration of incomplete penetrance) [1, 5, 6].
4. **Complete sensory electrophysiology**: Objective exclusion of sensory nerve action potential (SNAP) abnormalities to verify truly selective motor degeneration [2].

--------------------------------------------------------------------------------

picks across rounds: ['P04', 'P04', 'P04']
