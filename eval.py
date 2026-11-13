"""
Survey analysis
---------------
Main analysis: Finished == Yes
Conditional questions:
    Q9-Q11: Q8 contains "Anonymization techniques"
    Q29:    Q28 contains "fully a spectrum"

Outputs:
    - survey_with_last_answered_question.csv
    - other_responses_for_manual_coding.csv
    - paper figures (PDF + pgf)
    - CSV data underlying the paper figures

All other descriptive results are printed to the console.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
from itertools import combinations
from scipy.stats import permutation_test

mpl.use('pgf')
plt.rcParams["pgf.texsystem"] = ("pdflatex")
tex_fonts = {
    # Use LaTeX to write all text
    #"text.usetex": True,
    #"font.family": "serif",
    # Use 10pt font in plots, to match 10pt font in document
    "axes.labelsize": 10,
    "font.size": 10,
    # Make the legend/label fonts a little smaller
    "legend.fontsize": 8,
    "xtick.labelsize": 10,
    "ytick.labelsize": 8
}

plt.rcParams.update(tex_fonts)


# ============================================================
# Configuration
# ============================================================

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

# None -> newest export according to timestamp in filename
# Alternatively:
# INPUT_FILE = Path("export-ganges_2-second-iteration-2026-09-28-08-47-24.csv")
INPUT_FILE = None
EXPORT_PATTERN = "exportSurvey.csv"

SAVE_PNG = False
sns.set_theme(style="whitegrid", context="paper")


# Questions that may legitimately be empty
OPTIONAL = {14, 23, 24, 25, 26, 27, 29}

# Questions with multi-select answers
MULTI = {3, 6, 7, 8, 9, 10, 11, 13, 15, 16, 22, 26, 29}

DESCRIPTIVE_QUESTIONS = [
    1, 2, 3,          # sample
    4, 5,             # pipeline context
    8, 9, 10, 11,    # RQ1
    12, 13, 15, 16,  # RQ3
    17, 18, 19, 20,  # adoption/compliance
    21, 22,           # difficulties
    28, 29            # compliance concept
]

# ============================================================
# Load newest survey export
# ============================================================

def latest_export():
    files = list(Path(".").glob(EXPORT_PATTERN))
    if not files:
        raise FileNotFoundError(f"No file matching {EXPORT_PATTERN}")

    def timestamp(f):
        m = re.search(r"(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.csv$", f.name)
        return pd.to_datetime(m.group(1), format="%Y-%m-%d-%H-%M-%S") if m else pd.Timestamp.min

    return max(files, key=timestamp)


INPUT_FILE = INPUT_FILE or latest_export()
dataAll = pd.read_csv(INPUT_FILE)

print("Input:", INPUT_FILE)
print("All responses:", len(dataAll))
print(dataAll["Finished"].value_counts(dropna=False))


# ============================================================
# Detect survey columns
# ============================================================

def qnumber(col):
    m = re.match(r"^\s*(\d+)\.", str(col))
    return int(m.group(1)) if m else None


question = {}
option = {}

for col in dataAll.columns:
    q = qnumber(col)
    if q is None:
        continue

    if str(col).strip().endswith("- Option ID"):
        option[q] = col
    else:
        question[q] = col

print("\nQuestions detected:", sorted(question))

# ============================================================
# Basic helper functions
# ============================================================

def answered(x):
    return pd.notna(x) and str(x).strip() != ""


def split_ids(x):
    if not answered(x):
        return []
    return [v.strip() for v in str(x).split(",") if v.strip()]


def split_text(x):
    if not answered(x):
        return []
    return [v.strip() for v in str(x).split(";") if v.strip()]


# ============================================================
# Last answered question
# ============================================================

def last_answered(row):
    a = [q for q, col in question.items() if answered(row[col])]
    return max(a) if a else np.nan


dataAll["last_answered_question"] = dataAll.apply(last_answered, axis=1)

# Audit file including unfinished responses
dataAll.to_csv(
    RESULTS / "survey_with_last_answered_question.csv",
    index=False
)


# ============================================================
# Main sample
# ============================================================

data = dataAll[
    dataAll["Finished"].astype(str).str.strip().str.lower() == "yes"
].dropna(subset=["last_answered_question"])

anon = data[question[8]].str.contains("Anonymization techniques", case=False, na=False)
complete = data[[question[q] for q in (9, 10, 11)]].apply(lambda col: col.map(answered)).all(axis=1)
data = data.loc[~anon | complete].copy()

print("\nCompleted responses:", len(data))
data.to_csv(
    RESULTS / "survey_completed29.csv",
    index=False
)


# ============================================================
# Branching
# ============================================================

def eligible(df, q):

    if q in {9, 10, 11}:
        return df[
            df[question[8]]
            .fillna("")
            .str.contains("Anonymization techniques", case=False)
        ]

    if q == 29:
        return df[
            df[question[28]]
            .fillna("")
            .str.contains("fully a spectrum", case=False)
        ]

    return df

# ============================================================
# Option ID -> text mapping
# ============================================================

def build_mapping(q):
    """Build option-ID -> human-readable label from the full export."""

    if q not in option:
        return {}

    mapping = {}

    for _, row in dataAll[[question[q], option[q]]].dropna().iterrows():
        ids = split_ids(row[option[q]])
        texts = split_text(row[question[q]])

        if len(ids) != len(texts):
            continue

        for i, text in zip(ids, texts):
            if i.lower() != "other":
                mapping.setdefault(i, text)

    return mapping


mappings = {q: build_mapping(q) for q in option}


# ============================================================
# Other responses
# ============================================================

others = []

for q in option:
    for _, row in data.iterrows():

        ids = split_ids(row[option[q]])
        texts = split_text(row[question[q]])

        if "other" not in [x.lower() for x in ids]:
            continue

        if len(ids) == len(texts):
            for i, text in zip(ids, texts):
                if i.lower() == "other":
                    others.append([q, row["Response ID"], text, "", ""])
        else:
            others.append([
                q,
                row["Response ID"],
                row[question[q]],
                "",
                "check ID/text alignment"
            ])

others = pd.DataFrame(
    others,
    columns=[
        "question",
        "response_id",
        "other_text",
        "suggested_group",
        "coding_comment"
    ]
)

others.to_csv(
    RESULTS / "other_responses_for_manual_coding.csv",
    index=False
)

print("\nOTHER RESPONSES")
if len(others):
    for q, group in others.groupby("question"):
        print(f"\nQ{q}")
        for x in group["other_text"]:
            print(" -", x)
else:
    print("None")


# ============================================================
# Frequency functions
# ============================================================

def freq(q):
    """Single-choice frequencies."""

    d = eligible(data, q)
    d = d[d[question[q]].apply(answered)]

    out = d[question[q]].value_counts().rename_axis("response").reset_index(name="n")
    out["percent"] = 100 * out["n"] / len(d) if len(d) else np.nan
    return out, len(d)


def freq_multi(q):
    """Multi-select frequencies using option IDs."""

    d = eligible(data, q)
    d = d[d[option[q]].apply(answered)]

    values = [
        i
        for x in d[option[q]]
        for i in set(split_ids(x))
    ]

    out = pd.Series(values).value_counts().rename_axis("option_id").reset_index(name="n")

    if out.empty:
        return out, len(d)

    out["label"] = out["option_id"].map(mappings[q])
    out.loc[out["option_id"].str.lower() == "other", "label"] = "Other"
    out["label"] = out["label"].fillna(out["option_id"])
    out["percent"] = 100 * out["n"] / len(d)

    return out, len(d)


# ============================================================
# Response overview / missing conditional answers
# ============================================================

print("\n" + "=" * 70)
print("RESPONSE OVERVIEW")
print("=" * 70)

for q in sorted(question):

    d = eligible(data, q)
    n = d[question[q]].apply(answered).sum()

    marker = ""
    if q in OPTIONAL:
        marker += " optional"
    if q in {9, 10, 11, 29}:
        marker += " conditional"

    print(f"Q{q:02}: {n:2}/{len(d):2} answered{marker}")


# ============================================================
# Descriptive results
# ============================================================

def print_question(q):

    if q in MULTI and q in option:
        table, n = freq_multi(q)
        cols = ["label", "n", "percent"]
    else:
        table, n = freq(q)
        cols = ["response", "n", "percent"]

    print("\n" + "-" * 70)
    print(f"Q{q} (n={n})")
    print(question[q])
    print(table[cols].round({"percent": 1}).to_string(index=False))


# Print descriptive numbers for all questions.
# Paper figures for Q11/Q12/Q15/Q16/Q28 are created below.
#for q in sorted(question):
#    print_question(q)

for q in DESCRIPTIVE_QUESTIONS:
    print_question(q)

# ============================================================
# Ordinal Q17-Q20
# ============================================================
#
# Only endpoints were labelled in the questionnaire:
#
# Q17, Q19, Q20:
#   1 = Very unlikely
#   5 = Very likely
#
# Q18:
#   1 = Not important
#   5 = Very important
#
# Treat as ordinal -> median/IQR rather than mean/SD.
# ============================================================

print("\n" + "=" * 70)
print("ORDINAL RESPONSES")
print("=" * 70)

for q in [17, 18, 19, 20]:

    d = data[question[q]].dropna()

    # Extract star/number from answer
    values = pd.to_numeric(
        d.astype(str).str.extract(r"([1-5])", expand=False),
        errors="coerce"
    ).dropna()

    if len(values) == 0:
        continue

    print(
        f"Q{q}: n={len(values)}, "
        f"median={values.median():.1f}, "
        f"IQR={values.quantile(.25):.1f}-{values.quantile(.75):.1f}"
    )

    print(values.value_counts().sort_index().to_string())

# 
def choice_by(q, prefix, by, by_prefix=None):
    d = eligible(eligible(data, q), by)
    d = d[d[question[q]].map(answered) & d[question[by]].map(answered)]
    group = d[question[by]].str.strip()
    if by_prefix is not None:
        group = group.map(lambda x: any(v.startswith(by_prefix) for v in split_text(x)))

    out = d[question[q]].map(
        lambda x: any(v.startswith(prefix) for v in split_text(x))
    ).groupby(group).agg(selected="sum", n="size")
    if by == 12:
        out = out.reindex(["Never", "Rarely", "Sometimes", "Often", "Always"])
    out["percent"] = (100 * out["selected"] / out["n"]).round(1)
    print(f"\nQ{q} {prefix} / Q{by} {by_prefix or ''}")
    print(out.rename_axis("group").to_string())


# Modulare Pipeline und Barrieren für Wiederverwendung
for prefix in ("Consumer-specific requirements", "Tight coupling"):
    choice_by(15, prefix, 4)

# Duplikationshäufigkeit und Verständnis von Wiederverwendung
for prefix in ("Copying and modifying code", "Deploying a transformation stage once"):
    choice_by(13, prefix, 12)

# Anonymisierung bei Anfrage und Platzierung am Auslieferungspunkt
choice_by(11, "At the point of data delivery", 10, "Anonymization applied dynamically")


# Correlation mit spearman
def spearman_pairs():
    order = {
        2: ["Less that 2 years", "2-5 years", "5-10 years", "More that 10 years"],
        4: ["No", "Yes"],
        5: ["1-3 stages", "4-10 stages", "More that 10 stages"],
        12: ["Never", "Rarely", "Sometimes", "Often", "Always"],
        23: ["Less than 1 GB (per day)", "1 GB - 10 GB (per day)",
             "10 GB – 100 GB (per day)", "100 GB – 1 TB (per day)",
             "1 TB – 10 TB (per day)", "10 TB – 100 TB (per day)",
             "More than 100 TB (per day)"],
        24: ["Daily or less frequent", "Hourly", "Every few minutes",
             "Real-time (seconds or milliseconds)"],
        28: ["Completely binary – either present or absent",
             "Fully a spectrum – can be measured at varying levels"],
    }
    order[25] = order[24]

    values = pd.DataFrame({
        q: data[question[q]].str.strip().map({v: i for i, v in enumerate(order[q])})
        if q in order else pd.to_numeric(data[question[q]], errors="coerce")
        for q in sorted(set(order) | {17, 18, 19, 20})
    })
    pair = values[[12, 23]].dropna().reset_index(drop=True)
    print(pd.crosstab(pair[23], pair[12]).rename(
        index=dict(enumerate(order[23])), columns=dict(enumerate(order[12]))
    ))
    loo = [pair.drop(i).corr(method="spearman").iloc[0, 1] for i in pair.index]
    print(f"Q12/Q23 leave-one-out rho: {min(loo):.3f} to {max(loo):.3f}")
    pairs = list(combinations(values.columns, 2))
    print(f"\nSpearman: {len(pairs)} Paare, Bonferroni-Schwelle = {0.05 / len(pairs):.6g}")

    for a, b in pairs:
        ranks = values[[a, b]].dropna().rank()
        if len(ranks) < 3 or ranks.nunique().min() < 2:
            print(f"Q{a}/Q{b}: n={len(ranks)}, rho=NA, p_roh=NA, p_bonf=NA")
            continue

        rho = ranks.corr().iloc[0, 1]
        x, y = (ranks - ranks.mean()).to_numpy().T
        # Der Betrag macht den Permutationstest zweiseitig.
        p = permutation_test(
            (y,), lambda y, axis: np.abs(np.sum(x * y, axis=axis)),
            permutation_type="pairings", alternative="greater",
            n_resamples=99_999, batch=5_000, random_state=42
        ).pvalue
        
        if p<(0.05 / len(pairs)): # smaller than bonferroni schwelle
            print(f"Q{a}/Q{b}: n={len(ranks)}, rho={rho:+.3f}, "
              f"p_roh={p:.6g}, p_bonf={min(p * len(pairs), 1):.6g}")


spearman_pairs()

# ============================================================
# Figure helper
# ============================================================

def savefig(name):
    plt.tight_layout()
    plt.savefig(RESULTS / f"{name}.pdf", bbox_inches="tight")

    if SAVE_PNG:
        plt.savefig(
            RESULTS / f"{name}.png",
            dpi=300,
            bbox_inches="tight"
        )
        
    else:
        plt.savefig(
            RESULTS / f"{name}.pgf",
            format="pgf",
            bbox_inches="tight"
        )

    plt.close()


def bar(ax, table, label, title, xlabel="Respondents (%)"):

    p = table.sort_values("percent")

    sns.barplot(
        data=p,
        x="percent",
        y=label,
        ax=ax
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")

    for patch, n in zip(ax.patches, p["n"]):
        ax.text(
            patch.get_width() + 1,
            patch.get_y() + patch.get_height() / 2,
            f"n={n}",
            va="center",
            fontsize=8
        )


# ============================================================
# PAPER FIGURE 1
# RQ1/RQ2: anonymization placement
# ============================================================

q11, n11 = freq_multi(11)

d11 = eligible(data, 11)
d11 = d11[d11[option[11]].apply(answered)].copy()

d11["n_placements"] = d11[option[11]].apply(
    lambda x: len(set(split_ids(x)))
)

multiplicity = pd.DataFrame({
    "type": ["Single placement", "Multiple placements"],
    "n": [
        (d11["n_placements"] == 1).sum(),
        (d11["n_placements"] > 1).sum()
    ]
})
multiplicity["percent"] = 100 * multiplicity["n"] / len(d11)

# Placement combinations
d11["combination"] = d11[option[11]].apply(
    lambda x: " + ".join(mappings[11].get(i, i) for i in sorted(set(split_ids(x))))
)

# reported anonymization placement combinations among respondents
print(
    d11.groupby(d11["n_placements"].eq(1).map({True: "Single", False: "Multiple"}))["combination"]
    .value_counts()
)

fig, ax = plt.subplots(figsize=(3.8, 2.4))
bar(ax, q11, "label", None)
savefig("paper_fig1_placement")

fig, ax = plt.subplots(figsize=(3.8, 2.0))
bar(ax, multiplicity, "type", None)
savefig("paper_fig1_multiplicity")

q9, n9 = freq_multi(9)
q10, n10 = freq_multi(10)

for table, n, title, filename in [
    (q9, n9, "Reported techniques", "paper_fig1_anonymization_techniques"),
    (q10, n10, "Implementation of anonymization", "paper_fig1_anonymization_implementation"),
    (q11, n11, "Reported anonymization placement", "paper_fig1_placement"),
]:
    if table.empty:
        continue

    fig, ax = plt.subplots(figsize=(1.8, 2.0))
    bar(ax, table, "label", None)
    savefig(filename)

# Useful later for PGFPlots
q11.to_csv(RESULTS / "paper_fig1_placement.csv", index=False)
multiplicity.to_csv(RESULTS / "paper_fig1_multiplicity.csv", index=False)


# Also print which placement was selected if exactly one was selected
single = d11[d11["n_placements"] == 1]

single_ids = single[option[11]].apply(
    lambda x: split_ids(x)[0]
)

single_labels = single_ids.map(mappings[11]).fillna(single_ids)

print("\nSINGLE-PLACEMENT RESPONSES")
print(single_labels.value_counts().to_string())


# ============================================================
# PAPER FIGURE 2
# RQ3: duplication and barriers to reuse
# ============================================================

q12, n12 = freq(12)
q15, n15 = freq_multi(15)

# Preserve the ordinal order of Q12 where possible
duplication_order = ["Never", "Rarely", "Sometimes", "Often", "Always"]

q12["order"] = q12["response"].apply(
    lambda x: next(
        (i for i, v in enumerate(duplication_order)
         if v.lower() in str(x).lower()),
        99
    )
)

q12 = q12.sort_values("order")

fig, ax = plt.subplots(figsize=(2, 2.0))
sns.barplot(data=q12, x="response", y="percent", order=q12["response"], ax=ax)
ax.set(
    xlabel="",
    ylabel=r"Respondents ($\%$)",
    ylim=(0, q12["percent"].max() + 8),
)
ax.tick_params(axis="x", labelrotation=35)
savefig("paper_fig2_duplication")

fig, ax = plt.subplots(figsize=(3.06, 2))
bar(ax, q15, "label", None)
savefig("paper_fig1_reuse-challenges")

q12.to_csv(RESULTS / "paper_fig2_duplication.csv", index=False)
q15.to_csv(RESULTS / "paper_fig2_reuse_barriers.csv", index=False)


# ============================================================
# PAPER FIGURE 3
# RQ4: operational requirements + compliance concept
# ============================================================

q16, n16 = freq_multi(16)
q28, n28 = freq(28)

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))

bar(
    ax[0],
    q16,
    "label",
    f"Important non-functional requirements (n={n16})"
)

bar(
    ax[1],
    q28,
    "response",
    f"Understanding of compliance (n={n28})"
)

savefig("paper_fig3_requirements")

q16.to_csv(RESULTS / "paper_fig3_nfr.csv", index=False)
q28.to_csv(RESULTS / "paper_fig3_compliance.csv", index=False)


# ============================================================
# Main findings for quick inspection
# ============================================================

print("\n" + "=" * 70)
print("KEY RESULTS")
print("=" * 70)

print(f"Completed respondents: n={len(data)}")

print(
    f"Q11: {len(d11)} answered; "
    f"{(d11['n_placements'] == 1).sum()} single placement, "
    f"{(d11['n_placements'] > 1).sum()} multiple placements."
)

print("\nQ15 - reuse barriers:")
print(
    q15[["label", "n", "percent"]]
    .round({"percent": 1})
    .to_string(index=False)
)

print("\nQ16 - non-functional requirements:")
print(
    q16[["label", "n", "percent"]]
    .round({"percent": 1})
    .to_string(index=False)
)

print("\nQ28 - compliance:")
print(
    q28[["response", "n", "percent"]]
    .round({"percent": 1})
    .to_string(index=False)
)

print("\nFigures and audit files written to:", RESULTS.resolve())
