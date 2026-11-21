
import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROCESSED_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load training and testing datasets
train = pd.read_csv(PROCESSED_DIR / "train.csv")
test = pd.read_csv(PROCESSED_DIR / "test.csv")

# Separate measurement text and labels
X_train = train["text"]
y_train = train["label"]

X_test = test["text"]
y_test = test["label"]

# Convert text into numerical features
vectorizer = TfidfVectorizer(stop_words="english")

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train Logistic Regression model
model = LogisticRegression(max_iter=1000, random_state=143)
model.fit(X_train_tfidf, y_train)
joblib.dump(
    (vectorizer, model),
    MODEL_DIR / "logistic_regression.joblib"
)

# Predict labels for testing data
test["predicted_label"] = model.predict(X_test_tfidf)

# Find incorrect predictions
mistakes = test[test["label"] != test["predicted_label"]].copy()

# Count correct and incorrect predictions
print("Total test records:", len(test))
print("Correct predictions:", len(test) - len(mistakes))
print("Incorrect predictions:", len(mistakes))

# Display incorrectly classified measurements
print("\nIncorrectly classified measurements:")

print(
    mistakes[
        ["nct_id", "text", "label", "predicted_label"]
    ].to_string(index=False, max_colwidth=70)
)

# Save all predictions
test.to_csv(
    PROCESSED_DIR / "test_predictions.csv",
    index=False
)

# Train Naive Bayes and save predictions using the same test format
naive_vectorizer = TfidfVectorizer(stop_words="english")
X_train_naive = naive_vectorizer.fit_transform(X_train)
X_test_naive = naive_vectorizer.transform(X_test)
naive_model = MultinomialNB()
naive_model.fit(X_train_naive, y_train)
joblib.dump(
    (naive_vectorizer, naive_model),
    MODEL_DIR / "naive_bayes.joblib"
)

naive_test = test.copy()
naive_test["predicted_label"] = naive_model.predict(X_test_naive)
naive_test.to_csv(
    PROCESSED_DIR / "test_predictions_naive_bayes.csv",
    index=False
)

naive_mistakes = naive_test[
    naive_test["label"] != naive_test["predicted_label"]
].copy()
naive_mistakes.to_csv(
    PROCESSED_DIR / "naive_bayes_mistakes.csv",
    index=False
)

# Save incorrect predictions
mistakes.to_csv(
    PROCESSED_DIR / "model_mistakes.csv",
    index=False
)

# Report BioBERT predictions if they have been generated
biobert_path = PROCESSED_DIR / "test_predictions_biobert.csv"
try:
    biobert_test = pd.read_csv(biobert_path)
    biobert_mistakes = biobert_test[
        biobert_test["label"] != biobert_test["predicted_label"]
    ].copy()

    print("\nBioBERT test results:")
    print("Total test records:", len(biobert_test))
    print("Correct predictions:", len(biobert_test) - len(biobert_mistakes))
    print("Incorrect predictions:", len(biobert_mistakes))

    print("\nBioBERT incorrectly classified measurements:")
    print(
        biobert_mistakes[
            ["nct_id", "text", "label", "predicted_label"]
        ].to_string(index=False, max_colwidth=70)
    )

    biobert_mistakes.to_csv(
        PROCESSED_DIR / "biobert_mistakes.csv",
        index=False
    )
except FileNotFoundError:
    print(
        "\nBioBERT predictions not found. "
        "Run 13.1_train_BioBert.py to generate "
        "test_predictions_biobert.csv."
    )

# Report Linear SVM predictions if they have been generated
svm_path = PROCESSED_DIR / "test_predictions_svm.csv"
try:
    svm_test = pd.read_csv(svm_path)
    svm_mistakes = svm_test[
        svm_test["label"] != svm_test["predicted_label"]
    ].copy()

    print("\nLinear SVM test results:")
    print("Total test records:", len(svm_test))
    print("Correct predictions:", len(svm_test) - len(svm_mistakes))
    print("Incorrect predictions:", len(svm_mistakes))

    print("\nLinear SVM incorrectly classified measurements:")
    print(
        svm_mistakes[
            ["nct_id", "text", "label", "predicted_label"]
        ].to_string(index=False, max_colwidth=70)
    )

    svm_mistakes.to_csv(
        PROCESSED_DIR / "svm_mistakes.csv",
        index=False
    )
except FileNotFoundError:
    print(
        "\nLinear SVM predictions not found. "
        "Run 13.2_train_linear_svm.py to generate "
        "test_predictions_svm.csv."
    )

print("\nFiles saved successfully!")
