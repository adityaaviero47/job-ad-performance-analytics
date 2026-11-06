"""Download the 5,000-posting sample and write the compressed copy the analysis reads.
Only needed if data/ is empty:  python get_data.py"""
import os, pandas as pd

# 5,000-row random sample (seed 42) of the Kaggle "LinkedIn Job Postings (2023-2024)" dataset by arshkon (CC BY-SA 4.0),
# published in a public GitHub repo
URL = ("https://raw.githubusercontent.com/claretondori/qa_data_suite/53931f866c4af8af1a4907a5016ca49532ff0150/"
       "data/job_postings_sample.csv")

def build(src=URL):
    d = pd.read_csv(src)
    os.makedirs("data", exist_ok=True)
    d.to_csv("data/job_postings_sample.csv.gz", index=False, compression="gzip")
    print(f"data/job_postings_sample.csv.gz  {len(d):,} rows")

if __name__ == "__main__":
    build()
