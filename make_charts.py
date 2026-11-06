"""Charts for README from results/results.json and the data."""
import json, matplotlib, numpy as np, pandas as pd
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("results/results.json"))
d = pd.read_csv("data/job_postings_sample.csv.gz")
fig, ax = plt.subplots(2, 2, figsize=(11.5, 7.6))
v = np.sort(d.views.dropna().to_numpy())[::-1]
x = np.arange(1, len(v) + 1) / len(v) * 100; y = np.cumsum(v) / v.sum() * 100
ax[0, 0].plot(x, y, color="#0052CC"); ax[0, 0].plot([0, 100], [0, 100], "--", color="#9AA5AD")
ax[0, 0].scatter([10], [R["visibility"]["top10_share_of_views"] * 100], color="#E07A2F", zorder=3)
ax[0, 0].text(13, R["visibility"]["top10_share_of_views"] * 100 - 6, f"Top 10% of postings get\n{R['visibility']['top10_share_of_views']*100:.0f}% of all views", fontsize=9)
ax[0, 0].set_xlabel("Share of postings, most viewed first (%)"); ax[0, 0].set_ylabel("Share of all views (%)")
ax[0, 0].set_title("Visibility: most job ads are barely seen")

F = [f for f in R["families"] if f["family"] != "Other"]
F = sorted(F, key=lambda f: f["mean_views"])
ax[0, 1].barh([f["family"] for f in F], [f["mean_views"] for f in F], color=["#E07A2F" if f["family"] == "Healthcare" else "#0052CC" for f in F])
for i, f in enumerate(F): ax[0, 1].text(f["mean_views"] + .5, i, f"{f['share']*100:.0f}% of postings", va="center", fontsize=8)
ax[0, 1].set_xlabel("Average views per posting"); ax[0, 1].set_xlim(0, 45)
ax[0, 1].set_title("Healthcare: 12% of postings, lowest views")

s = R["segments"][0]
ax[1, 0].bar(["No salary", "Salary shown"], [s["mean_views_no"], s["mean_views_yes"]], color=["#9AA5AD", "#0052CC"], width=.5)
for i, val in enumerate([s["mean_views_no"], s["mean_views_yes"]]): ax[1, 0].text(i, val + .4, f"{val:.1f}", ha="center")
ax[1, 0].set_ylabel("Average views per posting"); ax[1, 0].set_ylim(0, 23)
ax[1, 0].set_title(f"Showing pay: {s['mean_views_yes']/s['mean_views_no']*100-100:.0f}% more views (only {s['share']*100:.0f}% do)")

t = R["triage"]
ax[1, 1].bar(["Share of views", "Share of applications"], [t["weak_conversion_view_share"] * 100, t["weak_conversion_apply_share"] * 100], color=["#9AA5AD", "#E07A2F"], width=.5)
for i, val in enumerate([t["weak_conversion_view_share"] * 100, t["weak_conversion_apply_share"] * 100]): ax[1, 1].text(i, val + .5, f"{val:.1f}%", ha="center")
ax[1, 1].set_ylabel("%"); ax[1, 1].set_ylim(0, 22)
ax[1, 1].set_title("Weakest-converting quarter of ads: views without applies")
for a in ax.flat: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("results/summary.png", dpi=150)
