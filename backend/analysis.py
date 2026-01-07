
import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CLEAN_PATH = os.path.join(BASE_DIR, "Data", "healthcare_cleaned.csv")
ANOM_DIR = os.path.join(BASE_DIR, "outputs", "anomalies")
REPORT_DIR = os.path.join(BASE_DIR, "outputs", "report")
TABLES_DIR = os.path.join(BASE_DIR, "outputs", "tables")

os.makedirs(ANOM_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

SUMMARY_PATH = os.path.join(REPORT_DIR, "02_analysis_summary.txt")


def _safe_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _iqr_bounds(x: pd.Series):
    """Return (q1, q3, iqr, lower, upper) for numeric series."""
    x = x.dropna()
    if len(x) < 8:
        return (np.nan, np.nan, np.nan, np.nan, np.nan)
    q1 = x.quantile(0.25)
    q3 = x.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return (q1, q3, iqr, lower, upper)


def _zscore(x: pd.Series) -> pd.Series:
    x = x.astype(float)
    mu = x.mean()
    sd = x.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return pd.Series([np.nan] * len(x), index=x.index)
    return (x - mu) / sd


def analyze_and_detect():

    df = pd.read_csv(CLEAN_PATH, low_memory=False)

    # Ensure required columns exist
    required = ["hcpcs_cd", "hcpcs_desc", "avg_mdcr_pymt_amt", "submitted_to_payment_ratio"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column in cleaned data: {col}")

   
    df["avg_mdcr_pymt_amt"] = _safe_numeric(df["avg_mdcr_pymt_amt"])
    df["submitted_to_payment_ratio"] = _safe_numeric(df["submitted_to_payment_ratio"])


    group_key = "hcpcs_cd"


    id_cols = [
        "hcpcs_cd", "hcpcs_desc",
        "rndrng_npi", "rndrng_prvdr_last_org_name", "rndrng_prvdr_first_name",
        "rndrng_prvdr_type",
        "place_of_srvc", "place_of_srvc_label",
        "rndrng_prvdr_state_abrvtn", "rndrng_prvdr_city",
        "tot_benes", "tot_srvcs",
        "avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt",
        "submitted_to_payment_ratio", "payment_to_allowed_ratio"
    ]
    id_cols = [c for c in id_cols if c in df.columns]


    iqr_rows = []

   
    group_sizes = df.groupby(group_key).size()

  
    min_group_size = 30
    valid_groups = set(group_sizes[group_sizes >= min_group_size].index.tolist())

    
    metrics = [
        ("avg_mdcr_pymt_amt", "Payment Amount"),
        ("submitted_to_payment_ratio", "Submitted/Payment Ratio"),
    ]

    for hcpcs, g in df.groupby(group_key, sort=False):
        if hcpcs not in valid_groups:
            continue

        for metric_col, metric_label in metrics:
            x = _safe_numeric(g[metric_col])
            q1, q3, iqr, lower, upper = _iqr_bounds(x)
            if np.isnan(upper):
                continue

            mask = (x > upper)  
            if mask.sum() == 0:
                continue

            sub = g.loc[mask, id_cols].copy()
            sub["anomaly_method"] = "IQR"
            sub["anomaly_metric"] = metric_col
            sub["anomaly_metric_label"] = metric_label
            sub["group_key"] = group_key
            sub["group_value"] = hcpcs
            sub["group_size"] = int(len(g))
            sub["iqr_q1"] = q1
            sub["iqr_q3"] = q3
            sub["iqr"] = iqr
            sub["iqr_upper_bound"] = upper
            sub["iqr_lower_bound"] = lower
            sub["anomaly_reason"] = f"{metric_col} > HCPCS-specific IQR upper bound"

            sub["_sort_metric"] = _safe_numeric(sub[metric_col])
            sub = sub.sort_values("_sort_metric", ascending=False).drop(columns=["_sort_metric"])

            iqr_rows.append(sub)

    anomalies_iqr = pd.concat(iqr_rows, ignore_index=True) if iqr_rows else pd.DataFrame(columns=id_cols)

    z_rows = []
    z_threshold = 3.5  
    for hcpcs, g in df.groupby(group_key, sort=False):
        if hcpcs not in valid_groups:
            continue

        for metric_col, metric_label in metrics:
            x = _safe_numeric(g[metric_col])
            x = x.dropna()
            if len(x) < min_group_size:
                continue

            z = _zscore(x)
            mask = (z > z_threshold)
            if mask.sum() == 0:
                continue

            idx = z.index[mask]
            sub = g.loc[idx, id_cols].copy()
            sub["anomaly_method"] = "Z-score"
            sub["anomaly_metric"] = metric_col
            sub["anomaly_metric_label"] = metric_label
            sub["group_key"] = group_key
            sub["group_value"] = hcpcs
            sub["group_size"] = int(len(g))
            sub["z_score"] = z.loc[idx].values
            sub["z_threshold"] = z_threshold
            sub["anomaly_reason"] = f"{metric_col} Z-score > {z_threshold} within HCPCS group"

            sub["_sort_metric"] = _safe_numeric(sub[metric_col])
            sub = sub.sort_values("_sort_metric", ascending=False).drop(columns=["_sort_metric"])

            z_rows.append(sub)

    anomalies_z = pd.concat(z_rows, ignore_index=True) if z_rows else pd.DataFrame(columns=id_cols)

    out_iqr = os.path.join(ANOM_DIR, "anomalies_iqr.csv")
    out_z = os.path.join(ANOM_DIR, "anomalies_zscore.csv")
    anomalies_iqr.to_csv(out_iqr, index=False)
    anomalies_z.to_csv(out_z, index=False)


    pay = _safe_numeric(df["avg_mdcr_pymt_amt"]).dropna()
    ratio = _safe_numeric(df["submitted_to_payment_ratio"]).replace([np.inf, -np.inf], np.nan).dropna()


    top_iqr_groups = (
        anomalies_iqr.groupby(["anomaly_metric", "hcpcs_cd", "hcpcs_desc"], dropna=False)
        .size().reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(20)
    )

    top_z_groups = (
        anomalies_z.groupby(["anomaly_metric", "hcpcs_cd", "hcpcs_desc"], dropna=False)
        .size().reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(20)
    )

    top_iqr_groups.to_csv(os.path.join(TABLES_DIR, "top_iqr_groups.csv"), index=False)
    top_z_groups.to_csv(os.path.join(TABLES_DIR, "top_zscore_groups.csv"), index=False)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("=== Analysis Summary (HCPCS Group-wise) ===\n")
        f.write(f"rows_total: {len(df)}\n")
        f.write(f"columns_total: {len(df.columns)}\n")
        f.write(f"group_column: {group_key}\n")
        f.write(f"min_group_size_used: {min_group_size}\n")
        f.write("\n")

        f.write("=== Payment (avg_mdcr_pymt_amt) Global Stats ===\n")
        if len(pay) > 0:
            f.write(f"mean: {pay.mean():.6f}\n")
            f.write(f"median: {pay.median():.6f}\n")
            f.write(f"min: {pay.min():.6f}\n")
            f.write(f"max: {pay.max():.6f}\n")
            f.write(f"std: {pay.std(ddof=0):.6f}\n")
        f.write("\n")

        f.write("=== Submitted/Payment Ratio Global Stats ===\n")
        if len(ratio) > 0:
            f.write(f"mean: {ratio.mean():.6f}\n")
            f.write(f"median: {ratio.median():.6f}\n")
            f.write(f"min: {ratio.min():.6f}\n")
            f.write(f"max: {ratio.max():.6f}\n")
            f.write(f"std: {ratio.std(ddof=0):.6f}\n")
        f.write("\n")

        f.write("=== Anomalies Counts ===\n")
        f.write(f"IQR anomalies total: {len(anomalies_iqr)}\n")
        f.write(f"Z-score anomalies total: {len(anomalies_z)}\n\n")

        f.write("=== Notes for Reporting ===\n")
        f.write("- IQR anomalies are defined per HCPCS code (service) to avoid mixing different services.\n")
        f.write("- Ratio anomalies highlight cases where submitted charges are disproportionately higher than Medicare payments.\n")
        f.write("- Use place_of_srvc_label + provider_type to interpret why costs differ (office vs facility, specialty differences).\n")
        f.write("\n")

    print("Analysis + anomalies done")
    print("Saved:")
    print("-", out_iqr)
    print("-", out_z)
    print("-", SUMMARY_PATH)
    print("-", os.path.join(TABLES_DIR, "top_iqr_groups.csv"))
    print("-", os.path.join(TABLES_DIR, "top_zscore_groups.csv"))
if __name__ == "__main__":
    analyze_and_detect()
