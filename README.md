# Mining Type 2 Diabetes Clinical Trial Results

**DSC 521 — Fall 2026**  
**Ashley Dees and Caroline Pearson**

## Our project

We wanted to find out whether machine learning could help organize the measurements reported in Type 2 diabetes clinical trials. The challenge is that the same clinical term can mean different things depending on the study. HbA1c measured before treatment is a baseline characteristic; change in HbA1c after treatment can be an efficacy outcome.

We trained text classifiers to sort measurement titles and descriptions into **Baseline, Efficacy, or Safety**. This is a classification project, **not** an attempt to determine whether a treatment is effective or safe.

## Data collection and labeling

We collected Type 2 diabetes study records through the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api), filtering on **Results First Posted** dates from **November 3, 2025, through November 2, 2026**. The data was retrieved on **November 5, 2026**.

Our search returned **121 studies**. After screening for relevant Type 2 diabetes results and usable measurements, we kept **89 studies** and extracted **6,943 records** from baseline characteristics, outcome measures, and adverse events.

Because almost 78% of the extracted records were adverse-event entries, we sampled **100 measurements from each source section**, then divided the 300-record sample for labeling. We used written definitions, reviewed unclear records, and used a rule-guided quality check to flag inconsistencies. We excluded 33 sampled records, including records from a Type 1 diabetes study, leaving **267 labeled measurements from 76 studies**:

| Category | Records |
| --- | ---: |
| Baseline | 92 |
| Efficacy | 86 |
| Safety | 89 |

The source section didn't always match the clinical label. For example, some entries in the outcomes section were actually safety measures.

## How we approached the machine learning

We used the measurement title and description as our input text. Our classical models used **TF-IDF** to convert that text into weighted numerical features. We compared **Logistic Regression**, **Multinomial Naive Bayes**, and **Linear SVM**. We also fine-tuned **BioBERT**, which starts with language representations learned from biomedical publications.

We split the dataset by **NCT study ID** rather than by individual measurement. That matters because measurements from the same trial often share wording; keeping studies together reduces the chance that the models see closely related records in both training and testing.

The final team analysis uses **189 training measurements from 53 studies** and **78 held-out measurements from 23 studies**, with seed **143** for reproducibility. We used **macro-F1** as the primary metric so all three classes count equally, as well as accuracy, confusion matrices, and grouped cross-validation for the classical models.

## Final report results

The following results are from our final report's **78-record held-out test set**, rather than Ashley's earlier development split:

| Model | Test accuracy | Macro-F1 |
| --- | ---: | ---: |
| Most-frequent-class baseline | 0.282 | 0.147 |
| Logistic Regression | 0.872 | 0.879 |
| Naive Bayes | 0.872 | 0.879 |
| Linear SVM | 0.885 | 0.890 |
| BioBERT (prespecified seed 143) | 0.923 | 0.928 |

BioBERT's mean macro-F1 across five training seeds was **0.932 ± 0.015**. It performed best on this test set, although the sample is small and the size of the improvement over Logistic Regression is uncertain. All three classical models were close to one another.

A recurring problem was **Baseline measurements being predicted as Efficacy**. We suspect that adding information about measurement timing could help with those cases.

## Code, report, and presentation

We worked separately on the [ashley branch](../../tree/ashley) and [caroline branch](../../tree/caroline). Ashley's branch contains the original collection, labeling, TF-IDF, Logistic Regression and Naive Bayes workflow. Caroline's branch contains the extended Linear SVM and BioBERT analysis, additional visualizations, and final presentation materials.

We are reviewing the changes before consolidating them on **main**. Until that merge is complete, some of the following paths are present on `caroline` rather than on `main`:

- `src/` — numbered scripts for collection, cleaning, labeling, model training, and evaluation
- `screening/` — reviewed eligibility and labeling files
- `data/processed/` — prepared data and selected model outputs
- `results/clinicaltrials_ml_final_report.pdf` — project report
- `results/clinicaltrials_ml_presentation.pdf` — presentation
- `results/` — figures and model comparison tables

For the full final report and slides **before the merge**, use [Caroline's results folder](../../tree/caroline/results).

To reproduce the analysis, start from the project root, install the dependencies appropriate for the scripts, and run the numbered files in order. Some raw API downloads and generated model outputs are not stored in GitHub; the source-data collection steps and reviewed label files should be used to regenerate the necessary inputs. The BioBERT experiments also require PyTorch and Hugging Face packages. Please note that some script paths still need a final portability check.

## Limitations and next steps

Our labeled dataset is small, and the labels partly follow how ClinicalTrials.gov organizes its records. Some measurements are ambiguous without study-specific context or timing. We also collected roughly one year of results postings, so the monthly summaries are descriptive rather than evidence of long-term trends.

If we continued this work, we'd label more difficult examples, add timing or study context, and test the models on new studies and other conditions.

## References

- [ClinicalTrials.gov](https://clinicaltrials.gov/)
- [ClinicalTrials.gov API documentation](https://clinicaltrials.gov/data-api/api)
- [scikit-learn](https://scikit-learn.org/stable/)
