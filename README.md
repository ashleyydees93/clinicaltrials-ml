# Mining Type 2 Diabetes Clinical Trial Results

**Team:** Caroline Pearson and Ashley Dees  
**Status:** In progress — project setup  
**Course project:** Professor-approved proposal

## Project overview

Type 2 diabetes clinical trials report treatment benefits, participant characteristics, and safety outcomes using varied terminology. Our goal is to use data from [ClinicalTrials.gov](https://clinicaltrials.gov/) to organize study outcome information and train a machine learning model to categorize outcome measures.

We will collect studies through **ClinicalTrials.gov API v2** using a **rolling one-year window based on the Results First Posted date**. We will document the exact start and end dates, retrieval date, search query, and study eligibility rules when data collection begins.

**What the model will do:** Classify the *type of outcome measure* reported in a study. It will **not** determine whether a treatment is effective or safe.

## Professor-approved project goals

1. Create a reviewed sample of outcome measures labeled **baseline characteristics**, **efficacy**, or **safety**.
2. Summarize outcome-category frequencies and reporting patterns by **Results First Posted year**.
3. Train a **text classifier** to assign outcome categories.

The approved proposal defines our project scope. Supporting planning or evaluation notes are implementation guides, not replacements for the proposal.

## Data source and collection

- **Source:** [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)
- **Population:** Studies relevant to Type 2 diabetes, screened using documented eligibility rules
- **Time frame:** Rolling one-year Results First Posted window (exact dates to be recorded)
- **Study identifier:** NCT ID
- **Information to preserve where available:** Study details, outcome titles and descriptions, structured results, and adverse events
- **Provenance:** Retain original source records and note when data was retrieved

A missing field is **not** evidence that an outcome or adverse event did not occur.

## Machine learning approach

We plan to begin with a simple, interpretable supervised text-classification workflow:

1. Extract and clean outcome text from eligible studies.
2. Write labeling rules and manually review a sample for the three approved categories. Flag ambiguous or out-of-scope outcomes instead of guessing.
3. Convert outcome titles/descriptions into numeric text features using **TF-IDF**.
4. Train a **Logistic Regression** classifier.
5. Compare it with a **most-frequent-class** baseline (`DummyClassifier`).
6. Evaluate on held-out studies using **macro-F1** (primary metric) and **accuracy**.

**Preventing data leakage:** All outcome rows belonging to the same NCT ID must remain in the same data split. We must never put outcomes from one study in both training and testing.

The algorithms above are our initial implementation choices and may be refined if evaluation indicates a reason to do so, while preserving the approved goals.

## Planned workflow

- [ ] Set up the shared repository and local Python environments
- [ ] Finalize and document the rolling one-year search dates and eligibility criteria
- [ ] Query API v2, follow all pages, and save source records
- [ ] Extract outcome measures and audit missing or duplicate fields
- [ ] Agree on labeling rules and review outcome labels
- [ ] Split labeled data by NCT ID; train baseline and text classifier
- [ ] Evaluate results and examine classification errors
- [ ] Create category-frequency and Results First Posted year visualizations
- [ ] Document limitations and prepare the 20-minute presentation

## Planned repository structure

```text
clinicaltrials-ml/
├── README.md
├── data/
│   ├── raw/            # Original API responses (do not commit large/private data)
│   └── processed/      # Cleaned and labeled data
├── src/                # Collection, cleaning, and modeling scripts
├── notebooks/          # Exploratory analysis
├── figures/            # Saved charts
├── presentation/       # Slides and presentation notes
└── requirements.txt    # Python package dependencies (to be added)
```

These directories describe the **planned structure**; files and scripts will be added as work progresses.

## Working together remotely

Ashley and Caroline can use **VS Code on their own computers** while sharing code through GitHub.

1. **Pull** the latest changes before starting work.
2. Create a **new branch** for your task rather than both editing the same file on the main branch.
3. Make focused changes and commit with a meaningful message.
4. **Push** your branch and open a **pull request** for the other person to review.
5. Merge reviewed work into `main`; pull the updated `main` before beginning the next task.

Do not commit passwords, API tokens, virtual environments, or unnecessary large downloaded datasets. Use a `.gitignore` for local files. If we need to share larger data, we will agree on an appropriate shared location and document how to reproduce it.

## Reproducibility and research cautions

- Keep a record of the API query, retrieval date, date limits, screening decisions, and exclusion counts.
- Store NCT IDs so every outcome can be traced back to its study.
- Document ambiguous labels, missing information, and class imbalance.
- Use the same held-out studies when comparing the baseline and classifier.
- Report category counts and clearly state their denominators.
- Results First Posted trends describe **reporting records**, not changes in treatment effectiveness.
- A one-year collection window may span only one or two calendar years; interpret year-by-year comparisons cautiously.

## Final deliverables

- Reproducible data collection and preprocessing code
- Reviewed outcome-label dataset and labeling rules
- Trained classifier, baseline comparison, and evaluation results
- Outcome-category summaries and visualizations
- Project documentation and a **20-minute presentation**

## References

- [ClinicalTrials.gov](https://clinicaltrials.gov/)
- [ClinicalTrials.gov API documentation](https://clinicaltrials.gov/data-api/api)
- Scikit-learn documentation: [TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html), [Logistic Regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), and [GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)
