
import requests

# ClinicalTrials.gov API endpoint
url = "https://clinicaltrials.gov/api/v2/studies"

# Search for Type 2 diabetes studies
params = {
    "query.cond": "Type 2 Diabetes",
    "filter.advanced": "AREA[ResultsFirstPostDate]RANGE[2025-10-26,2026-10-26]",
    "format": "json",
    "pageSize": 5,
}

# Send the request
response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

# Convert the response to Python data
data = response.json()

# Display the results
studies = data.get("studies", [])

print("Number of studies returned:", len(studies))

for study in studies:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})

    print("NCT ID:", identification.get("nctId"))
    print("Title:", identification.get("briefTitle"))
    print("-" * 40)


print("\n--- CHECKING STUDY DETAILS ---")

for study in studies:
    protocol = study.get("protocolSection", {})

    identification = protocol.get("identificationModule", {})
    conditions = protocol.get("conditionsModule", {})
    status = protocol.get("statusModule", {})

    nct_id = identification.get("nctId")
    condition_list = conditions.get("conditions", [])
    results_date = status.get("resultsFirstPostDateStruct", {}).get("date")

    has_results = "resultsSection" in study

    print("\nNCT ID:", nct_id)
    print("Conditions:", condition_list)
    print("Results first posted:", results_date)
    print("Structured results available:", has_results)
    print("-" * 40)

print("\n--- REPORTED OUTCOME MEASURES ---")

for study in studies:
    protocol = study.get("protocolSection", {})
    nct_id = protocol.get("identificationModule", {}).get("nctId")

    results = study.get("resultsSection", {})
    outcome_module = results.get("outcomeMeasuresModule", {})
    outcomes = outcome_module.get("outcomeMeasures", [])

    print("\nStudy:", nct_id)
    print("Number of reported outcome measures:", len(outcomes))

    for outcome in outcomes[:3]:
        print("Type:", outcome.get("type"))
        print("Title:", outcome.get("title"))
        print("Description:", outcome.get("description"))
        print("-" * 40)

print("\n--- EXAMINING RESULTS SECTIONS ---")

for study in studies:
    protocol = study.get("protocolSection", {})
    nct_id = protocol.get("identificationModule", {}).get("nctId")

    results = study.get("resultsSection", {})

    baseline = results.get("baselineCharacteristicsModule", {})
    outcomes = results.get("outcomeMeasuresModule", {})
    adverse = results.get("adverseEventsModule", {})

    baseline_measures = baseline.get("measures", [])
    outcome_measures = outcomes.get("outcomeMeasures", [])

    print("\nStudy:", nct_id)
    print("Baseline measures:", len(baseline_measures))
    print("Outcome measures:", len(outcome_measures))
    print("Adverse event section available:", bool(adverse))

    for measure in baseline_measures[:2]:
        print("Baseline title:", measure.get("title"))

    print("-" * 40)


import pandas as pd

# Create a table to review our studies
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
        "results_first_posted": status.get("resultsFirstPostDateStruct", {}).get("date")
    })

study_df = pd.DataFrame(study_list)

print(study_df.to_string(index=False))

 


# Add screening columns
study_df["include"] = "pending"
study_df["reason"] = ""

# Save as CSV
study_df.to_csv("data/processed/study_screening_sample.csv", index=False)

print("Screening table saved!")


