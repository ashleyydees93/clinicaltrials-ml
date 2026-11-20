
import requests
import pandas as pd
import json
import time

# Load our 89 approved studies
df = pd.read_csv("screening/eligible_studies_89.csv")
nct_ids = df["nct_id"].tolist()

url = "https://clinicaltrials.gov/api/v2/studies"

studies = []

# Download each approved study
for nct_id in nct_ids:
    response = requests.get(f"{url}/{nct_id}", timeout=30)
    response.raise_for_status()

    study = response.json()
    studies.append(study)

    print("Downloaded:", nct_id)
    time.sleep(0.2)

# Save the full records
with open("data/raw/eligible_studies.json", "w", encoding="utf-8") as file:
    json.dump(studies, file, indent=2)

print("Total studies downloaded:", len(studies))
