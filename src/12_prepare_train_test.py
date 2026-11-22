from pathlib import Path
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

SOURCE = Path("../screening/model_ready_267.csv")
OUTPUT = Path("../data/processed")
SEED = 143

# Read only the reviewed, eligible measurement records.
df = pd.read_csv(SOURCE, dtype={"nct_id": str, "record_id": str})
required = {"record_id", "nct_id", "text", "label"}
if not required.issubset(df.columns):
    raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
if df["text"].isna().any() or df["label"].isna().any():
    raise ValueError("Text and label cannot contain missing values.")
if not df["label"].isin(["Baseline", "Efficacy", "Safety"]).all():
    raise ValueError("Unexpected label found. Only Baseline, Efficacy, Safety are allowed.")
if df["record_id"].duplicated().any():
    raise ValueError("Duplicate record_id found.")
if "NCT05923827" in set(df["nct_id"]):
    raise ValueError("Type 1 diabetes RADIANT study was unexpectedly included.")

# Hold out entire studies so the model never sees a test-study during training.
split = GroupShuffleSplit(n_splits=1, test_size=0.70, random_state=SEED)
train_idx, test_idx = next(split.split(df, df["label"], groups=df["nct_id"]))
train = df.iloc[train_idx].copy()
test = df.iloc[test_idx].copy()

assert set(train["nct_id"]).isdisjoint(set(test["nct_id"]))
assert set(train["label"]) == {"Baseline", "Efficacy", "Safety"}
assert set(test["label"]) == {"Baseline", "Efficacy", "Safety"}

OUTPUT.mkdir(parents=True, exist_ok=True)
train.to_csv(OUTPUT / "train.csv", index=False)
test.to_csv(OUTPUT / "test.csv", index=False)

print("All records:", len(df), "from", df["nct_id"].nunique(), "studies")
print("Training:", len(train), "records from", train["nct_id"].nunique(), "studies")
print("Testing:", len(test), "records from", test["nct_id"].nunique(), "studies")
print("\nTraining labels:\n", train["label"].value_counts().to_string())
print("\nTesting labels:\n", test["label"].value_counts().to_string())
print("\nNo studies overlap between training and testing.")
print("Saved ../data/processed/train.csv and ../data/processed/test.csv")
