
import importlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit


def ensure_package(module_name, pip_name=None):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pip_name or module_name,
        ])
        return importlib.import_module(module_name)


datasets = ensure_package("datasets")
transformers = ensure_package("transformers")
ensure_package("torch")
ensure_package("accelerate")

Dataset = datasets.Dataset
BertTokenizer = transformers.BertTokenizer
BertForSequenceClassification = transformers.BertForSequenceClassification
DataCollatorWithPadding = transformers.DataCollatorWithPadding
TrainingArguments = transformers.TrainingArguments
Trainer = transformers.Trainer
set_seed = transformers.set_seed

# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROCESSED_DIR / "biobert_results"
SEED_DIR = PROCESSED_DIR / "biobert_seeds"
SEED_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "dmis-lab/biobert-base-cased-v1.1"
SPLIT_SEED = 143                       # validation split (fixed across seeds)
SEEDS = [143, 1, 2, 3, 4]              # training seeds
CANONICAL_SEED = 143                   # decided before seeing any test result
VAL_FRACTION = 0.25
MAX_EPOCHS = 6
LEARNING_RATE = 2e-5
BATCH_SIZE = 8
WEIGHT_DECAY = 0.01
MAX_LENGTH = 256

# Optional: run a subset of seeds, e.g. `python 13.1_train_BioBert.py 143 1`
if len(sys.argv) > 1:
    SEEDS = [int(s) for s in sys.argv[1:]]

# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
train = pd.read_csv(PROCESSED_DIR / "train.csv")
test = pd.read_csv(PROCESSED_DIR / "test.csv")

labels = sorted(train["label"].unique())
label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for label, idx in label2id.items()}
train["label_id"] = train["label"].map(label2id)
test["label_id"] = test["label"].map(label2id)


def make_validation_split(df):
    """Group split of training studies; retry until every class is in both parts."""
    for attempt in range(100):
        splitter = GroupShuffleSplit(n_splits=1, test_size=VAL_FRACTION,
                                     random_state=SPLIT_SEED + attempt)
        fit_idx, val_idx = next(splitter.split(df, groups=df["nct_id"]))
        fit, val = df.iloc[fit_idx], df.iloc[val_idx]
        if set(fit["label"]) == set(labels) and set(val["label"]) == set(labels):
            return fit.copy(), val.copy()
    raise RuntimeError("Could not build a validation split containing all classes.")


fit_df, val_df = make_validation_split(train)
assert set(fit_df["nct_id"]).isdisjoint(val_df["nct_id"])
assert set(train["nct_id"]).isdisjoint(test["nct_id"])

print(f"Training studies: {train['nct_id'].nunique()} "
      f"-> fit {fit_df['nct_id'].nunique()} studies / {len(fit_df)} records, "
      f"validation {val_df['nct_id'].nunique()} studies / {len(val_df)} records")
print("Validation labels:", val_df["label"].value_counts().to_dict())
print("Test set:", len(test), "records (used once per seed, after selection)")

tokenizer = BertTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
collator = DataCollatorWithPadding(tokenizer=tokenizer)


def to_dataset(df):
    ds = Dataset.from_pandas(
        df[["text", "label_id"]].rename(columns={"label_id": "label"}),
        preserve_index=False,
    )
    return ds.map(
        lambda b: tokenizer(b["text"], truncation=True, max_length=MAX_LENGTH),
        batched=True,
    )


fit_ds, val_ds = to_dataset(fit_df), to_dataset(val_df)
full_train_ds, test_ds = to_dataset(train), to_dataset(test)


def compute_metrics(eval_pred):
    logits, y_true = eval_pred
    y_pred = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
    }


def new_model(seed):
    set_seed(seed)  # controls classifier-head initialisation and dropout
    return BertForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(labels), id2label=id2label, label2id=label2id,
    )


def make_args(seed, epochs, run_name, evaluate):
    return TrainingArguments(
        output_dir=str(OUTPUT_DIR / run_name),
        eval_strategy="epoch" if evaluate else "no",
        save_strategy="no",            # selection is done from the eval log
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=epochs,
        weight_decay=WEIGHT_DECAY,
        seed=seed,
        data_seed=seed,
        logging_strategy="epoch",
        report_to="none",
    )


# ------------------------------------------------------------------
# Train each seed
# ------------------------------------------------------------------
seed_rows = []

for seed in SEEDS:
    print(f"\n=========== Seed {seed} ===========")

    # Stage 1: choose the number of epochs on the validation studies
    stage1 = Trainer(
        model=new_model(seed),
        args=make_args(seed, MAX_EPOCHS, f"stage1_seed{seed}", evaluate=True),
        train_dataset=fit_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        compute_metrics=compute_metrics,
    )
    stage1.train()

    val_log = pd.DataFrame([
        {"epoch": int(round(e["epoch"])), "val_loss": e["eval_loss"],
         "val_accuracy": e["eval_accuracy"], "val_f1_macro": e["eval_f1_macro"]}
        for e in stage1.state.log_history if "eval_f1_macro" in e
    ])
    best = val_log.sort_values(["val_f1_macro", "val_loss"],
                               ascending=[False, True]).iloc[0]
    best_epochs = int(best["epoch"])
    print(val_log.round(4).to_string(index=False))
    print(f"Selected epochs: {best_epochs} "
          f"(val macro-F1 {best['val_f1_macro']:.4f}, val loss {best['val_loss']:.4f})")
    del stage1

    # Stage 2: retrain on all training studies for the selected epoch count
    stage2 = Trainer(
        model=new_model(seed),
        args=make_args(seed, best_epochs, f"stage2_seed{seed}", evaluate=False),
        train_dataset=full_train_ds,
        data_collator=collator,
    )
    stage2.train()

    # Single, final look at the test set for this seed
    logits = stage2.predict(test_ds).predictions
    y_pred = np.argmax(logits, axis=1)
    seed_test = test.drop(columns=["label_id"]).copy()
    seed_test["predicted_label"] = [id2label[p] for p in y_pred]
    seed_test.to_csv(SEED_DIR / f"test_predictions_seed{seed}.csv", index=False)

    acc = accuracy_score(test["label_id"], y_pred)
    macro = f1_score(test["label_id"], y_pred, average="macro")
    print(f"Seed {seed} test accuracy {acc:.4f}, macro-F1 {macro:.4f}")

    seed_rows.append({
        "seed": seed,
        "selected_epochs": best_epochs,
        "val_f1_macro": best["val_f1_macro"],
        "val_loss": best["val_loss"],
        "test_accuracy": acc,
        "test_f1_macro": macro,
        "test_f1_weighted": f1_score(test["label_id"], y_pred, average="weighted"),
        "test_errors": int((y_pred != test["label_id"].values).sum()),
    })

    if seed == CANONICAL_SEED:
        stage2.save_model(str(OUTPUT_DIR / "best_model"))
        seed_test.to_csv(PROCESSED_DIR / "test_predictions_biobert.csv", index=False)
        seed_test[seed_test["label"] != seed_test["predicted_label"]].to_csv(
            PROCESSED_DIR / "biobert_mistakes.csv", index=False)
        print("\nCanonical-seed classification report:")
        print(classification_report(test["label_id"], y_pred, target_names=labels))
    del stage2

# ------------------------------------------------------------------
# Seed summary (merge with any earlier seeds so runs can be split up)
# ------------------------------------------------------------------
summary_path = PROCESSED_DIR / "biobert_seed_results.csv"
results = pd.DataFrame(seed_rows)
if summary_path.exists():
    previous = pd.read_csv(summary_path)
    results = pd.concat([previous[~previous["seed"].isin(results["seed"])], results])
results = results.sort_values("seed")
results.to_csv(summary_path, index=False)

print("\nBioBERT results by seed (test set used once per seed):")
print(results.round(4).to_string(index=False))
print(f"\nTest macro-F1 mean {results['test_f1_macro'].mean():.4f} "
      f"± SD {results['test_f1_macro'].std(ddof=1):.4f} "
      f"over {len(results)} seeds")
print("\nSaved:", summary_path)
