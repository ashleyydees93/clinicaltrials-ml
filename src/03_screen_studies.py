
import pandas as pd

# Load our screening table
df = pd.read_csv("data/processed/study_screening.csv")

# Check the dataset
print("Total studies:", len(df))
print("\nStructured results available:")
print(df["has_results"].value_counts())

# Check missing information
print("\nMissing values:")
print(df.isnull().sum())

# Display study titles
print("\nStudies to review:")
print(df[["nct_id", "title", "conditions"]].to_string(index=False))
