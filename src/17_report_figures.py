from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

LABELS = ["Baseline", "Efficacy", "Safety"]
SEED = 143

# Fixed categorical order (validated palette, light mode)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "legend.frameon": False,
})

MODELS = {
    "Logistic Regression": "test_predictions.csv",
    "Naive Bayes": "test_predictions_naive_bayes.csv",
    "Linear SVM": "test_predictions_svm.csv",
    "BioBERT": "test_predictions_biobert.csv",
}

train = pd.read_csv(PROCESSED_DIR / "train.csv")
test = pd.read_csv(PROCESSED_DIR / "test.csv")
preds = {name: pd.read_csv(PROCESSED_DIR / f) for name, f in MODELS.items()}

# Most-frequent-class baseline (the comparison named in the proposal)
majority = train["label"].value_counts().idxmax()
preds["Majority class"] = test.assign(predicted_label=majority)


def study_bootstrap(df, n=2000):
    """95% CI for macro F1, resampling whole studies (matches the grouped split)."""
    rng = np.random.default_rng(SEED)
    by_study = df.set_index("nct_id")
    ids = df["nct_id"].unique()
    scores = []
    for _ in range(n):
        sample = by_study.loc[rng.choice(ids, len(ids))]
        scores.append(f1_score(sample["label"], sample["predicted_label"],
                               average="macro", zero_division=0))
    return np.percentile(scores, [2.5, 97.5])


rows = []
for name, df in preds.items():
    lo, hi = study_bootstrap(df)
    per_class = f1_score(df["label"], df["predicted_label"], labels=LABELS,
                         average=None, zero_division=0)
    rows.append({
        "Model": name,
        "Accuracy": accuracy_score(df["label"], df["predicted_label"]),
        "Macro F1": f1_score(df["label"], df["predicted_label"],
                             average="macro", zero_division=0),
        "Macro F1 CI low": lo,
        "Macro F1 CI high": hi,
        **{f"F1 {lab}": v for lab, v in zip(LABELS, per_class)},
        "Errors": int((df["label"] != df["predicted_label"]).sum()),
    })
summary = pd.DataFrame(rows)
summary.to_csv(RESULTS_DIR / "report_summary_metrics.csv", index=False)
print(summary.round(3).to_string(index=False))

# ------------------------------------------------------------------
# Figure A: per-class F1 by model
# ------------------------------------------------------------------
model_names = list(MODELS)
fig, ax = plt.subplots(figsize=(9, 4.8))
width = 0.19
x = np.arange(len(LABELS))
for i, name in enumerate(model_names):
    vals = summary.set_index("Model").loc[name, [f"F1 {l}" for l in LABELS]].values
    bars = ax.bar(x + (i - 1.5) * (width + 0.01), vals, width,
                  color=SERIES[i], label=name, edgecolor="white", linewidth=1)
    if name == "BioBERT":
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=8, color=INK)
ax.set_xticks(x, LABELS)
ax.set_ylim(0.6, 1.0)
ax.set_ylabel("F1 score (held-out test set)")
ax.set_title("Per-class F1 by model", loc="left", color=INK, fontsize=12)
ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.08))
fig.tight_layout()
fig.savefig(RESULTS_DIR / "per_class_f1_by_model.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------------
# Figure B: macro F1 with study-level 95% CI, vs. majority baseline
# ------------------------------------------------------------------
order = ["Majority class"] + model_names
s = summary.set_index("Model").loc[order]
fig, ax = plt.subplots(figsize=(9, 4.4))
colors = ["#b5b3ad"] + SERIES
y = np.arange(len(order))
ax.barh(y, s["Macro F1"], color=colors, height=0.55)
ax.errorbar(s["Macro F1"], y,
            xerr=[s["Macro F1"] - s["Macro F1 CI low"],
                  s["Macro F1 CI high"] - s["Macro F1"]],
            fmt="none", ecolor=INK_2, capsize=3, linewidth=1)
for yi, (v, hi) in enumerate(zip(s["Macro F1"], s["Macro F1 CI high"])):
    ax.text(max(v, hi) + 0.015, yi, f"{v:.3f}", va="center", fontsize=9, color=INK)
ax.set_yticks(y, order)
ax.invert_yaxis()
ax.set_xlim(0, 1.08)
ax.grid(axis="x", color=GRID)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Macro F1 (error bars: 95% study-level bootstrap CI)")
ax.set_title("Macro F1 vs. most-frequent-class baseline", loc="left",
             color=INK, fontsize=12)
fig.tight_layout()
fig.savefig(RESULTS_DIR / "macro_f1_vs_baseline.png", dpi=200)
plt.close(fig)

# ------------------------------------------------------------------
# Figure C: labeled outcome categories by Results First Posted year
# ------------------------------------------------------------------
screen = pd.read_csv(PROCESSED_DIR / "study_screening.csv")
screen["month"] = pd.to_datetime(screen["results_first_posted"]).dt.to_period("M")
labeled = pd.read_csv(PROJECT_ROOT / "screening" / "model_ready_267.csv")
labeled = labeled.merge(screen[["nct_id", "month"]], on="nct_id", how="left")

# Every month in the collection window, including months with no labeled records
all_months = pd.period_range(screen["month"].min(), screen["month"].max(), freq="M")
counts = (pd.crosstab(labeled["month"], labeled["label"])
          .reindex(index=all_months, columns=LABELS, fill_value=0))
studies = labeled.groupby("month")["nct_id"].nunique().reindex(all_months, fill_value=0)
counts.assign(Studies=studies).to_csv(RESULTS_DIR / "categories_by_results_month.csv")

fig, ax = plt.subplots(figsize=(10, 4.8))
x = np.arange(len(counts))
bottom = np.zeros(len(counts))
for i, lab in enumerate(LABELS):
    ax.bar(x, counts[lab], bottom=bottom, color=SERIES[i], label=lab,
           width=0.7, edgecolor="white", linewidth=1.5)
    bottom += counts[lab].values
for xi, total in enumerate(bottom):
    ax.text(xi, total + 0.6, f"{int(total)}", ha="center", va="bottom",
            fontsize=8, color=INK)
ax.set_xticks(x, [f"{m.strftime('%b')}\n{m.year}\n{s} stud." for m, s in
                  zip(counts.index, studies)], fontsize=8)
ax.set_ylim(0, bottom.max() * 1.12)
ax.set_ylabel("Labeled measurements (count)")
ax.set_title("Labeled outcome categories by Results First Posted month",
             loc="left", color=INK, fontsize=12)
ax.legend(ncol=3, loc="upper left")
fig.tight_layout()
fig.savefig(RESULTS_DIR / "categories_by_results_month.png", dpi=200)
plt.close(fig)

print("\nReport figures saved to", RESULTS_DIR)
