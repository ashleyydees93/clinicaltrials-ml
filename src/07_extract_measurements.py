
import json
import pandas as pd

# Load our approved clinical trials
with open("data/raw/eligible_studies.json", encoding="utf-8") as file:
    studies = json.load(file)

measurements = []

for study in studies:
    protocol = study.get("protocolSection", {})
    results = study.get("resultsSection", {})

    nct_id = protocol.get("identificationModule", {}).get("nctId")

    # Baseline measurements
    baseline = results.get("baselineCharacteristicsModule", {})
    for measure in baseline.get("measures", []):
        measurements.append({
            "nct_id": nct_id,
            "source": "baseline",
            "title": measure.get("title", ""),
            "description": measure.get("description", "")
        })

    # Outcome measurements
    outcomes = results.get("outcomeMeasuresModule", {})
    for measure in outcomes.get("outcomeMeasures", []):
        measurements.append({
            "nct_id": nct_id,
            "source": "outcome",
            "title": measure.get("title", ""),
            "description": measure.get("description", "")
        })

    # Adverse event measurements
    adverse = results.get("adverseEventsModule", {})
    for group in ["seriousEvents", "otherEvents"]:
        for event in adverse.get(group, []):
            measurements.append({
                "nct_id": nct_id,
                "source": "adverse_event",
                "title": event.get("term", ""),
                "description": event.get("organSystem", "")
            })

# Create our dataset
df = pd.DataFrame(measurements)

# Save measurements
df.to_csv("data/processed/measurements.csv", index=False)

print("Total measurements:", len(df))
print(df["source"].value_counts())
