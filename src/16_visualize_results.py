
import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

# Create a folder for our graphs
os.makedirs("results", exist_ok=True)

# ----------------------------------------
# Graph 1: Compare our machine learning models
# ----------------------------------------

# Load cross-validation results
comparison = pd.read_csv("data/processed/model_comparison.csv")

# Plot accuracy and Macro F1 side by side
comparison.plot(
    x="Model",
    y=["Accuracy", "F1 Macro"],
    kind="bar",
    figsize=(9, 5),
    rot=0
)

plt.title("Machine Learning Model Comparison")
plt.ylabel("Cross-Validation Score")
plt.xlabel("")
plt.ylim(0, 1)
plt.legend(["Accuracy", "Macro F1"])
plt.tight_layout()

plt.savefig("results/model_comparison.png", dpi=300)
plt.show()

# ----------------------------------------
# Graph 2: Logistic Regression confusion matrix
# ----------------------------------------

# Load predictions from our test dataset
test = pd.read_csv("data/processed/test_predictions.csv")

labels = ["Baseline", "Efficacy", "Safety"]

# Display actual versus predicted labels
ConfusionMatrixDisplay.from_predictions(
    test["label"],
    test["predicted_label"],
    labels=labels,
    cmap="Blues",
    values_format="d"
)

plt.title("Logistic Regression Confusion Matrix")
plt.tight_layout()

plt.savefig("results/confusion_matrix.png", dpi=300)
plt.show()

print("\nGraphs saved in the results folder!")
