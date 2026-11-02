
import json
import pandas as pd
import os

# Load collected studies
with open("data/raw/studies.json") as file:
    studies = json.load(file)

# Load screening table
df = pd.read_csv("data/processed/study_screening.csv")

# Collect study summaries and eligibility criteria
details = []

for study in studies:
    protocol = study.get("protocolSection", {})

    details.append({
        "nct_id": protocol.get("identificationModule", {}).get("nctId"),
        "summary": protocol.get("descriptionModule", {}).get("briefSummary"),
        "eligibility": protocol.get("eligibilityModule", {}).get("eligibilityCriteria")
    })

details_df = pd.DataFrame(details)

# Add study details to screening table
review_df = df.merge(details_df, on="nct_id", how="left")

# Save without overwriting previous review decisions
filename = "data/processed/study_review.csv"

if not os.path.exists(filename):
    review_df.to_csv(filename, index=False)
    print("Study review table saved!")
else:
    print("Review file already exists. No changes made.")

print("Total studies:", len(review_df))
print("Studies missing summaries:", review_df["summary"].isna().sum())
