# Mining Type 2 Diabetes Clinical Trial Results
## Final Project Report — Caroline Pearson and Ashley Dees
**DSC 521 · November 2026**

---

## Abstract

We collected every Type 2 diabetes study on ClinicalTrials.gov whose results were first posted between **November 3, 2025 and November 2, 2026** (121 studies) and screened them with written eligibility rules (89 eligible). From these studies we extracted **6,943 measurement records** (baseline characteristics, outcome measures, and adverse events). We then manually labeled a stratified sample as **Baseline**, **Efficacy**, or **Safety**, which gave 267 model-ready records from 76 studies. We trained four text classifiers: TF-IDF + Logistic Regression, TF-IDF + Multinomial Naive Bayes, TF-IDF + Linear SVM, and fine-tuned **BioBERT**. We trained on 189 records from 53 studies and evaluated on **78 records from 23 held-out studies** that were never seen in training. All four models far outperform the most-frequent-class baseline (macro-F1 0.147). The three TF-IDF models were nearly tied, with macro-F1 between 0.879 and 0.890. BioBERT's settings were chosen on validation studies only, never the test set, and it was trained with five random seeds. It **performed best**, with a macro-F1 of 0.932 ± 0.015 across seeds (0.928 for the pre-specified seed). BioBERT beat Logistic Regression (0.879) on all five seeds, by +0.053 macro-F1 on average, and the seed-averaged 95% study-level confidence interval for that gap (+0.004 to +0.117) excludes zero. BioBERT is therefore better than Logistic Regression on this data, although the lower end of the interval is close to zero and the exact size of the advantage is uncertain with a 23-study test set.

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
| Training split | 53 | 189 |
| Held-out test split | 23 | 78 |

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

We held out 30% of studies for testing (23 studies, 78 records) and trained on the remaining 53 studies (189 records). Training labels are close to balanced (61 Baseline, 61 Efficacy, 67 Safety), as are test labels (31 Baseline, 25 Efficacy, 22 Safety). This keeps most of our limited labeled data for training. The trade-off is a smaller test set, so the confidence intervals in §5 are wide and the errors can cluster within a few studies.

### 4.2 Features

The three classical models use **TF-IDF** on `title + description`, with English stop words removed. The Linear SVM also uses unigrams and bigrams with `min_df = 2`. BioBERT uses its own WordPiece tokenizer (cased, truncated at 256 tokens, with dynamic padding).

### 4.3 Models and why each fits this data

| Model | Configuration | Why it suits this data |
|---|---|---|
| **Most-frequent class** (baseline) | Always predicts the majority training class (*Safety*) | The comparison required by the proposal. It shows what "no learning" scores. |
| **Logistic Regression** | `TfidfVectorizer(stop_words="english")` → `LogisticRegression(max_iter=1000)` | The standard strong baseline for short-text classification. It handles high-dimensional sparse TF-IDF features well with L2 regularization, so it resists overfitting with only 189 training rows. Its coefficients are **interpretable**. In our trained model, the top Baseline words are *age, continuous, sex, ethnicity, female, male, race*. The top Efficacy words are *change, baseline, week, participants, glucose, medication, weight*: the word "baseline" points to Efficacy because of the phrase *"change from baseline."* The top Safety words are MedDRA organ-system terms such as *disorders, gastrointestinal, infestations, infections, cardiac, injury*. It also outputs probabilities that can flag uncertain records for human review. This was the model named in our original plan. |
| **Multinomial Naive Bayes** | `TfidfVectorizer(stop_words="english")` → `MultinomialNB()` | A generative model that estimates one word distribution per class. It needs very little data to fit, which makes it a natural fit for a 189-record training set. It trains in milliseconds and gives a second simple, transparent reference point. Its word-independence assumption is a reasonable approximation for short measurement titles. |
| **Linear SVM** | `TfidfVectorizer(ngram_range=(1,2), min_df=2)` → `LinearSVC(C=1.0)` | Maximum-margin classifiers are among the strongest classical methods for sparse text. **Bigrams** capture phrases that single words miss, such as *"change from baseline"*, *"adverse events"*, and *"serious adverse"*. The SVM tests whether adding phrase context to a linear model closes the gap with a deep model. |
| **BioBERT** | `dmis-lab/biobert-base-cased-v1.1`, lr 2e-5, batch 8, weight decay 0.01, epoch count (1–6) selected on validation studies, 5 training seeds (CPU only); see §4.4 | A BERT model pre-trained on PubMed abstracts and PMC full-text articles, so it already **knows biomedical vocabulary**: drug names, lab tests (*aspartate aminotransferase*), MedDRA adverse-event terms, and clinical phrasing. Transfer learning lets it use that knowledge with only 189 labeled examples. Unlike bag-of-words models, it reads **word order and context**, which matters when the same term can be baseline, efficacy, or safety. With so few training rows, CPU-only fine-tuning was practical. |

Every trained model is saved: the classical models to `data/processed/models/*.joblib`, and BioBERT to `data/processed/biobert_results/best_model`.

### 4.4 BioBERT training protocol (no test-set selection, multiple seeds)

An earlier version of the BioBERT script passed the test set as its evaluation set, so `load_best_model_at_end` chose the checkpoint by test loss. That version was also run with only one seed. To get a fair comparison with Logistic Regression, `13.1_train_BioBert.py` now works like this:

1. **Validation split from training studies only.** We hold out 30% of the 53 training studies (16 studies, 60 records: 20 Baseline, 20 Efficacy, 20 Safety), grouped by NCT ID. That leaves 37 studies and 129 records for fitting. The test set plays no part in any choice.
2. **Stage 1, choosing the epoch count.** The model trains on the 129 fit records for up to 6 epochs and is scored on the validation studies after each one. The epoch count with the best validation macro-F1 is kept, with ties broken by lower validation loss.
3. **Stage 2, retraining.** The model restarts from the pre-trained BioBERT weights and trains on **all 189 training records** for the chosen number of epochs. BioBERT therefore sees exactly the same training data as the TF-IDF models.
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

### 5.1 Overall performance (held-out test set: 78 records, 23 studies)

| Model | Accuracy | **Macro-F1** | 95% CI (macro-F1) | Weighted-F1 | Micro-F1 | Error rate | Errors |
|---|---:|---:|:---:|---:|---:|---:|---:|
| Most-frequent class | 0.282 | 0.147 | 0.033 – 0.207 | 0.124 | 0.282 | 0.718 | 56 |
| Logistic Regression | 0.872 | 0.879 | 0.743 – 0.971 | 0.871 | 0.872 | 0.128 | 10 |
| Naive Bayes | 0.872 | 0.879 | 0.743 – 0.971 | 0.871 | 0.872 | 0.128 | 10 |
| Linear SVM | 0.885 | 0.890 | 0.753 – 0.976 | 0.885 | 0.885 | 0.115 | 9 |
| **BioBERT** (canonical seed 143) | **0.923** | **0.928** | 0.830 – 1.000 | **0.923** | **0.923** | **0.077** | **6** |
| *BioBERT, mean of 5 seeds* | *0.928 ± 0.015* | *0.932 ± 0.015* | — | *0.928* | *0.928* | *0.072* | *5.6* |

![Macro-F1 vs. most-frequent-class baseline](../clinicaltrials-ml/results/macro_f1_vs_baseline.png)

Every learned model improves macro-F1 by more than **0.73** over the majority-class baseline. The pre-specified BioBERT model (seed 143) is the best single model at 0.928, with 6 errors against 9–10 for the TF-IDF models. Averaged over five training seeds BioBERT reaches **0.932**, about 5.6 errors against 10 for Logistic Regression. Seed 143 falls in the middle of the five seeds (§5.4).

Naive Bayes and Logistic Regression made **exactly the same prediction on all 78 test records**, so their rows are identical. They are separate models trained separately, but on this test set they agree record for record.

The confidence intervals are wide (for example, 0.743–0.971 for Logistic Regression) because the test set holds only 23 studies, and several errors come from the same study. The intervals for all four models overlap.

#### Cross-validation on the training set (TF-IDF models)

As a second check that does not use the test set, `15_compare_models.py` runs **5-fold grouped cross-validation** (`StratifiedGroupKFold`, grouped by NCT ID) on the 189 training records. Each fold trains on about 151 records and is scored on the remaining 10–11 studies. BioBERT is not included, because each BioBERT fit takes minutes on CPU (see §4.4 for its own validation design).

| Model | Accuracy (mean ± SD) | **Macro-F1** (mean ± SD) | Weighted-F1 | Micro-F1 | Error rate |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.841 ± 0.096 | 0.827 ± 0.112 | 0.838 | 0.841 | 0.159 |
| Naive Bayes | 0.842 ± 0.095 | **0.828 ± 0.112** | 0.839 | 0.842 | 0.158 |
| Linear SVM | 0.837 ± 0.069 | 0.826 ± 0.079 | 0.837 | 0.837 | 0.163 |

![Cross-validation model comparison](../clinicaltrials-ml/results/model_comparison.png)

In cross-validation the three classical models are **essentially tied**, within 0.002 macro-F1 of each other. On the held-out test set Linear SVM is slightly ahead (0.890 against 0.879), a difference of one record. Both evaluations agree that no classical model is clearly better than the others. The Linear SVM varies least from fold to fold (macro-F1 SD 0.079 against 0.112).

The Linear SVM uses `min_df = 2`. With about 151 training records per fold, that setting keeps only about 540 of roughly 1,980 unigram and bigram terms, a cut of about 73%. In a training-set-only check, dropping the filter (`min_df = 1`) raised the SVM's CV macro-F1 only slightly, from 0.826 to 0.837. We kept the original SVM settings rather than re-tuning after test results were available.

### 5.2 Per-class performance

| Model | Baseline P / R / F1 | Efficacy P / R / F1 | Safety P / R / F1 |
|---|---|---|---|
| Logistic Regression | **1.00** / 0.71 / 0.83 | 0.73 / 0.96 / 0.83 | 0.96 / **1.00** / **0.98** |
| Naive Bayes | **1.00** / 0.71 / 0.83 | 0.73 / 0.96 / 0.83 | 0.96 / **1.00** / **0.98** |
| Linear SVM | 0.96 / 0.77 / 0.86 | 0.77 / 0.96 / 0.86 | 0.95 / 0.95 / 0.95 |
| **BioBERT** (seed 143) | 0.96 / **0.84** / **0.90** | **0.83** / **1.00** / **0.91** | **1.00** / 0.95 / **0.98** |
| *BioBERT F1, 5-seed mean (range)* | *0.90 (0.88–0.93)* | *0.92 (0.91–0.93)* | *0.97 (0.95–1.00)* |

![Per-class F1 by model](../clinicaltrials-ml/results/per_class_f1_by_model.png)

- **BioBERT** has the best or tied-best F1 in every class, with no class below 0.90 for seed 143 (5-seed means of 0.90 / 0.92 / 0.97). It found every Efficacy record (recall 1.00) and labeled nothing as Safety that was not Safety (precision 1.00).
- **Logistic Regression and Naive Bayes** over-predict *Efficacy*. They predicted 33 Efficacy labels when only 25 are true. Nine Baseline records were pulled into Efficacy, which drops Baseline recall to 0.71 and Efficacy precision to 0.73. Both are perfect on Safety recall.
- **Linear SVM** pulls fewer Baseline records into Efficacy (7 instead of 9), raising Baseline recall to 0.77. It also keeps Safety recall high (0.95): only 1 Safety record (*"Aspartate aminotransferase increased"*) was labeled Baseline.
- **Every model's weakest point is Baseline recall.** Short baseline titles and questionnaire scores look like efficacy endpoints, which is the core ambiguity of this task (§5.5).

### 5.3 Confusion matrices (rows = true label, columns = predicted)

| True ↓ / Pred → | LR: B / E / S | NB: B / E / S | SVM: B / E / S | **BioBERT (seed 143): B / E / S** |
|---|:---:|:---:|:---:|:---:|
| Baseline (31) | 22 / 9 / 0 | 22 / 9 / 0 | 24 / 7 / 0 | **26 / 5 / 0** |
| Efficacy (25) | 0 / 24 / 1 | 0 / 24 / 1 | 0 / 24 / 1 | **0 / 25 / 0** |
| Safety (22) | 0 / 0 / 22 | 0 / 0 / 22 | 1 / 0 / 21 | **1 / 0 / 21** |

| BioBERT (seed 143) | Logistic Regression |
|---|---|
| ![BioBERT confusion matrix](../clinicaltrials-ml/results/confusion_matrix_biobert.png) | ![Logistic Regression confusion matrix](../clinicaltrials-ml/results/confusion_matrix_logistic_regression.png) |
| **Linear SVM** | **Naive Bayes** |
| ![Linear SVM confusion matrix](../clinicaltrials-ml/results/confusion_matrix_linear_svm.png) | ![Naive Bayes confusion matrix](../clinicaltrials-ml/results/confusion_matrix_naive_bayes.png) |

`results/labeling_frequencies_by_model.png` compares each model's predicted label counts with the true test distribution. BioBERT's predicted counts (27 / 30 / 21) are closest to the true counts (31 / 25 / 22). Linear SVM is next at 25 / 31 / 22, and Logistic Regression and Naive Bayes are both at 22 / 33 / 23.

### 5.4 Is BioBERT truly better than Logistic Regression?

With selection moved to validation studies and five training seeds, we compared BioBERT with Logistic Regression on identical test records. Logistic Regression is deterministic, so it has a single score.

| Seed | Epochs chosen (validation) | Validation macro-F1 | Test macro-F1 | Difference vs. LR | 95% CI of difference (study bootstrap) | BioBERT-only correct | LR-only correct | McNemar *p* |
|---:|---:|---:|---:|---:|:---:|---:|---:|---:|
| 1 | 3 | 0.883 | 0.926 | +0.047 | −0.011 to +0.116 | 5 | 1 | 0.219 |
| 2 | 6 | 0.883 | 0.939 | +0.061 | **+0.001 to +0.146** | 6 | 1 | 0.125 |
| 3 | 4 | 0.867 | **0.952** | +0.074 | **+0.024 to +0.148** | 6 | 0 | **0.031** |
| 4 | 1 | 0.886 | 0.913 | +0.035 | −0.025 to +0.089 | 4 | 1 | 0.375 |
| **143** (canonical) | 4 | 0.851 | 0.928 | +0.049 | −0.001 to +0.128 | 5 | 1 | 0.219 |
| **Mean ± SD** | | | **0.932 ± 0.015** | **+0.053** | **+0.004 to +0.117** (seed-averaged) | | | |

![BioBERT across seeds vs. Logistic Regression](../clinicaltrials-ml/results/biobert_vs_lr_seeds.png)

*In the figure, each error bar shows the 95% CI of that seed's difference from Logistic Regression, drawn so that a bar crossing the blue line means "not distinguishable from LR."*

**What this shows**

1. **BioBERT scores higher than Logistic Regression on all 5 seeds,** by +0.035 to +0.074 macro-F1 (mean +0.053, about 4 fewer errors out of 78). Even the weakest seed (0.913) beats every TF-IDF model.
2. **The advantage is statistically supported, but only just.** The seed-averaged 95% interval for the difference (+0.004 to +0.117) excludes zero, and so do the per-seed intervals for seeds 2 and 3. The lower end of the seed-averaged interval is very close to zero, though, and the per-seed interval for the canonical seed 143 (−0.001 to +0.128) just barely includes it.
3. **McNemar's test has little power here.** Only seed 3 reaches p < 0.05. BioBERT and Logistic Regression disagree on just 4–7 of the 78 records, and with so few disagreements McNemar's test cannot reach significance unless nearly all of them go one way. In every seed BioBERT won at least 4 times as many disagreements as it lost (for example, 5 vs. 1 for seed 143).
4. **Training randomness is smaller than the gap.** BioBERT's test macro-F1 ranges from 0.913 to 0.952 depending only on the seed (SD 0.015). That spread is smaller than its average advantage over Logistic Regression.
5. **The validation set is still a poor guide for tuning.** With 60 validation records, validation macro-F1 was *negatively* correlated with test macro-F1 across seeds (r = −0.29). Seed 4 had the best validation score (0.886) but the worst test score (0.913), and it stopped after only 1 epoch. The chosen epoch count (1–6) therefore reflects validation noise more than true quality.

Against Naive Bayes and Linear SVM, the canonical seed-143 model also wins more disagreements than it loses (5 vs. 1 and 4 vs. 1), but neither difference is significant (McNemar p = 0.22 and 0.38).

**Answer:** on this data, BioBERT is **better** than Logistic Regression. It wins on every seed, by an average of 0.053 macro-F1, and the seed-averaged study-level interval excludes zero. However, the lower end of that interval is close to zero and only 1 of 5 McNemar tests is significant, so the true size of the advantage could be quite small. A larger test set would be needed to pin it down.

### 5.5 Error analysis (canonical BioBERT, 6 errors)

| Pattern | Count | Examples |
|---|---:|---|
| Baseline measure read as Efficacy | 5 | *"Depressive Symptoms Score (PHQ-9)"*, *"Health-related Quality of Life Score (SF-12)"*, *"Food Insecurity Score (HFSSM)"*, *"Diabetes Self-efficacy Score"*, *"Diabetes Self-Efficacy Baseline"* |
| Safety read as Baseline | 1 | *"Heart rate increased — Investigations"* |

Most errors are **inherently ambiguous from the text alone**.

- Four of the six errors come from **one behavioral study** (NCT04959487), whose baseline table reports questionnaire scores for depression, quality of life, food insecurity, and self-efficacy. In behavioral trials, these same scores are usually efficacy endpoints, so without the source section or the timing of the measurement the text looks like an outcome.
- *"Diabetes Self-Efficacy Baseline"* was read as Efficacy even though it contains the word "baseline." The word "self-efficacy" likely pulled it toward Efficacy.
- *"Heart rate increased"* is an adverse event, but heart rate is also a common baseline vital sign.

The five Baseline → Efficacy records were **missed by all four models**. The TF-IDF models also missed short baseline titles that BioBERT got right. All three missed *"Hemoglobin A1c"* and *"Participants With Any Hospital Admissions (prior 6 months)"*, and Logistic Regression and Naive Bayes also missed *"BMI"* and *"Body Mass Index (BMI)"*. All three TF-IDF models labeled one efficacy outcome, *"Renal Oxidative Metabolism"* (a PET imaging measure), as Safety.

These are exactly the overlaps the proposal anticipated. Section 7 suggests a direct fix.

---

## 6. Conclusion: Which Model Is Best and Why

**BioBERT is the best-performing model, and its margin over Logistic Regression is statistically supported, though the size of that margin is uncertain.**

**Why BioBERT ranks first**

1. **Highest primary metric.** The pre-specified BioBERT model has the best macro-F1 of any single model (0.928). Averaged over five seeds BioBERT reaches 0.932, against 0.879–0.890 for the three TF-IDF models.
2. **Consistent across training runs.** BioBERT beat Logistic Regression on 5 of 5 seeds, and its worst seed (0.913) still beat every linear model. Seed-to-seed spread (SD 0.015) is smaller than its lead.
3. **Most balanced.** It has the best or tied-best F1 in every class (5-seed mean F1 of 0.90 / 0.92 / 0.97), and its predicted label distribution is closest to the truth. The linear models all share the same weakness: they pull too many Baseline records into Efficacy.
4. **The advantage has a clear cause.** Biomedical pre-training gives BioBERT prior knowledge of lab tests, adverse-event terms, and clinical phrasing that 189 training examples cannot teach a bag-of-words model. That is why it gets bare baseline titles such as *"Hemoglobin A1c"* and *"BMI"* right when the TF-IDF models do not. Its remaining errors are mostly on text that is genuinely ambiguous without the source section.

**Why the margin is uncertain.** BioBERT's lead over Logistic Regression is +0.053 macro-F1 on average, about 4 fewer errors on 78 records. The seed-averaged 95% interval (+0.004 to +0.117) excludes zero, but only barely, and McNemar's test is significant for only 1 of 5 seeds. With a 23-study test set where several errors come from the same study, the true advantage could be anywhere from very small to about 0.12. BioBERT is also much heavier: about 110 million parameters, several minutes of CPU training per run, and a 400 MB model file.

**Practical recommendation**

- **Use BioBERT** when the goal is the best expected accuracy, for example when pre-labeling large batches of outcome measures for reviewers. Averaging several seeds, or using a larger validation set, would reduce run-to-run variance.
- **Use TF-IDF + Logistic Regression** when speed, transparency, or explainability matter. It reaches a macro-F1 of 0.879, trains in under a second, and its coefficients and probabilities make it easy to justify a label or flag uncertain records for review. On the current evidence, choosing it costs about 0.05 macro-F1.
- Naive Bayes and Linear SVM add no meaningful advantage over Logistic Regression here. Naive Bayes made the same predictions, and the Linear SVM's one-record edge on the test set did not hold up in cross-validation.

---

## 7. Limitations and Future Work

- **Small labeled set.** We had 267 labeled records, with 189 used for training. That leaves a 60-record validation set and a 78-record, 23-study test set. The test set is small enough that the confidence intervals are wide (for example, 0.830–1.000 for BioBERT), a single record moves macro-F1 by about 0.01, and four of BioBERT's six errors come from one study. That is why BioBERT's advantage over Logistic Regression is only barely significant. Labeling more records is the most direct way to improve every model and pin down the size of the BioBERT-vs-LR gap. Repeated grouped splits (for example, grouped cross-validation over all 267 records with several BioBERT seeds per fold) would also add evidence without new labeling.
- **Noisy validation-based tuning.** The epoch count chosen on 60 validation records did not track test performance (r = −0.29), and the seed with the best validation score had the worst test score. A larger validation set, grouped cross-validation inside the training studies, or a fixed epoch count chosen before training would make BioBERT's tuning more reliable.
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
| Train | `13_train_logistic_regression.py`, `13.1_train_BioBert.py` (validation split + 5 seeds, about 35 minutes on CPU; pass seed numbers as arguments to run a subset), `13.2_train_linear_svm.py`, `14_analyze_predictions.py` (Naive Bayes + error files) |
| Evaluate and visualize | `15_compare_models.py` (cross-validation → `model_comparison.csv`; held-out test → `model_test_results.csv`), `16_visualize_results.py`, `17_report_figures.py` (baseline, bootstrap CIs, per-class F1, monthly category figure), `18_compare_biobert_lr.py` (seed-level BioBERT vs. LR tests) |

Key outputs: `data/processed/model_comparison.csv` (5-fold grouped CV), `data/processed/model_test_results.csv` (held-out test), `data/processed/biobert_seed_results.csv`, `data/processed/biobert_seeds/`, `data/processed/biobert_training_log.txt`, `data/processed/*_classification_report.txt`, `data/processed/*_mistakes.csv`, `results/report_summary_metrics.csv`, `results/biobert_vs_lr.csv`, `results/*.png`.
