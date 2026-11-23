# Mining Type 2 Diabetes Clinical Trial Results

**DSC 521 | Ashley Dees and Caroline Pearson | Fall 2026**

This is my working branch for our clinical trials machine learning project. Caroline and I worked together on the study screening and labeling, and I focused on getting the ClinicalTrials.gov data into a format we could actually use to train and evaluate a text classifier. We used our own branches while working and will use [main](../../tree/main) for the combined project.

## What we were trying to do

A measurement in a clinical trial doesn't always fit neatly into a category just because of its name. For example, HbA1c at the start of a study is a baseline measurement, while the change in HbA1c after treatment might be an efficacy outcome. We wanted to see whether a machine learning model could recognize the difference from the measurement's title and description.

Our three labels were:
- **Baseline:** participant characteristics at the beginning of a study
- **Efficacy:** measurements of an intervention's intended benefit
- **Safety:** adverse events, side effects, and tolerability

We weren't trying to decide whether a drug works or is safe. We were classifying what kind of measurement was being reported.

## Getting the data ready

We queried the [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api) for Type 2 diabetes studies with results first posted between **November 3, 2025, and November 2, 2026**. We retrieved the data on November 5, 2026, and screened the studies against our eligibility rules.

We started with **121 studies** and kept **89** after screening. Those studies contained **6,943 measurement records**. Most came from adverse-event sections, so simply drawing a random sample would have given us a lot more adverse events than the other types. Instead, we sampled **100 records from each source section**, for 300 records to label.

We divided those records for review, used consistent label definitions, and checked the results for mistakes and unclear cases. The quality-check process included rule-guided assistance, so I wouldn't describe all of the final labels as independently clinically verified. We removed 33 sampled records, including records from a Type 1 diabetes study that was identified during review. That left **267 labeled measurements from 76 studies**:

| Label | Records |
| --- | ---: |
| Baseline | 92 |
| Efficacy | 86 |
| Safety | 89 |

One thing I found interesting was that some measurements in the outcome section belonged in Safety. The source section was helpful, but it wasn't enough by itself to determine the label.

## The models I worked on

I combined each measurement's title and available description into a text field and used **TF-IDF** to turn that text into numerical features. The vectorizer learned its vocabulary from the training set only, so it didn't get information from the test set.

I started with **Logistic Regression** because it's a good, fairly interpretable baseline for text classification. I also compared it with **Multinomial Naive Bayes**, which uses a different probabilistic approach and trains quickly.

To avoid data leakage, I used `GroupShuffleSplit` with the study's **NCT ID** as the group. That keeps all measurements from the same study together instead of letting related records end up on both sides of the train/test split. I used random seed **143** to make the split repeatable.

On this branch, the original split has **210 training records from 60 studies** and **57 test records from 16 studies**.

## Results from my original run

| Model | Five-fold grouped CV accuracy | Five-fold grouped CV macro-F1 |
| --- | ---: | ---: |
| Logistic Regression | 0.8509 | 0.8412 |
| Naive Bayes | 0.8505 | 0.8396 |

The original Logistic Regression model correctly classified **47 of 57 test records (82.46%)**. Nine of its ten mistakes were Baseline records predicted as Efficacy. That's a useful example of the limitation we ran into: a short title like BMI or HbA1c often doesn't explain when or why the measurement was taken.

These are **my initial experiments**, not the final presentation scores. We later used a different **70/30 study split (189 training / 78 testing records)** for the team report. The final model comparisons are documented in the report on Caroline's branch and will be consolidated into main.

## Where the work is

- `src/01_...` through `src/11_...`: API collection, study screening, measurement extraction, preparation, and label sampling
- `screening/`: study reviews, labeling workbooks, and `model_ready_267.csv`
- `src/12_prepare_train_test.py`: study-grouped train/test split
- `src/13_train_logistic_regression.py`: TF-IDF and Logistic Regression training
- `src/14_analyze_predictions.py`: prediction errors and saved test predictions
- `src/15_compare_models.py`: grouped cross-validation of the classical models
- `src/16_visualize_results.py`: comparison plot and confusion matrix
- `results/`: graphs from this branch

To run the modeling scripts on this branch, start in the repository root and use the numbered scripts in order. You'll need Python with pandas, scikit-learn and matplotlib installed, plus the reviewed `screening/model_ready_267.csv`. Some downloaded raw records aren't committed to GitHub.

## What I'd improve next

We only labeled a small sample of the extracted measurements, and some labels were difficult to distinguish without additional context. More labeled examples, especially ambiguous ones, and information about **when** measurements occurred would probably help. I'd also want to test the approach on studies outside this collection window.

Caroline extended the project with **Linear SVM, BioBERT, additional evaluations, and the final report and slides**. We kept that work separate during development rather than overwriting each other's branches.
