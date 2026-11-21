import importlib
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report


def ensure_package(module_name, pip_name=None):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            pip_name or module_name,
        ])
        return importlib.import_module(module_name)

datasets = ensure_package("datasets")
transformers = ensure_package("transformers")
ensure_package("torch")
ensure_package("accelerate")

Dataset = datasets.Dataset
BertTokenizer = transformers.BertTokenizer
BertForSequenceClassification = transformers.BertForSequenceClassification
TrainingArguments = transformers.TrainingArguments
Trainer = transformers.Trainer

# Load data
train = pd.read_csv("../data/processed/train.csv")
test = pd.read_csv("../data/processed/test.csv")

# Create label mapping
labels = sorted(train["label"].unique())

label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for label, idx in label2id.items()}

train["label_id"] = train["label"].map(label2id)
test["label_id"] = test["label"].map(label2id)

# Convert to Hugging Face datasets
train_ds = Dataset.from_pandas(
    train[["text", "label_id"]].rename(columns={"label_id": "label"})
)

test_ds = Dataset.from_pandas(
    test[["text", "label_id"]].rename(columns={"label_id": "label"})
)

# BioBERT model
MODEL_NAME = "dmis-lab/biobert-base-cased-v1.1"

tokenizer = BertTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=256
    )

train_ds = train_ds.map(tokenize, batched=True)
test_ds = test_ds.map(tokenize, batched=True)

# Load model
model = BertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

# Metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    return {
        "accuracy": accuracy_score(labels, predictions)
    }

# Training configuration
training_args = TrainingArguments(
    output_dir="../data/processed/biobert_results",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=test_ds,
    compute_metrics=compute_metrics
)

# Train
trainer.train()
trainer.save_model("../data/processed/biobert_results/best_model")

# Predict
predictions = trainer.predict(test_ds)
y_pred = np.argmax(predictions.predictions, axis=1)

# Results
print("\nBioBERT Results")
print("Accuracy:", accuracy_score(test["label_id"], y_pred))

print("\nClassification Report:")
print(
    classification_report(
        test["label_id"],
        y_pred,
        target_names=labels
    )
)

# Save predictions in the same format as the Logistic Regression analysis
test["predicted_label"] = [id2label[prediction] for prediction in y_pred]
test.to_csv(
    "../data/processed/test_predictions_biobert.csv",
    index=False
)

mistakes = test[test["label"] != test["predicted_label"]].copy()
mistakes.to_csv(
    "../data/processed/biobert_mistakes.csv",
    index=False
)

print("\nBioBERT prediction files saved:")
print("  ../data/processed/test_predictions_biobert.csv")
print("  ../data/processed/biobert_mistakes.csv")