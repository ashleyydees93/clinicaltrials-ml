
import pandas as pd

# Load our cleaned measurements
df = pd.read_csv("data/processed/measurements_clean.csv")

# Suggest labels using the source section
label_map = {
    "baseline": "Baseline",
    "outcome": "Review",
    "adverse_event": "Safety"
}

df["suggested_label"] = df["source"].map(label_map)

# Leave final labels empty until reviewed
df["final_label"] = ""

# Save the labeling worksheet
df.to_csv("data/processed/measurements_to_label.csv", index=False)

print("Total measurements:", len(df))
print("\nSuggested labels:")
print(df["suggested_label"].value_counts())
