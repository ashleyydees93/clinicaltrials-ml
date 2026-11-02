
import pandas as pd
import os

# Load our study review table
df = pd.read_csv("screening/study_review.csv")

# Sort studies by NCT ID
df = df.sort_values("nct_id").reset_index(drop=True)

# Split studies between Ashley and Caroline
ashley_df = df.iloc[::2].copy()
caroline_df = df.iloc[1::2].copy()

# Save separate review files
if not os.path.exists("screening/ashley_review.csv"):
    ashley_df.to_csv("screening/ashley_review.csv", index=False)

if not os.path.exists("screening/caroline_review.csv"):
    caroline_df.to_csv("screening/caroline_review.csv", index=False)

print("Total studies:", len(df))
print("Ashley's studies:", len(ashley_df))
print("Caroline's studies:", len(caroline_df))
