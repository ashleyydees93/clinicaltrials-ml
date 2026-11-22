from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SEED_DIR = PROCESSED_DIR / "biobert_seeds"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

N_BOOT = 2000
RNG_SEED = 143

lr = pd.read_csv(PROCESSED_DIR / "test_predictions.csv")
seed_files = sorted(SEED_DIR.glob("test_predictions_seed*.csv"),
                    key=lambda p: int(p.stem.replace("test_predictions_seed", "")))
if not seed_files:
    raise SystemExit("No BioBERT seed predictions found. Run 13.1_train_BioBert.py first.")

bert = {}
for path in seed_files:
    seed = int(path.stem.replace("test_predictions_seed", ""))
    df = pd.read_csv(path)
    assert df["record_id"].tolist() == lr["record_id"].tolist(), "Row order differs"
    bert[seed] = df

y_true = lr["label"].to_numpy()
lr_pred = lr["predicted_label"].to_numpy()
studies = lr["nct_id"].to_numpy()
study_ids = np.unique(studies)
rows_by_study = {s: np.flatnonzero(studies == s) for s in study_ids}


def macro_f1(idx, pred):
    return f1_score(y_true[idx], pred[idx], average="macro", zero_division=0)


# Shared bootstrap resamples (same studies for every seed -> paired comparison)
rng = np.random.default_rng(RNG_SEED)
boot_idx = [np.concatenate([rows_by_study[s] for s in rng.choice(study_ids, len(study_ids))])
            for _ in range(N_BOOT)]
lr_boot = np.array([macro_f1(i, lr_pred) for i in boot_idx])

lr_macro = f1_score(y_true, lr_pred, average="macro")
lr_acc = accuracy_score(y_true, lr_pred)
lr_correct = lr_pred == y_true

rows, diff_boot_by_seed = [], []
for seed, df in bert.items():
    pred = df["predicted_label"].to_numpy()
    correct = pred == y_true
    b = int((correct & ~lr_correct).sum())   # BioBERT right, LR wrong
    c = int((~correct & lr_correct).sum())   # LR right, BioBERT wrong
    p = binomtest(b, b + c).pvalue if b + c else 1.0

    diff_boot = np.array([macro_f1(i, pred) for i in boot_idx]) - lr_boot
    diff_boot_by_seed.append(diff_boot)
    lo, hi = np.percentile(diff_boot, [2.5, 97.5])
    macro = f1_score(y_true, pred, average="macro")
    rows.append({
        "seed": seed,
        "biobert_accuracy": accuracy_score(y_true, pred),
        "biobert_f1_macro": macro,
        "lr_f1_macro": lr_macro,
        "diff_f1_macro": macro - lr_macro,
        "diff_ci_low": lo,
        "diff_ci_high": hi,
        "biobert_only_correct": b,
        "lr_only_correct": c,
        "mcnemar_p": p,
    })

res = pd.DataFrame(rows)
mean_diff_boot = np.mean(diff_boot_by_seed, axis=0)
pooled_lo, pooled_hi = np.percentile(mean_diff_boot, [2.5, 97.5])
res.to_csv(RESULTS_DIR / "biobert_vs_lr.csv", index=False)

print(f"Logistic Regression: accuracy {lr_acc:.4f}, macro-F1 {lr_macro:.4f}\n")
print(res.round(4).to_string(index=False))
n = len(res)
print(f"\nBioBERT macro-F1 over {n} seeds: mean {res.biobert_f1_macro.mean():.4f}, "
      f"SD {res.biobert_f1_macro.std(ddof=1):.4f}, "
      f"range {res.biobert_f1_macro.min():.4f}–{res.biobert_f1_macro.max():.4f}")
print(f"Mean difference vs LR: {res.diff_f1_macro.mean():+.4f} "
      f"(seed-averaged 95% study-bootstrap CI {pooled_lo:+.4f} to {pooled_hi:+.4f})")
print(f"Seeds where BioBERT > LR: {(res.diff_f1_macro > 0).sum()}/{n}")
print(f"Seeds with McNemar p < 0.05: {(res.mcnemar_p < 0.05).sum()}/{n}")
print(f"Seeds whose difference CI excludes 0: {(res.diff_ci_low > 0).sum()}/{n}")

if pooled_lo > 0 and (res.diff_f1_macro > 0).all():
    verdict = "BioBERT is reliably better than Logistic Regression on held-out studies."
elif pooled_hi < 0:
    verdict = "Logistic Regression is reliably better than BioBERT."
else:
    verdict = ("No reliable difference: the seed-averaged CI includes 0 "
               "or BioBERT does not beat LR on every seed.")
print("\nVerdict:", verdict)

# ------------------------------------------------------------------
# Figure: per-seed macro-F1 vs. the Logistic Regression reference
# ------------------------------------------------------------------
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, YELLOW = "#2a78d6", "#eda100"

fig, ax = plt.subplots(figsize=(8, 4.2))
x = np.arange(n)
ax.axhline(lr_macro, color=BLUE, linewidth=2, label=f"Logistic Regression ({lr_macro:.3f})")
ax.errorbar(x, res.biobert_f1_macro,
            yerr=[res.diff_f1_macro - res.diff_ci_low, res.diff_ci_high - res.diff_f1_macro],
            fmt="o", color=YELLOW, ecolor=INK_2, capsize=3, markersize=8,
            label="BioBERT by seed (bars: 95% CI of difference vs. LR)")
ax.axhline(res.biobert_f1_macro.mean(), color=YELLOW, linestyle="--", linewidth=1.5,
           label=f"BioBERT mean ({res.biobert_f1_macro.mean():.3f})")
ax.set_xticks(x, [f"seed {s}" for s in res.seed])
ax.set_ylabel("Macro-F1 (held-out test set)")
ax.set_title("BioBERT across seeds vs. Logistic Regression", loc="left", color=INK)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.grid(axis="y", color=GRID)
ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, loc="upper right",bbox_to_anchor=(0.95, 1.0))
fig.tight_layout()
fig.savefig(RESULTS_DIR / "biobert_vs_lr_seeds.png", dpi=200)
print("\nSaved results/biobert_vs_lr.csv and results/biobert_vs_lr_seeds.png")
