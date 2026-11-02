
import requests
import pandas as pd
import json
from datetime import date

# API settings
url = "https://clinicaltrials.gov/api/v2/studies"

start_date = "2025-11-03"
end_date = "2026-11-02"

params = {
    "query.cond": "Type 2 Diabetes",
    "filter.advanced": f"AREA[ResultsFirstPostDate]RANGE[{start_date},{end_date}]",
    "format": "json",
    "pageSize": 100
}

# Collect all pages
studies = []

while True:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    studies.extend(data.get("studies", []))
    print("Studies collected:", len(studies))

    if "nextPageToken" not in data:
        break

    params["pageToken"] = data["nextPageToken"]

# Save original study records
with open("data/raw/studies.json", "w") as file:
    json.dump(studies, file, indent=2)

# Create a screening table
study_list = []

for study in studies:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    conditions = protocol.get("conditionsModule", {})
    status = protocol.get("statusModule", {})

    study_list.append({
        "nct_id": identification.get("nctId"),
        "title": identification.get("briefTitle"),
        "conditions": ", ".join(conditions.get("conditions", [])),
        "results_first_posted": status.get(
            "resultsFirstPostDateStruct", {}
        ).get("date"),
        "has_results": "resultsSection" in study,
        "include": "pending",
        "reason": ""
    })

study_df = pd.DataFrame(study_list)

# Check for duplicate study IDs
print("Duplicate NCT IDs:", study_df["nct_id"].duplicated().sum())

# Check that posting dates match our search window
dates = pd.to_datetime(study_df["results_first_posted"], errors="coerce")
valid_dates = dates.between(start_date, end_date)

print("Studies outside date window or missing dates:", (~valid_dates).sum())

# Stop if the dataset fails these checks
assert study_df["nct_id"].notna().all()
assert not study_df["nct_id"].duplicated().any()
assert valid_dates.all()

# Save the screening table
study_df.to_csv("data/processed/study_screening.csv", index=False)

# Save collection information
metadata = {
    "retrieval_date": date.today().isoformat(),
    "start_date": start_date,
    "end_date": end_date,
    "condition_query": "Type 2 Diabetes",
    "number_of_studies": len(studies),
    "api_url": url
}

with open("data/raw/collection_metadata.json", "w") as file:
    json.dump(metadata, file, indent=2)

print("\nCollection complete!")
print("Total studies:", len(studies))
print("Screening table saved!")
