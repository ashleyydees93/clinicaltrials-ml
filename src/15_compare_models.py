
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Load the training dataset only
train = pd.read_csv(PROCESSED_DIR / "train.csv")

X = train["text"].fillna("")
y = train["label"]
groups = train["nct_id"]

# Create our machine learning models
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=143
    ),
    "Naive Bayes": MultinomialNB(),
    "Linear SVM": LinearSVC(
        C=1.0,
        random_state=143
    )
}

# Keep measurements from the same study together
cv = StratifiedGroupKFold(
    n_splits=5,
    shuffle=True,
    random_state=143
)

results = []

# Train and evaluate each model
for name, model in models.items():

    vectorizer_kwargs = {"stop_words": "english"}
    if name == "Linear SVM":
        vectorizer_kwargs.update({
            "ngram_range": (1, 2),
            "min_df": 2
        })

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(**vectorizer_kwargs)),
        ("model", model)
    ])

    scores = cross_validate(
        pipeline,
        X,
        y,
        groups=groups,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "f1_macro": "f1_macro",
            "f1_weighted": "f1_weighted",
            "f1_micro": "f1_micro"
        }
    )

    results.append({
        "Model": name,
        "Accuracy": scores["test_accuracy"].mean(),
        "Macro F1": scores["test_f1_macro"].mean(),
        "Weighted F1": scores["test_f1_weighted"].mean(),
        "Micro F1": scores["test_f1_micro"].mean(),
        "Error Rate": 1 - scores["test_accuracy"].mean()
    })

try:
    import torch
    gpu_support = "Yes" if torch.cuda.is_available() else "CPU only"
except ImportError:
    gpu_support = "Not installed"

held_out_outputs = [
    ("Logistic Regression", "test_predictions.csv", "logistic_regression"),
    ("Naive Bayes", "test_predictions_naive_bayes.csv", "naive_bayes"),
    ("Linear SVM", "test_predictions_svm.csv", "linear_svm"),
    ("BioBERT", "test_predictions_biobert.csv", "biobert"),
]

for model_name, filename, slug in held_out_outputs:
    prediction_path = PROCESSED_DIR / filename
    if not prediction_path.exists():
        continue

    predictions = pd.read_csv(prediction_path)
    actual = predictions["label"]
    predicted = predictions["predicted_label"]

    label_report = classification_report(
        actual,
        predicted,
        zero_division=0
    )
    report_path = PROCESSED_DIR / f"{slug}_classification_report.txt"
    report_path.write_text(label_report, encoding="utf-8")

    labels = sorted(actual.unique())
    confusion_path = PROJECT_ROOT / "results" / f"confusion_matrix_{slug}.png"
    confusion_exists = confusion_path.exists()

    held_out_row = {
        "Model": model_name,
        "Accuracy": accuracy_score(actual, predicted),
        "Macro F1": f1_score(actual, predicted, average="macro"),
        "Weighted F1": f1_score(actual, predicted, average="weighted"),
        "Micro F1": f1_score(actual, predicted, average="micro"),
        "Error Rate": 1 - accuracy_score(actual, predicted),
    }

    existing = next(
        (row for row in results if row["Model"] == model_name),
        None
    )
    if existing is not None:
        existing.update(held_out_row)
    else:
        results.append(held_out_row)

model_artifacts = {
    "Logistic Regression": (
        PROCESSED_DIR / "models" / "logistic_regression.joblib",
        "Not applicable",
    ),
    "Naive Bayes": (
        PROCESSED_DIR / "models" / "naive_bayes.joblib",
        "Not applicable",
    ),
    "Linear SVM": (
        PROCESSED_DIR / "models" / "linear_svm.joblib",
        "Not applicable",
    ),
    "BioBERT": (
        PROCESSED_DIR / "biobert_results",
        "Enabled with load_best_model_at_end",
    ),
}

for row in results:
    model_name = row["Model"]
    artifact, best_loading = model_artifacts.get(
        model_name,
        (None, "Not implemented"),
    )
    row["GPU Support"] = (
        gpu_support if model_name == "BioBERT" else "Not applicable"
    )
    row["Model Saving"] = (
        "Yes" if artifact is not None and artifact.exists() else "Not detected"
    )
    row["Best-Model Loading"] = best_loading

    report_path = PROCESSED_DIR / f"{model_name.lower().replace(' ', '_')}_classification_report.txt"
    row["Label Prediction Report"] = (
        str(report_path) if report_path.exists() else "Not generated"
    )

    confusion_path = (
        PROJECT_ROOT
        / "results"
        / f"confusion_matrix_{model_name.lower().replace(' ', '_')}.png"
    )
    row["Confusion Matrix"] = (
        str(confusion_path) if confusion_path.exists() else "Not generated"
    )

# Display comparison
results_df = pd.DataFrame(results)

print("\nModel Comparison (5-Fold Cross-Validation)")
print(results_df.round(4).to_string(index=False))

# Save results
results_df.to_csv(
    PROCESSED_DIR / "model_comparison.csv",
    index=False
)

print("\nResults saved successfully!")
