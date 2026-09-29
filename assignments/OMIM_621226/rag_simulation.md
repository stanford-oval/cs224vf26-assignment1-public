# Plain RAG on Spastic ataxia 11, autosomal dominant (TUBA4A, OMIM:621226)
model: gemini-3.8-flash   generated: 2026-09-28 20:51

Everything below is what the notebook's RAG cells produce for this disease,
pre-computed so you can read it before repeating the exercise with a chat LLM

## 1. The search
query: `TUBA4A gene Spastic ataxia 11, autosomal dominant`

[1] **621226 - SPASTIC ATAXIA 11, AUTOSOMAL DOMINANT; ...**  
    https://omim.org/entry/621226  
    Autosomal dominant spastic ataxia-11 (SPAX11) is a progressive neurologic disorder characterized by gait disturbances due to ataxia and ...

[2] **A mouse model of autosomal dominant spastic ataxia ... - PMC**  
    https://pmc.ncbi.nlm.nih.gov/articles/PMC13014175/  
    Dominant TUBA4A mutations in humans are associated with spastic ataxia type 11 (SPAX11), congenital myopathy type 26 (CMYO26), and frontotemporal dementia ...

[3] **A mouse model of autosomal dominant spastic ataxia and ...**  
    https://www.biorxiv.org/content/10.64898/2026.03.06.710113v1  
    Dominant TUBA4A mutations in humans are associated with spastic ataxia type 11 (SPAX11), congenital myopathy type 26 (CMYO26), and ...

[4] **Gene: TUBA4A (Ataxia)**  
    https://panelapp-aus.org/panels/271/gene/TUBA4A/  
    Spastic ataxia 11, autosomal dominant, cognitive decline in 4/12, TUBA4A missense showed significant alterations in microtubule organisation and dynamics, ...

[5] **Spastic ataxia 11, autosomal dominant | Human diseases**  
    https://www.uniprot.org/diseases/DI-07045  
    SPAX11 is an autosomal dominant, progressive form with age at onset usually in the first 2 decades. Brain imaging often shows cerebellar atrophy. Gene: TUBA4A ...

[6] **De novo and inherited monoallelic variants in TUBA4A ...**  
    https://mayoclinic.elsevierpure.com/en/publications/de-novo-and-inherited-monoallelic-variants-in-tuba4a-cause-ataxia  
    Taken together, we report 12 patients presenting with spasticity and/or cerebellar ataxia and harbouring a predicted pathogenic TUBA4A missense ...

## 2. The context handed to the model
```
[1] 621226 - SPASTIC ATAXIA 11, AUTOSOMAL DOMINANT; ...
https://omim.org/entry/621226
Autosomal dominant spastic ataxia-11 (SPAX11) is a progressive neurologic disorder characterized by gait disturbances due to ataxia and ...

[2] A mouse model of autosomal dominant spastic ataxia ... - PMC
https://pmc.ncbi.nlm.nih.gov/articles/PMC13014175/
Dominant TUBA4A mutations in humans are associated with spastic ataxia type 11 (SPAX11), congenital myopathy type 26 (CMYO26), and frontotemporal dementia ...

[3] A mouse model of autosomal dominant spastic ataxia and ...
https://www.biorxiv.org/content/10.64898/2026.03.06.710113v1
Dominant TUBA4A mutations in humans are associated with spastic ataxia type 11 (SPAX11), congenital myopathy type 26 (CMYO26), and ...

[4] Gene: TUBA4A (Ataxia)
https://panelapp-aus.org/panels/271/gene/TUBA4A/
Spastic ataxia 11, autosomal dominant, cognitive decline in 4/12, TUBA4A missense showed significant alterations in microtubule organisation and dynamics, ...

[5] Spastic ataxia 11, autosomal dominant | Human diseases
https://www.uniprot.org/diseases/DI-07045
SPAX11 is an autosomal dominant, progressive form with age at onset usually in the first 2 decades. Brain imaging often shows cerebellar atrophy. Gene: TUBA4A ...

[6] De novo and inherited monoallelic variants in TUBA4A ...
https://mayoclinic.elsevierpure.com/en/publications/de-novo-and-inherited-monoallelic-variants-in-tuba4a-cause-ataxia
Taken together, we report 12 patients presenting with spasticity and/or cerebellar ataxia and harbouring a predicted pathogenic TUBA4A missense ...
```

## 3. The gene, from the sources

Dominant and monoallelic variants in the *TUBA4A* gene cause spastic ataxia 11, autosomal dominant (SPAX11) [2, 6]. The provided sources do not specifically define the exact gene product of *TUBA4A*, but they establish that its cellular function involves microtubule organisation and dynamics [4]. Pathogenic *TUBA4A* missense variants cause disease by triggering significant alterations in these cellular microtubule dynamics and organisation [4]. As a result of these variants, individuals develop SPAX11, which is a progressive neurologic disorder characterized by gait disturbances, spasticity, and cerebellar ataxia [1, 5, 6]. Onset typically occurs within the first two decades of life, and patients often show cerebellar atrophy on brain imaging, with some experiencing cognitive decline [4, 5]. Dominant mutations in *TUBA4A* are also linked to other conditions, including congenital myopathy type 26 and frontotemporal dementia [2].

*tokens in 595, out 1325*

## 4. The gene, closed book (no sources; beware hallucinations)

**TUBA4A** encodes **tubulin alpha-4A**, a structural protein that dimerizes with beta-tubulin to form microtubules. Microtubules are vital cytoskeletal components responsible for maintaining cellular structure, facilitating intracellular transport, and preserving axonal architecture, particularly in long projection neurons.

Pathogenic heterozygous missense variants in *TUBA4A* disrupt microtubule dynamics and stability. These altered subunits exert a dominant-negative effect or cause a toxic gain of function, impairing microtubule polymerization, compromising anterograde and retrograde axonal transport, and triggering length-dependent axonal degeneration of the corticospinal tracts and cerebellar pathways. Consequently, patients present with progressive lower-limb spasticity, hyperreflexia, cerebellar ataxia, and dysarthria.

## 5. Which patient? Three independent rounds, same prompt

### Round 1  (picked: P10)

Based on the provided sources, here is the clinical evaluation:

### 1. Patient Evaluation (Rule-in / Rule-out)

The sources define Spastic Ataxia 11 (SPAX11) as an autosomal dominant disorder characterized by gait disturbances due to ataxia [1], spasticity and/or cerebellar ataxia [6], and cerebellar atrophy on brain imaging [5]. The sources provide brief summary descriptions and do not include complete individual phenotypic profiles, negative diagnostic criteria, or individual HPO listings for the reported cases [1–6]. Consequently, **no patient can be definitively ruled in or ruled out with absolute certainty from the sources alone**, but their phenotypes can be evaluated for consistency with the documented features:

* **P01:** **Cannot be definitively ruled in or out.** P01 exhibits gait disturbance [1], cerebellar atrophy [5], dysmetria (cerebellar ataxia) [1, 6], and lower limb hypertonia/Babinski sign/clonus (spasticity) [6]. However, the sources do not provide individual case details to confirm whether P01 is the specific patient [1–6].
* **P02:** **Likely ruled out.** P02 has spastic paraplegia and gait disturbance, but lacks ataxia [1, 6] and cerebellar atrophy [5], which are characteristic of SPAX11.
* **P03:** **Likely ruled out.** P03 presents with motor axonal neuropathy, distal weakness, and amyotrophy without documented spasticity, ataxia, or cerebellar atrophy [1, 5, 6].
* **P04:** **Cannot be definitively ruled in or out, but unlikely.** P04 has gait ataxia [1], lower limb spasticity [6], and hyperreflexia, but exhibits "cerebellar vermis hypoplasia" rather than progressive cerebellar atrophy [5].
* **P05:** **Ruled out for SPAX11.** P05 displays a myopathic phenotype (elevated CK, ophthalmoplegia, ptosis, respiratory insufficiency, axial/limb weakness) consistent with congenital myopathy 26 (CMYO26), a different condition linked to *TUBA4A* [2, 3], rather than the spastic ataxia phenotype of SPAX11 [1, 5, 6].
* **P06:** **Likely ruled out.** P06 has ataxia, unsteady gait, and cerebellar atrophy [1, 5, 6], but lacks spasticity [6].
* **P07:** **Likely ruled out.** P07 has spasticity and motor neuropathy but lacks ataxia [1, 6] and cerebellar atrophy [5].
* **P08:** **Likely ruled out.** P08 has spasticity and sensory/motor deficits but lacks cerebellar ataxia [1, 6] and cerebellar atrophy [5].
* **P09:** **Likely ruled out.** P09 has dysmetria, unsteady gait, and cerebellar atrophy [1, 5, 6], but also has CNS demyelination and sensory neuropathy, and lacks spasticity [6].
* **P10:** **Cannot be definitively ruled in, but has the highest concordance.** P10 presents with the hallmark features: "Spastic ataxia" [1–5], gait imbalance [1], upper and lower limb spasticity [6], dysmetria (ataxia) [1, 6], and cerebellar vermis atrophy [5].

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P10**
* **Estimated Probability:** **75%** 
  * *Rationale:* P10 possesses all hallmark phenotypic elements cited across the sources: spastic ataxia [1–5], gait disturbance/imbalance [1], spasticity [6], dysmetria/cerebellar ataxia [1, 6], and cerebellar atrophy [5]. (P01 is the only other strong candidate exhibiting both spasticity, ataxia, and cerebellar atrophy, but P10 explicitly manifests the combined spastic ataxia entity).

---

### 3. Facts Needed (and Not Present in the Sources) to Be Confident

The provided sources do not contain:
1. **Specific genetic test results:** Confirmation of a pathogenic heterozygous/monoallelic *TUBA4A* missense variant in the patient [4, 6].
2. **Individual clinical profiles/HPO term lists:** The exact clinical records or HPO terms of the 12 reported individuals with *TUBA4A* mutations [4, 6].
3. **Age of onset:** Whether onset was during the first two decades of life [5].
4. **Cognitive assessment:** Information on whether cognitive decline is present or evaluated (seen in 4/12 patients) [4].
5. **Family history:** Confirmation of an autosomal dominant inheritance pattern or a confirmed *de novo* occurrence [1, 5, 6].
6. **Definitive exclusion/inclusion criteria:** Granular guidelines to formally rule out phenotypically overlapping spastic ataxias from these brief abstracts [1–6].

--------------------------------------------------------------------------------

### Round 2  (picked: P10)

Based on the provided sources, here is the clinical evaluation for each patient:

### 1. Patient Evaluation (Ruling In/Ruling Out)

The provided sources establish that autosomal dominant spastic ataxia-11 (SPAX11) is characterized by:
* Spastic ataxia, or spasticity and/or cerebellar ataxia [1, 2, 3, 5, 6].
* Gait disturbances due to ataxia [1].
* Cerebellar atrophy on brain imaging [5].
* Progressive course with age of onset usually in the first two decades [1, 5].
* Cognitive decline in a subset of patients (4 of 12) [4].

Critically, the sources **do not** provide complete phenotypic descriptions of all 12 reported individuals, full negative/exclusionary criteria, or molecular genetic results for the patients listed [1–6]. Consequently, **no patient can be definitively ruled in or ruled out** based solely on the provided text:

* **P01**: **Cannot be ruled in or out.** P01 has gait disturbance [1], cerebellar atrophy [5], and hypertonia/pyramidal signs consistent with spasticity [6]. However, the sources do not provide individual case details or ancillary test criteria (e.g., evoked potentials, bladder function) to confirm or exclude SPAX11 [1–6].
* **P02**: **Cannot be ruled in or out.** P02 exhibits spasticity and gait disturbance [1, 6], but lacks documented ataxia or cerebellar atrophy [1, 5, 6]. While source [6] mentions presentation with "spasticity and/or cerebellar ataxia," the sources do not provide exclusion criteria to rule P02 out definitively.
* **P03**: **Cannot be ruled in or out.** P03 has lower limb weakness and motor axonal neuropathy, with no ataxia, spasticity, or cerebellar atrophy reported [1, 5, 6]. The sources lack explicit negative criteria to rule P03 out, but offer no support to rule P03 in.
* **P04**: **Cannot be ruled in or out.** P04 has gait ataxia, limb ataxia, and spasticity [1, 6]. However, imaging shows cerebellar vermis *hypoplasia* rather than the cerebellar *atrophy* described in the source [5]. The sources do not specify whether hypoplasia is an accepted feature of SPAX11.
* **P05**: **Cannot be ruled in or out.** P05 has myopathic, ptosis, and respiratory features. Although *TUBA4A* is also associated with congenital myopathy type 26 (CMYO26) [2, 3], the diagnosis in question is SPAX11. P05 lacks spasticity, ataxia, and cerebellar atrophy [1, 5, 6], but the text provides no formal exclusion list to definitively rule P05 out.
* **P06**: **Cannot be ruled in or out.** P06 has ataxia, unsteady gait, and cerebellar atrophy [1, 5, 6], but lacks documented spasticity. Because source [6] mentions "spasticity and/or cerebellar ataxia," P06 cannot be ruled out, but lack of detailed clinical data prevents ruling P06 in.
* **P07**: **Cannot be ruled in or out.** P07 has spasticity and spastic gait [1, 6], but predominantly displays peripheral motor axonal neuropathy features without ataxia or cerebellar atrophy [1, 5, 6]. The sources provide neither exclusionary rules nor confirming details.
* **P08**: **Cannot be ruled in or out.** P08 has spasticity [6], but lacks ataxia or cerebellar atrophy [1, 5]. The sources do not give sufficient clinical limits to rule P08 out, nor sufficient evidence to rule P08 in.
* **P09**: **Cannot be ruled in or out.** P09 has cerebellar atrophy [5], dysmetria (ataxic sign), and unsteady gait [1], but also features CNS demyelination and sensory neuropathy, neither of which are described in the sources. The sources do not state whether demyelinating findings exclude SPAX11.
* **P10**: **Cannot be ruled in or out.** P10 displays the core triad explicitly identified in the text: spastic ataxia [1, 2, 3, 4, 5], gait disturbance/imbalance [1], spasticity [6], and cerebellar atrophy [5]. However, without molecular genetic confirmation or the original paper's case-level data, P10 cannot be definitively ruled in.

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P10**
* **Estimated Probability:** **80%**
  * *Rationale:* P10 exhibits the explicit, defining diagnostic entity named in the sources ("Spastic ataxia") [1, 2, 3, 4, 5], along with limb spasticity [6], gait disturbance [1], and cerebellar atrophy [5]. The remaining 20% uncertainty accounts for the clinical overlap seen in other candidates (such as P01 and P04) and the lack of genetic confirmation in the prompt.

---

### 3. Missing Information Needed for Diagnostic Confidence

To establish a definitive diagnosis, the following information is missing from the provided sources:
1. **Molecular genetic data:** Demonstration of a heterozygous, pathogenic/likely pathogenic missense variant in *TUBA4A* [2, 4, 5, 6].
2. **Individual-level phenotypic descriptions:** The full HPO term lists or comprehensive clinical summaries of the 12 reported individuals with *TUBA4A*-related SPAX11 [4, 6].
3. **Age of onset and disease progression:** Confirmation that the disorder was progressive and manifested within the first two decades of life [1, 5].
4. **Cognitive status:** Documentation of cognitive decline (reported in 4 of 12 patients) [4].
5. **Exclusionary criteria:** Clear information on whether peripheral neuropathy, conduction blocks, or demyelination are compatible with or exclusionary for SPAX11.

--------------------------------------------------------------------------------

### Round 3  (picked: P10)

Based on the provided sources, here is the clinical genetics evaluation:

### 1. Patient Evaluation (Rule In / Rule Out)

The provided sources do not include patient-level datasets, full HPO terms, or explicit exclusion criteria; therefore, **the sources do not allow any patient to be definitively ruled in or definitively ruled out with certainty.** However, comparing each patient's presentation against the core features described—progressive gait disturbance due to spasticity and/or cerebellar ataxia [1, 6] and cerebellar atrophy [5]—yields the following:

* **P01:** **Cannot be ruled in or out.** P01 exhibits core features described in the sources, including gait disturbance [1], dysmetria/ataxia [1, 6], cerebellar atrophy [5], and signs of spasticity/hypertonia [1, 6]. However, the sources do not provide individual case details to definitively confirm (rule in) this patient.
* **P02:** **Cannot be ruled in or out, but unlikely.** P02 has spastic paraplegia and gait disturbance [1, 6], but lacks cerebellar ataxia and cerebellar atrophy [1, 5, 6]. The sources do not explicitly state that the absence of ataxia definitively rules out the diagnosis.
* **P03:** **Cannot be ruled in or out, but highly unlikely.** P03 presents with motor axonal neuropathy and distal weakness without documented spasticity, cerebellar ataxia, or cerebellar atrophy [1, 5, 6].
* **P04:** **Cannot be ruled in or out, but unlikely.** P04 has gait/limb ataxia and lower limb spasticity [1, 6], but presents with cerebellar vermis *hypoplasia* (a developmental defect) rather than progressive cerebellar *atrophy* [1, 5].
* **P05:** **Cannot be ruled in or out, but unlikely.** P05 has severe generalized weakness, ptosis, ophthalmoplegia, and elevated creatine kinase. While dominant *TUBA4A* mutations are also linked to congenital myopathy type 26 (CMYO26) [2, 3], this presentation does not fit the phenotype of spastic ataxia 11 (SPAX11), which requires gait disturbance, spasticity, and/or ataxia [1, 5, 6].
* **P06:** **Cannot be ruled in or out, but unlikely.** P06 has unsteady gait, ataxia, and cerebellar atrophy [1, 5, 6], but lacks spasticity (only brisk reflexes are noted) [1, 6].
* **P07:** **Cannot be ruled in or out, but unlikely.** P07 has spasticity and a spastic gait [1, 6], but lacks cerebellar ataxia or cerebellar atrophy [1, 5, 6].
* **P08:** **Cannot be ruled in or out, but unlikely.** P08 has spasticity and hyperreflexia [1, 6], but lacks ataxia, gait disturbance, and cerebellar atrophy [1, 5].
* **P09:** **Cannot be ruled in or out, but unlikely.** P09 has dysmetria, unsteady gait, and cerebellar atrophy [1, 5, 6], but has central demyelination and lacks clear spasticity or spastic ataxia [1, 6].
* **P10:** **Cannot be ruled in or out.** P10 displays the hallmark features of SPAX11 explicitly: "Spastic ataxia" [1, 2, 3, 4, 5], gait imbalance/disturbance [1], upper and lower limb spasticity [6], dysmetria (ataxia) [1, 6], and cerebellar vermis atrophy [5]. However, the sources do not provide genetic confirmation to definitively rule them in.

---

### 2. Single Most Likely Patient and Estimated Probability

* **Most Likely Patient:** **P10** 
* **Estimated Probability:** **60%** (with P01 being the alternative possibility at ~35%, and all others combined at ~5%).

**Reasoning:** P10 aligns directly with all primary clinical descriptors provided: gait disturbance [1], spastic ataxia / spasticity [1, 6], dysmetria/cerebellar involvement [1, 6], and cerebellar atrophy [5]. P01 also matches closely, but P10 explicitly lists the disease's cardinal manifestation ("Spastic ataxia") [1].

---

### 3. Facts Needed (That Are Missing in the Sources) to Be Confident

To establish a definitive diagnosis, the following information—which is not contained in the sources—is required:
1. **Genetic testing results:** Identification of a heterozygous pathogenic missense variant in *TUBA4A* for the specific patient [2, 4, 6].
2. **Family history / Mode of inheritance:** Demonstration of autosomal dominant transmission or a confirmed *de novo* mutation [1, 5, 6].
3. **Age of onset:** Verification that symptom onset occurred in the first two decades of life [5].
4. **Clinical course:** Confirmation of a progressive neurological decline [1, 5].
5. **Original cohort HPO descriptions:** The exact individual phenotypic profiles and variant details of the 12 reported SPAX11 patients referenced in the literature [4, 6].

--------------------------------------------------------------------------------

picks across rounds: ['P10', 'P10', 'P10']
