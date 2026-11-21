
import pandas as pd
import joblib
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROCESSED_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load training and testing data
train = pd.read_csv(PROCESSED_DIR / "train.csv")
test = pd.read_csv(PROCESSED_DIR / "test.csv")

# Separate measurement text and labels
X_train = train["text"]
y_train = train["label"]

X_test = test["text"]
y_test = test["label"]

# Convert text into TF-IDF features
vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train Linear SVM
model = LinearSVC(
    C=1.0,
    random_state=143
)

model.fit(X_train_tfidf, y_train)

# Predict
predictions = model.predict(X_test_tfidf)

# Metrics
accuracy = accuracy_score(y_test, predictions)
macro_f1 = f1_score(y_test, predictions, average="macro")
weighted_f1 = f1_score(y_test, predictions, average="weighted")

print("Model: TF-IDF + Linear SVM")
print("Training records:", len(train))
print("Testing records:", len(test))

print("\nAccuracy:", round(accuracy, 4))
print("Macro F1:", round(float(macro_f1), 4))
print("Weighted F1:", round(float(weighted_f1), 4))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

print("\nConfusion Matrix:")
labels = ["Baseline", "Efficacy", "Safety"]

print(
    confusion_matrix(
        y_test,
        predictions,
        labels=labels
    )
)

# Save predictions in the same format as the other test-analysis scripts
test["predicted_label"] = predictions
test.to_csv(
    PROCESSED_DIR / "test_predictions_svm.csv",
    index=False
)

mistakes = test[test["label"] != test["predicted_label"]].copy()
mistakes.to_csv(
    PROCESSED_DIR / "svm_mistakes.csv",
    index=False
)

print("\nLinear SVM prediction files saved:")
print(" ", PROCESSED_DIR / "test_predictions_svm.csv")
print(" ", PROCESSED_DIR / "svm_mistakes.csv")

joblib.dump(
    (vectorizer, model),
    MODEL_DIR / "linear_svm.joblib"
)