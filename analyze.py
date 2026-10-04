"""Summarise results.csv -> results_summary.md and print it."""
import csv
import os
import statistics as st
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(BASE_DIR, "results.csv"))))

vals = defaultdict(list)                  # (scenario, metric, mode) -> values
per_client = defaultdict(list)            # (scenario, mode, client) -> mbps
for r in rows:
    v = float(r["value"])
    vals[(r["scenario"], r["metric"], r["mode"])].append(v)
    if r["metric"] == "mbps":
        per_client[(r["scenario"], r["mode"], r["client"])].append(v)

ORDER = ["baseline", "sdn", "sdn_nolimit", "sdn_limit"]
seen = {k[2] for k in vals}
modes = [m for m in ORDER if m in seen] + sorted(seen - set(ORDER))


def fmt(xs):
    if not xs:
        return "-"
    sd = st.stdev(xs) if len(xs) > 1 else 0.0
    return f"{st.mean(xs):.2f} ± {sd:.2f} (n={len(xs)})"


def jain(xs):
    return sum(xs) ** 2 / (len(xs) * sum(x * x for x in xs)) if xs else 0


out = ["| Scenario | Metric | " + " | ".join(modes) + " |", "|---|---|" + "---|" * len(modes)]
for (scn, met) in sorted({(k[0], k[1]) for k in vals}):
    out.append(f"| {scn} | {met} | " + " | ".join(fmt(vals.get((scn, met, m), [])) for m in modes) + " |")

fair = []
for scn in sorted({k[0] for k in per_client if not k[0].startswith('hog_')}):
    cells = []
    for mode in modes:
        means = [st.mean(v) for (s, m, c), v in per_client.items() if s == scn and m == mode]
        cells.append(f"{jain(means):.3f} ({len(means)} clients)" if len(means) > 1 else "-")
    if any(c != "-" for c in cells):
        fair.append(f"| {scn} | " + " | ".join(cells) + " |")
if fair:
    out += ["", "Jain fairness index (1.0 = perfectly fair):", "",
            "| Scenario | " + " | ".join(modes) + " |", "|---|" + "---|" * len(modes)] + fair

text = "\n".join(out)
open(os.path.join(BASE_DIR, "results_summary.md"), "w").write(text + "\n")
print(text)
