
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

# Load the training dataset only
train = pd.read_csv("data/processed/train.csv")

X = train["text"].fillna("")
y = train["label"]
groups = train["nct_id"]

# Create our machine learning models
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=143
    ),
    "Naive Bayes": MultinomialNB()
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

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english")),
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
            "f1_macro": "f1_macro"
        }
    )

    results.append({
        "Model": name,
        "Accuracy": scores["test_accuracy"].mean(),
        "F1 Macro": scores["test_f1_macro"].mean()
    })

# Display comparison
results_df = pd.DataFrame(results)

print("\nModel Comparison (5-Fold Cross-Validation)")
print(results_df.round(4).to_string(index=False))

# Save results
results_df.to_csv(
    "data/processed/model_comparison.csv",
    index=False
)

print("\nResults saved successfully!")
