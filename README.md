# Mining Type 2 Diabetes Clinical Trial Results

**DSC 521 — Machine Learning · November 2026**  
**Team:** Ashley Dees and Caroline Pearson  
**Branch:** `ashley` — initial data pipeline and classical ML experiments  
**Final team project:** See the [`main` branch](../../tree/main) once the reviewed integration is complete. Caroline's additional model experiments are preserved on [`caroline`](../../tree/caroline).

## Research question

Can supervised machine learning identify whether a Type 2 diabetes clinical-trial measurement describes **Baseline** participant characteristics, **Efficacy** outcomes, or **Safety** events from its title and description?

Clinical terminology overlaps between categories: HbA1c can be a baseline characteristic or an efficacy endpoint depending on timing and study design. **This project classifies the type of measurement; it does not assess whether a treatment works or is safe.**

## Data collection and review

- **Source:** [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)
- **Search:** `query.cond=Type 2 Diabetes` with `ResultsFirstPostDate` between **2025-11-03 and 2026-11-02**
- **Retrieved:** 2026-11-05; followed API pagination and retained study NCT IDs
- **Initial search:** 121 studies
- **Eligible after screening:** 89 studies
- **Extracted:** 6,943 measurement records from baseline, outcome, and adverse-event sections
- **Reviewed sample:** 300 measurements, sampled as 100 from each source section and divided for labeling
- **Final labeled dataset:** 267 measurements from 76 studies after 33 exclusions; **92 Baseline, 86 Efficacy, 89 Safety**

Screening excluded Type 1-only, prediabetes-only, incidental Type 2 diabetes without identifiable results, and studies lacking usable measurements. During labeling review, an incorrectly eligible Type 1 diabetes RADIANT study (NCT05923827) and unclear records were excluded. An additional rule-guided quality check helped identify inconsistent labels. Labels are not fully independent of their source sections, which is a limitation.

Original extracted records were not all manually labeled: the supervised model uses the **reviewed 267-record sample**, not all 6,943 extracted measurements.

## Machine learning approach on this branch

**Text preparation:** Combine measurement titles and available descriptions into the `text` column. Handle missing descriptions without treating missing information as evidence of a negative finding.

**Feature extraction:** `TfidfVectorizer(stop_words="english")` turns training text into weighted numerical word features. The vectorizer is fitted on training text only; the test set is transformed without fitting again.

**Classifiers:**
- **Logistic Regression:** `LogisticRegression(max_iter=1000, random_state=143)` — a linear, interpretable classifier.
- **Multinomial Naive Bayes:** `MultinomialNB()` — a fast probabilistic text classifier, used for comparison.

**Study-level holdout:** `GroupShuffleSplit(test_size=0.20, random_state=143)` groups on NCT ID, ensuring no study is shared between train and test. The original `ashley` branch has **210 training measurements from 60 studies** and **57 test measurements from 16 studies**.

**Model comparison:** Five-fold `StratifiedGroupKFold` cross-validation on the *training portion only*, also grouped by NCT ID.

### Original branch results

| Model | 5-fold grouped CV accuracy | 5-fold grouped CV macro-F1 |
| --- | ---: | ---: |
| Logistic Regression | 0.8509 | 0.8412 |
| Multinomial Naive Bayes | 0.8505 | 0.8396 |

Logistic Regression on the original held-out **57-record** test set: **47 correct, 10 incorrect (82.46% accuracy)**.

The main error pattern was Baseline being classified as Efficacy (9 of the 10 mistakes), illustrating how ambiguous wording and missing timing information affect text classification.

**Important:** These are the *initial* results on the `ashley` branch's 80/20 study split. The final report and presentation use a later **70/30 study split** (189 training / 78 test measurements) with expanded models and updated results. Do not compare test scores from these different partitions as if they used the same held-out data.

## Running the original pipeline

From the repository root, with Python dependencies installed in your environment:

```powershell
# Windows PowerShell, using an existing virtual environment
.\.venv\Scripts\python.exe src\12_prepare_train_test.py
.\.venv\Scripts\python.exe src\13_train_logistic_regression.py
.\.venv\Scripts\python.exe src\14_analyze_predictions.py
.\.venv\Scripts\python.exe src\15_compare_models.py
.\.venv\Scripts\python.exe src\16_visualize_results.py
```

These commands require `screening/model_ready_267.csv`, and the scripts use relative paths resolved from the repository root. To rebuild from source, inspect the numbered `src/01_...` through `src/11_...` files, screening rules, and reviewed label workbook. Install dependencies such as `pandas`, `numpy`, `scikit-learn`, and `matplotlib` before running the modeling scripts.

Generated output files include:
- `data/processed/train.csv`, `data/processed/test.csv`
- `data/processed/test_predictions.csv`, `data/processed/model_mistakes.csv`
- `data/processed/model_comparison.csv`
- `results/model_comparison.png`, `results/confusion_matrix.png`

Some downloaded source data and generated files are omitted by `.gitignore`; do not assume every run can be reproduced without the documented retrieval and labeling steps.

## Repository organization

- `src/` — numbered scripts for retrieval, screening, text preparation, splitting, model fitting, analysis, and plots
- `screening/` — eligibility review, measurement-label review, and final 267-record labeled sample
- `data/processed/` — extracted and prepared measurements; selected evaluation CSVs
- `results/` — model-comparison and confusion-matrix plots

## Limitations

This is a small reviewed training sample. Source-section writing style can influence the labels and learned patterns. Short titles may omit collection timing, making Baseline versus Efficacy ambiguous. The one-year retrieval window does not support broad claims about long-term reporting trends. Performance on other conditions or independent clinical-trial corpora remains untested.

## Team integration

This branch preserves the initial experiments and code. The [`caroline` branch](../../tree/caroline) adds Linear SVM, fine-tuned BioBERT, expanded evaluation, reporting figures, and the presentation. The [`main` branch](../../tree/main) is intended to be the reviewed, consolidated version for the DSC 521 presentation and faculty review.
