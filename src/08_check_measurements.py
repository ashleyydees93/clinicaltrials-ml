
import pandas as pd

# Load extracted measurements
df = pd.read_csv("data/processed/measurements.csv")

# Check dataset size
print("Dataset shape:", df.shape)

# Check number of studies
print("Unique studies:", df["nct_id"].nunique())

# Check missing values
print("\nMissing values:")
print(df.isnull().sum())

# Check source counts
print("\nMeasurement sources:")
print(df["source"].value_counts())

# Preview the measurements
print("\nFirst 10 measurements:")
print(df[["source", "title", "description"]].head(10))
