
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Load training and testing datasets
train = pd.read_csv("data/processed/train.csv")
test = pd.read_csv("data/processed/test.csv")

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
    "data/processed/test_predictions.csv",
    index=False
)

# Save incorrect predictions
mistakes.to_csv(
    "data/processed/model_mistakes.csv",
    index=False
)

print("\nFiles saved successfully!")
