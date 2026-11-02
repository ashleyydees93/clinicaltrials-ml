# Clinical Trial Study Screening Rules

## Project: Mining Type 2 Diabetes Clinical Trial Results

**Researchers:** Ashley Dees and Caroline Pearson

## 1. Purpose

This document defines the rules for selecting Type 2 diabetes clinical studies from ClinicalTrials.gov.

Both researchers will use these rules to make consistent decisions about which studies should be included in the machine learning dataset.

## 2. Data Collection

- **Source:** ClinicalTrials.gov API v2
- **Condition search:** Type 2 Diabetes
- **Results First Posted:** November 3, 2025 – November 2, 2026
- **Initial dataset:** 121 candidate studies
- **Unique study identifier:** NCT ID

The initial search results are not automatically considered eligible.

## 3. Inclusion Criteria

Include studies that meet the following criteria:

1. Investigate Type 2 diabetes or a relevant Type 2 diabetes complication.
2. Include participants with Type 2 diabetes, or provide separately identifiable results for participants with Type 2 diabetes.
3. Investigate treatment, management, education, monitoring, safety, or relevant physiological outcomes associated with Type 2 diabetes.
4. Have structured results and usable measurement descriptions.
5. Have a Results First Posted date within the approved collection window.

## 4. Exclusion Criteria

Exclude studies when:

1. The population exclusively involves Type 1 diabetes.
2. The study focuses only on prediabetes or preventing diabetes in people without diagnosed Type 2 diabetes.
3. Type 2 diabetes is only an incidental characteristic and not relevant to the research question.
4. Results for Type 2 diabetes cannot be distinguished from an unrelated population when that distinction is necessary.
5. No usable measurements or descriptions are available for classification.

## 5. Studies Requiring Further Review

Mark a study as `review` when:

- It includes both Type 1 and Type 2 diabetes.
- It investigates another disease alongside Type 2 diabetes.
- It includes a mixture of diagnosed Type 2 diabetes and at-risk participants.
- Its outcomes or population are unclear.
- Its relevance cannot be determined from the title, summary, and eligibility criteria.

Both researchers should examine these records before making a final decision.

## 6. Screening Decisions

Record one of the following in the `include` column:

| Decision | Meaning |
|---|---|
| `yes` | Meets the inclusion criteria |
| `no` | Meets an exclusion criterion |
| `review` | Requires additional examination |
| `pending` | Not yet screened |

Record a brief explanation in the `reason` column.

## 7. Outcome Classification

After study screening, prepare a reviewed sample using the three categories in the approved project proposal.

### Baseline Characteristics
Measurements describing participants at the beginning of a study.

Examples:
- Participant age
- Sex
- Baseline BMI
- Baseline HbA1c

### Efficacy
Measurements used to assess an intervention's intended benefits or effectiveness.

Examples:
- Change in HbA1c
- Change in fasting glucose
- Improvement in time in glucose range
- Change in body weight when weight reduction is an intended benefit

### Safety
Measurements evaluating adverse effects, harms, or treatment tolerability.

Examples:
- Hypoglycemic adverse events
- Serious adverse events
- Treatment-related side effects
- Treatment discontinuation due to adverse events

**Important:** A measurement's clinical meaning depends on the study objective. Do not automatically classify cardiovascular events, weight changes, or glucose measurements without reviewing their context.

ClinicalTrials.gov's primary and secondary outcome designations are separate from these project labels.

Measurements that cannot be reliably assigned to one of the three categories will be flagged for review rather than forced into an incorrect category.

## 8. Review Process

1. Divide the candidate studies between Ashley and Caroline.
2. Review the study title, conditions, summary, and eligibility criteria.
3. Record `yes`, `no`, or `review` in the screening table.
4. Provide a reason for every decision.
5. Discuss uncertain cases together.
6. Resolve disagreements and document the final decision.
7. Retain the final eligible study list for outcome extraction.

Screening decisions should be made before training the classifier.

## 9. Documentation

Record the number of studies:

- Initially retrieved
- Included
- Excluded
- Requiring additional review
- Finally retained for analysis

Preserve study identifiers and screening decisions for reproducibility.

## 10. Important Limitations

ClinicalTrials.gov records may contain incomplete or changing information.

Condition searches may return studies that are not directly focused on Type 2 diabetes.

Study eligibility and outcome classification require careful interpretation. Missing information must not be treated as evidence that an outcome or adverse event did not occur.

These rules may be refined before screening is finalized, but any changes must be documented and applied consistently.