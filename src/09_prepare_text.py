
import pandas as pd

# Load extracted measurements
df = pd.read_csv("data/processed/measurements.csv")

# Replace missing descriptions with empty text
df["description"] = df["description"].fillna("")

# Combine title and description
df["text"] = df["title"] + " " + df["description"]

# Remove extra spaces
df["text"] = df["text"].str.strip()

# Check for empty text
print("Empty text records:", (df["text"] == "").sum())

# Save cleaned dataset
df.to_csv("data/processed/measurements_clean.csv", index=False)

print("Cleaned measurements:", len(df))
print(df[["source", "text"]].head(10))
