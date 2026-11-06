"""Job ad performance analytics: what turns a job posting's views into applications?
Data: a 5,000-posting random sample of the LinkedIn Job Postings 2023-2024 dataset (arshkon, Kaggle, CC BY-SA 4.0),
postings listed Jan-Apr 2024. Reproduces every number in README.md:  python run_analysis.py"""
import json, re, numpy as np, pandas as pd
from scipy.stats import mannwhitneyu

R = {}
d = pd.read_csv("data/job_postings_sample.csv.gz", parse_dates=["posted_date", "expiry_date", "closed_date"])

# ---------- 1. data checks ----------
key = d.job_title.str.lower().str.strip() + "|" + d.company_name.fillna("").str.lower().str.strip() + "|" + d.location.str.lower()
checks = dict(
    postings=len(d), missing_company=int(d.company_name.isna().sum()), missing_views=int(d.views.isna().sum()),
    applies_not_recorded=int(d.applies.isna().sum()), applies_not_recorded_share=float(d.applies.isna().mean()),
    salary_shown=int(d.salary_min.notna().sum()), salary_min_above_max=int((d.salary_min > d.salary_max).sum()),
    applies_above_views=int((d.applies > d.views).sum()), expiry_before_posting=int((d.expiry_date < d.posted_date).sum()),
    probable_duplicates=int(key.duplicated().sum()))
R["validation"] = checks
R["data"] = dict(start=str(d.posted_date.min().date()), end=str(d.posted_date.max().date()))

# ---------- 2. visibility: how views are spread across postings ----------
v = d.views.dropna().sort_values(ascending=False)
R["visibility"] = dict(postings_with_views=int(len(v)), total_views=int(v.sum()), median_views=float(v.median()),
                       top10_share_of_views=float(v.head(int(len(v) * .1)).sum() / v.sum()),
                       bottom50_share_of_views=float(v.tail(int(len(v) * .5)).sum() / v.sum()),
                       share_under_5_views=float((v < 5).mean()))

# ---------- 3. segments ----------
t = d.job_title.str.lower()
d["salary_shown"] = d.salary_min.notna() | d.salary_max.notna()
d["remote"] = t.str.contains(r"\bremote\b") | d.location.str.contains(r"\bremote\b", case=False)
d["senior"] = t.str.contains(r"\b(?:senior|sr\.?|lead|principal|manager|director|head)\b")
d["entry"] = t.str.contains(r"\b(?:intern|internship|junior|jr\.?|entry|graduate|trainee|associate)\b")
FAM = {"Healthcare": r"\b(?:nurse|rn|lpn|cna|physician|therap|medical|clinical|pharm|dental|patient|health)",
       "Software & data": r"\b(?:software|developer|engineer.*(?:software|data|cloud)|data|analyst|devops|python|java)",
       "Sales & marketing": r"\b(?:sales|marketing|account executive|business development|brand|seo)",
       "Driving & logistics": r"\b(?:driver|cdl|warehouse|logistics|delivery|forklift|truck)",
       "Admin & customer service": r"\b(?:customer service|admin|assistant|receptionist|clerk|call center|representative)",
       "Finance & accounting": r"\b(?:account|finance|financial|tax|audit|payroll|bookkeep)"}
def fam(s):
    for k, p in FAM.items():
        if re.search(p, s): return k
    return "Other"
d["family"] = t.map(fam)
# apply rate is measured only where applies are recorded and the posting had at least 10 views
a = d[d.applies.notna() & (d.views >= 10)].copy()
a["apply_rate"] = a.applies / a.views
R["apply_rate"] = dict(postings=int(len(a)), median=float(a.apply_rate.median()), pooled=float(a.applies.sum() / a.views.sum()),
                       top_quartile=float(a.apply_rate.quantile(.75)), bottom_quartile=float(a.apply_rate.quantile(.25)))
def compare(col, label):
    yes, no = d[d[col]], d[~d[col]]; ay, an = a[a[col]], a[~a[col]]
    return dict(segment=label, postings=int(len(yes)), share=float(d[col].mean()),
                median_views_yes=float(yes.views.median()), median_views_no=float(no.views.median()),
                mean_views_yes=float(yes.views.mean()), mean_views_no=float(no.views.mean()),
                views_p=float(mannwhitneyu(yes.views.dropna(), no.views.dropna()).pvalue),
                apply_rate_yes=float(ay.apply_rate.median()) if len(ay) else None, apply_rate_no=float(an.apply_rate.median()) if len(an) else None,
                apply_n_yes=int(len(ay)), apply_n_no=int(len(an)),
                apply_p=float(mannwhitneyu(ay.apply_rate, an.apply_rate).pvalue) if len(ay) > 5 and len(an) > 5 else None)
R["segments"] = [compare("salary_shown", "Salary shown"), compare("remote", "Remote"), compare("senior", "Senior title"), compare("entry", "Entry-level title")]
F = d.groupby("family").agg(postings=("views", "size"), median_views=("views", "median"), mean_views=("views", "mean"))
F["share"] = F.postings / len(d)
F["apply_rate_median"] = a.groupby("family").apply_rate.median()
F["apply_n"] = a.groupby("family").size()
R["families"] = F.sort_values("postings", ascending=False).round(4).reset_index().to_dict("records")

# ---------- 4. lever: what if postings without salary got the views of postings with salary ----------
s = R["segments"][0]
no_sal = d[~d.salary_shown]
extra_views = (s["mean_views_yes"] - s["mean_views_no"]) * no_sal.views.notna().sum()
R["salary_lever"] = dict(postings_without_salary=int(len(no_sal)), share=float(len(no_sal) / len(d)),
                         view_uplift_if_matched=float(s["mean_views_yes"] / s["mean_views_no"] - 1),
                         extra_views_on_sample=float(extra_views), share_of_total_views=float(extra_views / d.views.sum()),
                         note="association, not proven cause: postings that show pay differ in other ways")

# ---------- 5. campaign triage: postings that need help, using early signals ----------
# a distribution platform would boost postings with low visibility and flag postings with views but few applies
low_vis = d.views < 5
weak_conv = a.apply_rate < a.apply_rate.quantile(.25)
R["triage"] = dict(low_visibility_postings=int(low_vis.sum()), low_visibility_share=float(low_vis.mean()),
                   weak_conversion_postings=int(weak_conv.sum()),
                   weak_conversion_view_share=float(a.views[weak_conv].sum() / a.views.sum()),
                   weak_conversion_apply_share=float(a.applies[weak_conv].sum() / a.applies.sum()))

d[["posting_id", "job_title", "family", "salary_shown", "remote", "senior", "entry", "views", "applies"]].to_csv("results/postings_tagged.csv", index=False)
with pd.ExcelWriter("results/job_ad_dashboard.xlsx") as x:
    pd.DataFrame(list(checks.items()), columns=["check", "value"]).to_excel(x, sheet_name="Data checks", index=False)
    pd.DataFrame(R["segments"]).to_excel(x, sheet_name="Segments", index=False)
    F.to_excel(x, sheet_name="Job families")
    a.sort_values("apply_rate")[["posting_id", "job_title", "family", "views", "applies", "apply_rate"]].to_excel(x, sheet_name="Apply rate", index=False)
json.dump(R, open("results/results.json", "w"), indent=2, default=str)
print(json.dumps(R, indent=2, default=str))
