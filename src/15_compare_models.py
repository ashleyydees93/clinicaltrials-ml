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
    f1_score,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ----------------------------------------------------------------------
# Part 1: 5-fold grouped cross-validation (training set only)
# ----------------------------------------------------------------------

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

cv_results = []

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

    cv_results.append({
        "Model": name,
        "Evaluation": "5-fold grouped CV (training set)",
        "Accuracy": scores["test_accuracy"].mean(),
        "Accuracy SD": scores["test_accuracy"].std(ddof=1),
        "Macro F1": scores["test_f1_macro"].mean(),
        "Macro F1 SD": scores["test_f1_macro"].std(ddof=1),
        "Weighted F1": scores["test_f1_weighted"].mean(),
        "Weighted F1 SD": scores["test_f1_weighted"].std(ddof=1),
        "Micro F1": scores["test_f1_micro"].mean(),
        "Micro F1 SD": scores["test_f1_micro"].std(ddof=1),
        "Error Rate": 1 - scores["test_accuracy"].mean(),
    })

cv_df = pd.DataFrame(cv_results)

print("Model Comparison (5-Fold Grouped Cross-Validation, training set)")
print(cv_df.drop(columns="Evaluation").round(4).to_string(index=False))

cv_df.to_csv(PROCESSED_DIR / "model_comparison.csv", index=False)

# ----------------------------------------------------------------------
# Part 2: Held-out test set (saved predictions from each training script)
# ----------------------------------------------------------------------

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
        PROCESSED_DIR / "biobert_results" / "best_model",
        "Epochs selected on validation studies (seed 143)",
    ),
}

test_results = []

for model_name, filename, slug in held_out_outputs:
    prediction_path = PROCESSED_DIR / filename
    if not prediction_path.exists():
        print(f"\nSkipping {model_name}: {filename} not found.")
        continue

    predictions = pd.read_csv(prediction_path)
    actual = predictions["label"]
    predicted = predictions["predicted_label"]

    # Per-label precision/recall/F1 report
    report_path = PROCESSED_DIR / f"{slug}_classification_report.txt"
    report_path.write_text(
        classification_report(actual, predicted, zero_division=0),
        encoding="utf-8"
    )

    confusion_path = PROJECT_ROOT / "results" / f"confusion_matrix_{slug}.png"
    artifact, best_loading = model_artifacts[model_name]

    test_results.append({
        "Model": model_name,
        "Evaluation": "Held-out test set",
        "Accuracy": accuracy_score(actual, predicted),
        "Macro F1": f1_score(actual, predicted, average="macro"),
        "Weighted F1": f1_score(actual, predicted, average="weighted"),
        "Micro F1": f1_score(actual, predicted, average="micro"),
        "Error Rate": 1 - accuracy_score(actual, predicted),
        "GPU Support": gpu_support if model_name == "BioBERT" else "Not applicable",
        "Model Saving": "Yes" if artifact.exists() else "Not detected",
        "Best-Model Loading": best_loading,
        "Label Prediction Report": str(report_path),
        "Confusion Matrix": (
            str(confusion_path) if confusion_path.exists() else "Not generated"
        ),
    })

test_df = pd.DataFrame(test_results)

print("\nModel Comparison (Held-out Test Set)")
print(test_df[["Model", "Accuracy", "Macro F1", "Weighted F1", "Micro F1",
               "Error Rate"]].round(4).to_string(index=False))

test_df.to_csv(PROCESSED_DIR / "model_test_results.csv", index=False)

print("\nSaved:")
print(" ", PROCESSED_DIR / "model_comparison.csv", "(cross-validation)")
print(" ", PROCESSED_DIR / "model_test_results.csv", "(held-out test)")
