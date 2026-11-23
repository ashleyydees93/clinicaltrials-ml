
import pandas as pd

# Load measurements
df = pd.read_csv("data/processed/measurements_to_label.csv")

# Select 100 records from each source
baseline = df[df["source"] == "baseline"].sample(100, random_state=143)
outcome = df[df["source"] == "outcome"].sample(100, random_state=143)
safety = df[df["source"] == "adverse_event"].sample(100, random_state=143)

# Combine the samples
sample = pd.concat([baseline, outcome, safety])

# Shuffle the rows
sample = sample.sample(frac=1, random_state=143).reset_index(drop=True)

# Assign a unique row ID for tracking decisions
sample.insert(0, "record_id", range(1, len(sample) + 1))

# Divide the work between Ashley and Caroline
sample["reviewer"] = ["Ashley" if i % 2 == 0 else "Caroline" for i in range(len(sample))]

# Save labeling sample
sample.to_csv("screening/measurement_label_sample.csv", index=False)

print("Total sample:", len(sample))
print(sample["source"].value_counts())
print("\nAssignments:")
print(sample["reviewer"].value_counts())
