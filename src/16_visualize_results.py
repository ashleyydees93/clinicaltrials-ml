
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Create a folder for our graphs
os.makedirs(RESULTS_DIR, exist_ok=True)

# ----------------------------------------
# Graph 1: Compare our machine learning models
# ----------------------------------------

# Load cross-validation results
comparison = pd.read_csv(PROCESSED_DIR / "model_comparison.csv")

# Plot accuracy and Macro F1 side by side
comparison.plot(
    x="Model",
    y=["Accuracy", "Macro F1", "Weighted F1", "Micro F1"],
    kind="bar",
    figsize=(11, 6),
    rot=0
)

plt.title("Machine Learning Model Comparison")
plt.ylabel("Cross-Validation Score")
plt.xlabel("")
plt.ylim(0, 1)
plt.legend(["Accuracy", "Macro F1", "Weighted F1", "Micro F1"])
plt.tight_layout()

plt.savefig(RESULTS_DIR / "model_comparison.png", dpi=300)
plt.show()

# ----------------------------------------
# Graph 1b: Error rate by model
# ----------------------------------------

if "Error Rate" not in comparison.columns:
    comparison["Error Rate"] = 1 - comparison["Accuracy"]

comparison.plot(
    x="Model",
    y="Error Rate",
    kind="bar",
    figsize=(9, 5),
    rot=0,
    legend=False,
    color="tomato"
)

plt.title("Error Rate by Model")
plt.ylabel("Error Rate")
plt.xlabel("")
plt.ylim(0, 1)

for index, value in enumerate(comparison["Error Rate"]):
    plt.text(
        index,
        value + 0.015,
        f"{value:.1%}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()
plt.savefig(
    RESULTS_DIR / "error_rate_by_model.png",
    dpi=300
)
plt.show()

# ----------------------------------------
# Graph 2: Prediction confusion matrices
# ----------------------------------------

labels = ["Baseline", "Efficacy", "Safety"]

prediction_outputs = [
    ("Logistic Regression", PROCESSED_DIR / "test_predictions.csv"),
    ("Naive Bayes", PROCESSED_DIR / "test_predictions_naive_bayes.csv"),
    ("BioBERT", PROCESSED_DIR / "test_predictions_biobert.csv"),
    ("Linear SVM", PROCESSED_DIR / "test_predictions_svm.csv"),
]

# ----------------------------------------
# Graph 3: Labeling frequencies by model
# ----------------------------------------

frequency_frames = []

actual_test = pd.read_csv(PROCESSED_DIR / "test.csv")
actual_counts = actual_test["label"].value_counts()
frequency_frames.append(
    pd.DataFrame({
        "Model": "Labeled data",
        "Label": actual_counts.index,
        "Count": actual_counts.values,
    })
)

for model_name, prediction_path in prediction_outputs:
    if not prediction_path.exists():
        continue

    prediction_test = pd.read_csv(prediction_path)
    counts = prediction_test["predicted_label"].value_counts()
    frequency_frames.append(
        pd.DataFrame({
            "Model": model_name,
            "Label": counts.index,
            "Count": counts.values,
        })
    )

frequency_table = pd.concat(frequency_frames, ignore_index=True)
frequency_table = (
    frequency_table
    .groupby(["Model", "Label"], as_index=False)["Count"]
    .sum()
)

all_labels = ["Baseline", "Efficacy", "Safety"]
frequency_table.to_csv(
    PROCESSED_DIR / "labeling_frequencies_by_model.csv",
    index=False
)

frequency_pivot = frequency_table.pivot(
    index="Label",
    columns="Model",
    values="Count"
).reindex(all_labels).fillna(0)

frequency_pivot.plot(
    kind="bar",
    figsize=(10, 6),
    rot=0
)
plt.title("Outcome Labeling Frequencies by Model")
plt.ylabel("Number of Held-Out Test Records")
plt.xlabel("Outcome Label")
plt.tight_layout()
plt.savefig(
    RESULTS_DIR / "labeling_frequencies_by_model.png",
    dpi=300
)
plt.show()

# Figure 4: Relative frequencies (percentages)
frequency_percent = (
    frequency_pivot.div(frequency_pivot.sum(axis=0), axis=1) * 100
)

frequency_percent.plot(
    kind="bar",
    figsize=(10, 6),
    rot=0
)
plt.title("Relative Outcome Labeling Frequencies by Model")
plt.ylabel("Percent of Held-Out Test Records")
plt.xlabel("Outcome Label")
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig(
    RESULTS_DIR / "labeling_frequencies_by_model_percent.png",
    dpi=300
)
plt.show()

for model_name, prediction_path in prediction_outputs:
    if not os.path.exists(prediction_path):
        continue

    test = pd.read_csv(prediction_path)

    ConfusionMatrixDisplay.from_predictions(
        test["label"],
        test["predicted_label"],
        labels=labels,
        cmap="Blues",
        values_format="d"
    )

    plt.title(f"{model_name} Confusion Matrix")
    plt.tight_layout()

    safe_name = model_name.lower().replace(" ", "_")
    plt.savefig(
        RESULTS_DIR / f"confusion_matrix_{safe_name}.png",
        dpi=300
    )
    plt.show()

    if model_name == "Logistic Regression":
        plt.savefig(RESULTS_DIR / "confusion_matrix.png", dpi=300)

print("\nGraphs saved in the results folder!")
