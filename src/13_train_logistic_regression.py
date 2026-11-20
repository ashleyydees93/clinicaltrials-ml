
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Load training and testing data
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

# Train Logistic Regression
model = LogisticRegression(max_iter=1000, random_state=143)
model.fit(X_train_tfidf, y_train)

# Predict labels for testing data
predictions = model.predict(X_test_tfidf)

# Evaluate model performance
accuracy = accuracy_score(y_test, predictions)

print("Model: TF-IDF + Logistic Regression")
print("Training records:", len(train))
print("Testing records:", len(test))
print("Accuracy:", round(accuracy, 4))

print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))

print("\nConfusion Matrix:")
labels = ["Baseline", "Efficacy", "Safety"]
print(confusion_matrix(y_test, predictions, labels=labels))
