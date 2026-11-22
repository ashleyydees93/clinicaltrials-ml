# Mining Type 2 Diabetes Clinical Trial Results
## Final Project Report — Caroline Pearson and Ashley Dees
**DSC 521 · November 2026**

---

## Abstract

We collected every Type 2 diabetes study on ClinicalTrials.gov whose results were first posted between **November 3, 2025 and November 2, 2026** (121 studies) and screened them with written eligibility rules (89 eligible). From these studies we extracted **6,943 measurement records** (baseline characteristics, outcome measures, and adverse events). We then manually labeled a stratified sample as **Baseline**, **Efficacy**, or **Safety**, which gave 267 model-ready records from 76 studies. We trained four text classifiers: TF-IDF + Logistic Regression, TF-IDF + Multinomial Naive Bayes, TF-IDF + Linear SVM, and fine-tuned **BioBERT**. We evaluated them on **191 records from 54 held-out studies** that were never seen in training. All four models far outperform the most-frequent-class baseline (macro-F1 0.157). The three TF-IDF models were nearly tied at a macro-F1 of about 0.86. BioBERT's settings were chosen on validation studies only, never the test set, and it was trained with five random seeds. It **performed best**, with a macro-F1 of 0.905 ± 0.024 across seeds (0.879 for the pre-specified seed). BioBERT beat Logistic Regression (0.865) on all five seeds, by +0.040 macro-F1 on average. However, the 95% study-level confidence interval for that gap (−0.016 to +0.093) includes zero. BioBERT is therefore probably, but not demonstrably, better than Logistic Regression on this data.

---

## 1. Introduction and Objectives

Type 2 diabetes trials report treatment benefit, participant characteristics, and harms using inconsistent terminology. The same phrase, for example *"HbA1c"* or *"body weight,"* can describe a participant's starting point, an intended benefit, or a side effect, depending on where it appears in the record. Our classifier assigns each measurement a type of outcome measure. It **does not** judge whether a treatment worked or was safe.

The professor-approved proposal set three goals:

1. Create a reviewed sample of outcome measures labeled **baseline characteristics**, **efficacy**, or **safety**.
2. Summarize outcome-category frequencies and trends by **Results First Posted year**. We report these by month (Section 3) because the collection window spans a single year.
3. Train a **text classifier** to assign outcome categories, evaluated with **F1 as the primary metric** (plus accuracy) against a **most-frequent-class baseline** on **held-out studies**.

All three goals were completed. Sections 2–3 cover goals 1–2, and Sections 4–6 cover goal 3.

---

## 2. Data

### 2.1 Collection

| Item | Value |
|---|---|
| Source | ClinicalTrials.gov API v2 (`/api/v2/studies`) |
| Condition query | `query.cond = "Type 2 Diabetes"` |
| Date filter | `AREA[ResultsFirstPostDate]RANGE[2025-11-03, 2026-11-02]` |
| Retrieval date | 2026-11-05 |
| Pagination | All pages followed with `nextPageToken` (page size 100) |
| Studies retrieved | **121** (no duplicate NCT IDs; all dates inside the window) |

The original JSON records are saved in `data/raw/studies.json`, and the query parameters are saved in `data/raw/collection_metadata.json`. Together they make the retrieval reproducible and auditable, even though ClinicalTrials.gov records can change over time.

### 2.2 Screening

Both researchers screened the studies using the written rules in `screening/screening_rules.md`. Studies were included if they examined Type 2 diabetes or a relevant complication and had structured results. Studies were excluded if they were Type 1 only, prediabetes or prevention only, mentioned T2D only incidentally, or had no usable measurements. Uncertain cases were marked `review` and decided jointly.

| Stage | Studies | Records |
|---|---:|---:|
| Retrieved by search | 121 | — |
| Eligible after screening | **89** | — |
| Measurements extracted from eligible studies | 89 | **6,943** |
| Stratified labeling sample (100 per source section) | 77 | 300 |
| Excluded during label review (see §2.4) | 12 | 33 |
| Model-ready after review | **76** | **267** |
| Training split | 22 | 76 |
| Held-out test split | 54 | 191 |

One study, RADIANT (NCT05923827), passed screening but was confirmed during label review to be a **Type 1 diabetes** study. Its sampled records were removed (§2.4), and the split script includes an explicit check that stops it from re-entering the dataset.

### 2.3 Extraction and missing data

Each eligible study was re-downloaded individually. Three kinds of record were extracted: baseline measures (`baselineCharacteristicsModule`), outcome measures (`outcomeMeasuresModule`), and serious and other adverse events (`adverseEventsModule`). The model input is `title + description`. For adverse events, that means the MedDRA term followed by its organ system.

| Source section | Records | Missing description |
|---|---:|---:|
| Adverse events | 5,412 (77.9%) | 0 |
| Outcome measures | 966 (13.9%) | 15 (1.6%) |
| Baseline characteristics | 565 (8.1%) | 492 (87.1%) |
| **Total** | **6,943** | **507 (7.3%)** |

Most baseline records are bare titles such as *"Age"* or *"Systolic blood pressure"* with no description. A missing description was stored as empty text and was **not** treated as evidence of anything. As planned in the proposal, a missing adverse-event entry is never read as "no adverse event occurred."

### 2.4 Labeling (Goal 1)

We drew a stratified random sample of 100 records from each source section (seed 143) and split it evenly between the two reviewers. Labels followed the written definitions in the screening rules:

- **Baseline:** describes participants at study start (age, sex, baseline BMI or HbA1c).
- **Efficacy:** assesses an intervention's intended benefit (change in HbA1c, time in range, weight change when weight loss is the goal).
- **Safety:** assesses harms or tolerability (adverse events, hypoglycemia, discontinuation due to AEs).

Each reviewer's original decision was kept next to a rule-based quality check. Where the two disagreed, the label was corrected and the reason recorded. There were **102 corrections** in total, mostly baseline-table records originally labeled Efficacy and adverse-event terms originally labeled Efficacy. The full audit trail is in `screening/Clinical_Trials_Model_Ready_T2D_Exclusions_Applied.xlsx` (sheets *Corrections Log* and *Excluded Records*).

**33 of the 300 sampled records were excluded**, for these documented reasons:

| Exclusion reason | Records | Studies | Source sections (AE / baseline / outcome) | Examples |
|---|---:|---:|---|---|
| Originally marked *Unclear* by reviewer | 25 | 10 | 18 / 3 / 4 | *"Diabetic ketoacidosis"*, *"Septic shock"*, *"Percentage of Participants Who Achieve ≥10% Body Weight Reduction"*, *"Time to CV Death"* |
| Type 1 diabetes study (RADIANT; NCT05923827) | 7 | 1 | 1 / 6 / 0 | *"Age, Continuous"*, *"BMI (kg/m²)"*, *"Systolic Blood Pressure"* |
| Unclear after quality check | 1 | 1 | 0 / 0 / 1 | *"Study Retention Rate"* (measures feasibility, not baseline, efficacy, or safety) |
| **Total** | **33** | **12** | 19 / 9 / 5 | |

As the proposal required, unclear records were flagged and set aside instead of being forced into a category. Many of them are clinical events that could be an efficacy endpoint in one trial and a harm in another, such as cardiovascular death or weight reduction.

After review, 267 records were kept. They are close to balanced across classes (Baseline 92, Safety 89, Efficacy 86), so class imbalance was not a concern in this project. Labels did not simply copy the source section:

| Source section → label | Baseline | Efficacy | Safety |
|---|---:|---:|---:|
| baseline | 91 | 0 | 0 |
| outcome | 1 | 86 | **8** |
| adverse_event | 0 | 0 | 81 |

Eight registered *outcome measures* were safety endpoints, for example hypoglycaemic episodes or orthostatic hypotension. This is the overlap between efficacy and safety that the proposal anticipated. It is also why a keyword or section rule alone would not be enough.

---

## 3. Reporting Patterns by Results First Posted Month (Goal 2)

The proposal called for trends by Results First Posted **year**. Our rolling window (November 3, 2025 – November 2, 2026) contains only one full calendar year, so a yearly breakdown would compare about two months of 2025 against ten months of 2026. We therefore summarize by **month**, which shows how reporting varies across the window.

**All extracted measurements (eligible studies):**

| Results First Posted month | Studies retrieved | Eligible studies | Baseline | Outcome | Adverse events | AE per eligible study |
|---|---:|---:|---:|---:|---:|---:|
| Nov 2025 | 2 | 0 | 0 | 0 | 0 | — |
| Dec 2025 | 10 | 6 | 62 | 57 | 51 | 8.5 |
| Jan 2026 | 7 | 6 | 31 | 43 | 113 | 18.8 |
| Feb 2026 | 7 | 5 | 21 | 28 | 35 | 7.0 |
| Mar 2026 | 11 | 7 | 41 | 72 | 8 | 1.1 |
| Apr 2026 | 16 | 11 | 75 | 124 | 794 | 72.2 |
| May 2026 | 12 | 9 | 50 | 67 | 139 | 15.4 |
| Jun 2026 | 15 | 11 | 66 | 109 | 359 | 32.6 |
| Jul 2026 | 9 | 8 | 38 | 81 | **2,028** | **253.5** |
| Aug 2026 | 12 | 9 | 67 | 140 | 178 | 19.8 |
| Sep 2026 | 11 | 9 | 64 | 146 | 438 | 48.7 |
| Oct 2026 | 8 | 7 | 42 | 82 | 1,115 | 159.3 |
| Nov 2026 (1–2) | 1 | 1 | 8 | 17 | 154 | 154.0 |
| **Total** | **121** | **89** | **565** | **966** | **5,412** | **60.8** |

**Labeled (model-ready) measurements by month:**

![Labeled outcome categories by Results First Posted month](../clinicaltrials-ml/results/categories_by_results_month.png)

**Observations**

- **Adverse events dominate what is reported.** They make up 78% of all extracted measurements, against 14% outcome measures and 8% baseline measures.
- **Adverse-event volume depends on a few large trials, not on the calendar.** Baseline and outcome counts stay fairly steady each month (roughly 20–75 and 30–145). Adverse-event counts swing from 8 (March) to 2,028 (July). A handful of large, multi-arm drug trials report hundreds of MedDRA terms each, which produces the spikes in April, July, and October. Small behavioral or education studies report few or none.
- **Monthly baseline and efficacy counts in the labeled sample are fairly stable.** The largest Safety bars (July, October, April) line up with the adverse-event spikes in the full extraction.
- **The labeled sample's mix reflects our sampling, not a trend.** We sampled 100 records per source section, and individual months hold only 10–42 labeled records from 1–8 studies. The full-extraction table is the better guide to reporting patterns.
- No month-to-month trend can be claimed from one year of data. Repeating the collection over several years would allow a true trend analysis.

---


## 4. Methods

### 4.1 Leakage-safe split

Measurements from the same study share wording, interventions, and sponsor templates, so a random row split would leak information. We used `GroupShuffleSplit` grouped by **NCT ID** (seed 143). The script asserts that no study appears in both training and test, and that every class appears in both splits.

We deliberately made the test split large, holding out 70% of studies (54 studies, 191 records) and training on 22 studies (76 records). This has two effects:

- The held-out estimate is more stable than a 20% test set of about 53 records would be.
- It stress-tests each model in the **low-data regime** this project will always face, because manual labeling is expensive.

### 4.2 Features

The three classical models use **TF-IDF** on `title + description`, with English stop words removed. The Linear SVM also uses unigrams and bigrams with `min_df = 2`. BioBERT uses its own WordPiece tokenizer (cased, truncated at 256 tokens, with dynamic padding).

### 4.3 Models and why each fits this data

| Model | Configuration | Why it suits this data |
|---|---|---|
| **Most-frequent class** (baseline) | Always predicts the majority training class (*Efficacy*) | The comparison required by the proposal. It shows what "no learning" scores. |
| **Logistic Regression** | `TfidfVectorizer(stop_words="english")` → `LogisticRegression(max_iter=1000)` | The standard strong baseline for short-text classification. It handles high-dimensional sparse TF-IDF features well with L2 regularization, so it resists overfitting with only 76 training rows. Its coefficients are **interpretable**. In our trained model, the top Baseline words are *age, sex, male, female, race, ethnicity*. The top Efficacy words are *change, baseline, weight, self, care*: the word "baseline" points to Efficacy because of the phrase *"change from baseline."* The top Safety words are MedDRA organ-system terms such as *disorders, gastrointestinal, cardiac, infections, investigations*. It also outputs probabilities that can flag uncertain records for human review. This was the model named in our original plan. |
| **Multinomial Naive Bayes** | `TfidfVectorizer(stop_words="english")` → `MultinomialNB()` | A generative model that estimates one word distribution per class. It needs very little data to fit, which makes it a natural fit for a 76-record training set. It trains in milliseconds and gives a second simple, transparent reference point. Its word-independence assumption is a reasonable approximation for short measurement titles. |
| **Linear SVM** | `TfidfVectorizer(ngram_range=(1,2), min_df=2)` → `LinearSVC(C=1.0)` | Maximum-margin classifiers are among the strongest classical methods for sparse text. **Bigrams** capture phrases that single words miss, such as *"change from baseline"*, *"adverse events"*, and *"serious adverse"*. The SVM tests whether adding phrase context to a linear model closes the gap with a deep model. |
| **BioBERT** | `dmis-lab/biobert-base-cased-v1.1`, lr 2e-5, batch 8, weight decay 0.01, epoch count (1–6) selected on validation studies, 5 training seeds (CPU only); see §4.4 | A BERT model pre-trained on PubMed abstracts and PMC full-text articles, so it already **knows biomedical vocabulary**: drug names, lab tests (*aspartate aminotransferase*), MedDRA adverse-event terms, and clinical phrasing. Transfer learning lets it use that knowledge with only 76 labeled examples. Unlike bag-of-words models, it reads **word order and context**, which matters when the same term can be baseline, efficacy, or safety. With so few training rows, CPU-only fine-tuning was practical. |

Every trained model is saved: the classical models to `data/processed/models/*.joblib`, and BioBERT to `data/processed/biobert_results/best_model`.

### 4.4 BioBERT training protocol (no test-set selection, multiple seeds)

An earlier version of the BioBERT script passed the test set as its evaluation set, so `load_best_model_at_end` chose the checkpoint by test loss. That version was also run with only one seed. To get a fair comparison with Logistic Regression, `13.1_train_BioBert.py` now works like this:

1. **Validation split from training studies only.** We hold out 25% of the 22 training studies (6 studies, 25 records: 7 Baseline, 7 Efficacy, 11 Safety), grouped by NCT ID. That leaves 16 studies and 51 records for fitting. The test set plays no part in any choice.
2. **Stage 1, choosing the epoch count.** The model trains on the 51 fit records for up to 6 epochs and is scored on the validation studies after each one. The epoch count with the best validation macro-F1 is kept, with ties broken by lower validation loss.
3. **Stage 2, retraining.** The model restarts from the pre-trained BioBERT weights and trains on **all 76 training records** for the chosen number of epochs. BioBERT therefore sees exactly the same training data as the TF-IDF models.
4. **One test prediction per seed.** The test set is scored once per seed, after every choice has been made.
5. **Five seeds** (143, 1, 2, 3, 4). Each seed changes the classifier-head initialization, the dropout, and the batch order.

**Seed 143**, the project-wide seed, was fixed in advance as the *canonical* model. Its predictions feed the tables in §5.1–5.3 and the saved model. We did **not** pick the seed with the best test score. The other four seeds measure how much results vary between training runs (§5.4).

### 4.5 Metrics

Following the proposal and the course evaluation guide, we report **macro-F1 (primary)**, accuracy, weighted-F1, micro-F1, and per-class precision, recall, and F1. Macro-F1 weights every class equally, so a model cannot score well by ignoring one category. For single-label multiclass problems, micro-F1 equals accuracy. We also report:

- **95% confidence intervals** for macro-F1, from a bootstrap that resamples whole studies (2,000 resamples), to match the grouped design.
- **McNemar exact tests** on paired predictions, to check whether differences between models are larger than chance.
- **5-fold grouped cross-validation** on the training set for the TF-IDF models, reported separately from the held-out test scores (§5.1).
- For BioBERT against Logistic Regression, a **paired study-level bootstrap of the macro-F1 difference**, run for each seed and averaged across seeds (`18_compare_biobert_lr.py`).

---

## 5. Results

### 5.1 Overall performance (held-out test set: 191 records, 54 studies)

| Model | Accuracy | **Macro-F1** | 95% CI (macro-F1) | Weighted-F1 | Micro-F1 | Error rate | Errors |
|---|---:|---:|:---:|---:|---:|---:|---:|
| Most-frequent class | 0.309 | 0.157 | 0.118 – 0.196 | 0.146 | 0.309 | 0.691 | 132 |
| Logistic Regression | 0.864 | 0.865 | 0.786 – 0.937 | 0.866 | 0.864 | 0.136 | 26 |
| Naive Bayes | 0.859 | 0.859 | 0.782 – 0.928 | 0.861 | 0.859 | 0.141 | 27 |
| Linear SVM | 0.859 | 0.860 | 0.794 – 0.926 | 0.859 | 0.859 | 0.141 | 27 |
| **BioBERT** (canonical seed 143) | **0.880** | **0.879** | 0.811 – 0.928 | **0.880** | **0.880** | **0.120** | **23** |
| *BioBERT, mean of 5 seeds* | *0.906 ± 0.023* | *0.905 ± 0.024* | — | *0.906* | *0.906* | *0.094* | *18.0* |

![Macro-F1 vs. most-frequent-class baseline](../clinicaltrials-ml/results/macro_f1_vs_baseline.png)

Every learned model improves macro-F1 by about **0.70** over the majority-class baseline. The pre-specified BioBERT model (seed 143) is the best single model at 0.879. Averaged over five training seeds BioBERT reaches **0.905**, which means about 18 errors against 26 for Logistic Regression. Seed 143 happens to be the **weakest** of the five seeds (§5.4).

#### Cross-validation on the training set (TF-IDF models)

As a second check that does not use the test set, `15_compare_models.py` runs **5-fold grouped cross-validation** (`StratifiedGroupKFold`, grouped by NCT ID) on the 76 training records. Each fold trains on about 61 records and is scored on the remaining 4–5 studies. BioBERT is not included, because each BioBERT fit takes minutes on CPU (see §4.4 for its own validation design).

| Model | Accuracy (mean ± SD) | **Macro-F1** (mean ± SD) | Weighted-F1 | Micro-F1 | Error rate |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.792 ± 0.120 | **0.755 ± 0.174** | 0.785 | 0.792 | 0.208 |
| Naive Bayes | 0.765 ± 0.132 | 0.720 ± 0.187 | 0.747 | 0.765 | 0.235 |
| Linear SVM | 0.727 ± 0.025 | 0.670 ± 0.075 | 0.709 | 0.727 | 0.273 |

![Cross-validation model comparison](../clinicaltrials-ml/results/model_comparison.png)

Cross-validation gives the **same ranking** of the classical models as the held-out test set, with Logistic Regression first, then Naive Bayes, then Linear SVM. The scores are lower and much more variable (macro-F1 SD up to 0.19) because each fold trains on fewer records and is scored on only 4–5 studies. Cross-validation therefore confirms the ranking, and the larger 54-study test set gives the more precise performance estimate.

The Linear SVM's weaker cross-validation result is largely explained by its `min_df = 2` setting. With about 61 training records per fold, `min_df = 2` keeps only about 266 of roughly 957 terms, a 72% cut. In a training-set-only check, dropping that filter (`min_df = 1`) raised the SVM's CV macro-F1 from 0.670 to 0.734. That is still below Logistic Regression's 0.755, so the ranking does not change. We kept the original SVM settings rather than re-tuning after test results were available. All of these differences fall within one fold standard deviation.

### 5.2 Per-class performance

| Model | Baseline P / R / F1 | Efficacy P / R / F1 | Safety P / R / F1 |
|---|---|---|---|
| Logistic Regression | **0.96** / 0.74 / 0.84 | 0.71 / **0.97** / 0.82 | **0.98** / 0.89 / **0.94** |
| Naive Bayes | 0.91 / 0.79 / 0.85 | 0.73 / 0.90 / 0.80 | 0.97 / 0.89 / 0.93 |
| Linear SVM | 0.77 / **0.88** / 0.82 | **0.86** / 0.93 / **0.89** | 0.98 / 0.77 / 0.86 |
| **BioBERT** (seed 143) | 0.93 / 0.83 / **0.88** | 0.79 / 0.88 / 0.83 | 0.92 / **0.92** / 0.92 |
| *BioBERT F1, 5-seed mean (range)* | *0.89 (0.86–0.92)* | *0.89 (0.83–0.93)* | *0.93 (0.91–0.96)* |

![Per-class F1 by model](../clinicaltrials-ml/results/per_class_f1_by_model.png)

- **BioBERT** has the most **balanced** profile, with no class below 0.83 F1. Averaged over seeds it is best or tied-best on Baseline and Efficacy and level with Logistic Regression on Safety. Seed 143 has the best Baseline F1 and the best Safety recall (0.92). It gives up some Efficacy precision because it labels 5 efficacy outcomes as Safety (§5.5).
- **Logistic Regression and Naive Bayes** over-predict *Efficacy*. They predicted 80 and 73 Efficacy labels when only 59 are true. Many bare baseline titles get pulled into Efficacy, which gives Efficacy a precision of only 0.71–0.73.
- **Linear SVM** fixes much of that, with Baseline recall of 0.88 and the best Efficacy precision. But it loses **Safety recall (0.77)**: it labeled 14 adverse-event terms as Baseline. Many MedDRA terms appear only once, so `min_df = 2` drops them from the bigram vocabulary, leaving the SVM with little evidence for rare adverse-event wording.

### 5.3 Confusion matrices (rows = true label, columns = predicted)

| True ↓ / Pred → | LR: B / E / S | NB: B / E / S | SVM: B / E / S | **BioBERT (seed 143): B / E / S** |
|---|:---:|:---:|:---:|:---:|
| Baseline (66) | 49 / 17 / 0 | 52 / 14 / 0 | 58 / 8 / 0 | **55 / 11 / 0** |
| Efficacy (59) | 1 / 57 / 1 | 4 / 53 / 2 | 3 / 55 / 1 | **2 / 52 / 5** |
| Safety (66) | 1 / 6 / 59 | 1 / 6 / 59 | 14 / 1 / 51 | **2 / 3 / 61** |

| BioBERT (seed 143) | Logistic Regression |
|---|---|
| ![BioBERT confusion matrix](../clinicaltrials-ml/results/confusion_matrix_biobert.png) | ![Logistic Regression confusion matrix](../clinicaltrials-ml/results/confusion_matrix_logistic_regression.png) |
| **Linear SVM** | **Naive Bayes** |
| ![Linear SVM confusion matrix](../clinicaltrials-ml/results/confusion_matrix_linear_svm.png) | ![Naive Bayes confusion matrix](../clinicaltrials-ml/results/confusion_matrix_naive_bayes.png) |

`results/labeling_frequencies_by_model.png` compares each model's predicted label counts with the true test distribution. BioBERT's predicted counts (59 / 66 / 66) are closest to the true counts (66 / 59 / 66). Logistic Regression is at 51 / 80 / 60, Naive Bayes at 57 / 73 / 61, and Linear SVM at 75 / 64 / 52.

### 5.4 Is BioBERT truly better than Logistic Regression?

With selection moved to validation studies and five training seeds, we compared BioBERT with Logistic Regression on identical test records. Logistic Regression is deterministic, so it has a single score.

| Seed | Epochs chosen (validation) | Validation macro-F1 | Test macro-F1 | Difference vs. LR | 95% CI of difference (study bootstrap) | BioBERT-only correct | LR-only correct | McNemar *p* |
|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| 1 | 6 | 0.806 | **0.937** | +0.072 | +0.004 to +0.141 | 18 | 4 | **0.004** |
| 2 | 5 | 0.842 | 0.921 | +0.056 | −0.000 to +0.112 | 15 | 4 | **0.019** |
| 3 | 6 | 0.813 | 0.901 | +0.036 | −0.029 to +0.105 | 18 | 11 | 0.265 |
| 4 | 2 | 0.877 | 0.889 | +0.024 | −0.038 to +0.073 | 11 | 6 | 0.332 |
| **143** (canonical) | 3 | 0.838 | 0.879 | +0.014 | −0.054 to +0.069 | 13 | 10 | 0.678 |
| **Mean ± SD** | | | **0.905 ± 0.024** | **+0.040** | **−0.016 to +0.093** (seed-averaged) | | | |

![BioBERT across seeds vs. Logistic Regression](../clinicaltrials-ml/results/biobert_vs_lr_seeds.png)

*In the figure, each error bar shows the 95% CI of that seed's difference from Logistic Regression, drawn so that a bar crossing the blue line means "not distinguishable from LR."*

**What this shows**

1. **BioBERT scores higher than Logistic Regression on all 5 seeds,** by +0.014 to +0.072 macro-F1 (mean +0.040, about 8 fewer errors out of 191). The direction is consistent.
2. **The size of the advantage is uncertain.** The seed-averaged 95% interval for the difference (−0.016 to +0.093) includes zero. Only 2 of 5 seeds reach McNemar p < 0.05, and only 1 of 5 has a per-seed interval that excludes zero.
3. **Training randomness is as large as the gap.** BioBERT's test macro-F1 ranges from 0.879 to 0.937 depending only on the seed (SD 0.024). That spread is as large as the average advantage over LR. The earlier single-seed result of 0.906 sat in the middle of this range, so it was neither a lucky nor an unlucky run. A single run, however, could not have shown this.
4. **The validation set is too small to tune on.** With 25 records, validation macro-F1 was *negatively* correlated with test macro-F1 across seeds (r = −0.56). Seed 4 had the best validation score (0.877) but the second-worst test score. The chosen epoch count (2–6) therefore reflects validation noise more than true quality. This is the cost of a 76-record training set.

Against Naive Bayes and Linear SVM, the canonical seed-143 model also wins more disagreements than it loses (14 vs. 10 and 13 vs. 9), but neither difference is significant (McNemar p = 0.54 and 0.52).

**Answer:** on this data, BioBERT is **probably** better than Logistic Regression. It wins on every seed, by an average of 0.04 macro-F1. However, we **cannot** call it *reliably* better: the study-level uncertainty from a 54-study test set, together with seed-to-seed variance, is large enough that a true difference of zero cannot be ruled out.

### 5.5 Error analysis (canonical BioBERT, 23 errors)

| Pattern | Count | Examples |
|---|---:|---|
| Baseline measure read as Efficacy | 11 | *"Systolic blood pressure"*, *"triglyceride"*, *"HOMA-IR"*, *"Depressive Symptoms Score (PHQ-9)"*, *"Diabetes Self-efficacy Score"*, *"Food Insecurity Score (HFSSM)"* |
| Efficacy read as Safety | 5 | *"Major Adverse Cardiovascular Event (MACE-3)"*, *"Change in Kidney Function (Creatinine Clearance)"*, *"Time to Treatment Intensification"*, *"ADA Adherence Measures: Flu Vaccination"* |
| Safety read as Efficacy | 3 | *"Aspartate aminotransferase increased"*, *"Number of Clinically Significant Hypoglycaemic Episodes (Level 2)"*, *"Presence of Orthostatic Hypotension"* |
| Safety read as Baseline | 2 | *"Heart rate increased — Investigations"*, *"Rates of NICU Admission"* |
| Efficacy read as Baseline | 2 | *"Number of Participants With an eGFR Decline > 30%"*, *"Clinical Significant Hypoglycemia"* |

Most errors are **inherently ambiguous from the text alone**.

- *"Systolic blood pressure"* or a quality-of-life score is a Baseline measure in the baseline table, but the identical phrase is an Efficacy endpoint in the outcome table.
- MACE and kidney-function decline are efficacy endpoints in cardiovascular and renal outcome trials, but read like harms.
- One test record titled *"Clinical Significant Hypoglycemia"* is labeled **Efficacy**, while a near-identical hypoglycaemia outcome in another study is labeled **Safety**. Inconsistencies like this put a ceiling on any model's score.

These are exactly the overlaps the proposal anticipated. Section 7 suggests a direct fix.

---

## 6. Conclusion: Which Model Is Best and Why

**BioBERT is the best-performing model, but its margin over Logistic Regression is not statistically established.**

**Why BioBERT ranks first**

1. **Highest primary metric.** The pre-specified BioBERT model has the best macro-F1 of any single model (0.879). Averaged over five seeds BioBERT reaches 0.905, against 0.859–0.865 for the three TF-IDF models.
2. **Consistent across training runs.** BioBERT beat Logistic Regression on 5 of 5 seeds, and its worst seed still beat every linear model.
3. **Most balanced.** It has no weak class (5-seed mean F1 of 0.89 / 0.89 / 0.93), and its predicted label distribution is closest to the truth. Each linear model has one clear weakness: LR and NB over-predict Efficacy, and the SVM misses adverse events.
4. **The advantage has a clear cause.** Biomedical pre-training gives BioBERT prior knowledge of lab tests, adverse-event terms, and clinical phrasing that 76 training examples cannot teach a bag-of-words model. Its remaining errors are mostly on text that is genuinely ambiguous without the source section.

**Why the margin is not certain.** With leakage removed, BioBERT's lead over Logistic Regression is +0.040 macro-F1 on average. The 95% interval (−0.016 to +0.093) includes zero, seed-to-seed spread (0.879–0.937) is as large as the gap, and McNemar's test is significant for only 2 of 5 seeds. BioBERT is also much heavier: about 110 million parameters, several minutes of CPU training per run, and a 400 MB model file.

**Practical recommendation**

- **Use BioBERT** when the goal is the best expected accuracy, for example when pre-labeling large batches of outcome measures for reviewers. Average several seeds, or use a larger validation set, to reduce run-to-run variance.
- **Use TF-IDF + Logistic Regression** when speed, transparency, or explainability matter. It is the strongest classical model (macro-F1 0.865), trains in under a second, and its coefficients and probabilities make it easy to justify a label or flag uncertain records for review. Given the current evidence, choosing it costs at most a few points of macro-F1.
- Naive Bayes and Linear SVM add no advantage over Logistic Regression here.

---

## 7. Limitations and Future Work

- **Small labeled set.** We had 267 labeled records, with 76 used for training. That leaves only a 25-record validation set and a 54-study test set, which together explain why BioBERT's advantage cannot be confirmed statistically. Labeling more records is the most direct way to improve every model and settle the BioBERT-vs-LR question. Repeated grouped splits (for example, grouped cross-validation over all 267 records with several BioBERT seeds per fold) would also add evidence without new labeling.
- **Noisy validation-based tuning.** The epoch count chosen on 25 validation records did not track test performance (r = −0.56). A larger validation set, grouped cross-validation inside the training studies, or a fixed epoch count chosen before training would make BioBERT's tuning more reliable.
- **Text-only input.** The most common errors would likely disappear if the model also saw the **source section** (baseline table, outcome measure, or adverse-event table) as a feature, for example by prepending `[OUTCOME]` to the text. We excluded it to test the text alone, but it is available, legitimate information.
- **One-year window.** The Results First Posted window covers a single year, which supports a month-level description but not trend claims. Repeating the pipeline over several years would make Goal 2's trend analysis meaningful.
- **Labels partly follow the source section.** The quality-check rules label baseline-table records as Baseline and adverse-event records as Safety. Labels are therefore not fully independent of record structure, and the classifiers may learn a section's writing style instead of its clinical meaning. The workbook flags this as a training caution. The 8 outcome measures relabeled Safety and the 33 excluded unclear records are the cases where human judgment went beyond the section rule. A few similar outcomes, such as the hypoglycaemia measures, received different labels in different studies.
- **Changing source data.** ClinicalTrials.gov records are updated over time. Our raw JSON snapshot and retrieval date (2026-11-05) are the reference for reproducing these results.

---

## 8. Reproducibility

All code is in `clinicaltrials-ml/src/` and should be run in numeric order. Seed 143 is used for every split and as the canonical BioBERT seed.

| Step | Scripts |
|---|---|
| Collect and screen | `01_test_api.py` – `05_assign_studies.py` |
| Extract and clean | `06_extract_measures.py` – `09_prepare_text.py` |
| Label | `10_prepare_labels.py`, `11_create_label_sample.py` → reviewed in `screening/Clinical_Trials_Model_Ready_T2D_Exclusions_Applied.xlsx` → `screening/model_ready_267.csv` |
| Split | `12_prepare_train_test.py` |
| Train | `13_train_logistic_regression.py`, `13.1_train_BioBert.py` (validation split + 5 seeds, about 40 minutes on CPU; pass seed numbers as arguments to run a subset), `13.2_train_linear_svm.py`, `14_analyze_predictions.py` (Naive Bayes + error files) |
| Evaluate and visualize | `15_compare_models.py` (cross-validation → `model_comparison.csv`; held-out test → `model_test_results.csv`), `16_visualize_results.py`, `17_report_figures.py` (baseline, bootstrap CIs, per-class F1, monthly category figure), `18_compare_biobert_lr.py` (seed-level BioBERT vs. LR tests) |

Key outputs: `data/processed/model_comparison.csv` (5-fold grouped CV), `data/processed/model_test_results.csv` (held-out test), `data/processed/biobert_seed_results.csv`, `data/processed/biobert_seeds/`, `data/processed/biobert_training_log.txt`, `data/processed/*_classification_report.txt`, `data/processed/*_mistakes.csv`, `results/report_summary_metrics.csv`, `results/biobert_vs_lr.csv`, `results/*.png`.
