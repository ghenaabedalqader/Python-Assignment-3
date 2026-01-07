
import os
import json
import math
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CLEAN_PATH = os.path.join(BASE_DIR, "Data", "healthcare_cleaned.csv")

ANOM_IQR_PATH = os.path.join(BASE_DIR, "outputs", "anomalies", "anomalies_iqr.csv")
ANOM_Z_PATH = os.path.join(BASE_DIR, "outputs", "anomalies", "anomalies_zscore.csv")

TOP_IQR_GROUPS = os.path.join(BASE_DIR, "outputs", "tables", "top_iqr_groups.csv")
TOP_Z_GROUPS = os.path.join(BASE_DIR, "outputs", "tables", "top_zscore_groups.csv")

OUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

SUMMARY_JSON = os.path.join(OUT_DIR, "summary.json")
ANOM_JSON = os.path.join(OUT_DIR, "anomalies.json")
TOP_GROUPS_JSON = os.path.join(OUT_DIR, "top_groups.json")


def _to_py(x):
    """Convert numpy/pandas scalars to plain Python types + handle NaN/inf."""
    if x is None:
        return None
    try:
      
        if pd.isna(x):
            return None
    except Exception:
        pass

   
    if isinstance(x, float):
        if math.isfinite(x):
            return x
        return None

  
    if hasattr(x, "item"):
        try:
            return x.item()
        except Exception:
            pass

    return x


def _sanitize_records(df: pd.DataFrame):
    """Return list[dict] JSON-safe (no NaN, no numpy types)."""
    if df is None or len(df) == 0:
        return []
    df2 = df.copy()
   
    df2 = df2.replace([float("inf"), -float("inf")], pd.NA)
    df2 = df2.where(pd.notnull(df2), None)
    records = df2.to_dict(orient="records")
    out = []
    for r in records:
        out.append({k: _to_py(v) for k, v in r.items()})
    return out


def _read_if_exists(path: str) -> pd.DataFrame:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return pd.read_csv(path, low_memory=False)
    return pd.DataFrame()


def _pick_cost_column(df: pd.DataFrame) -> str:
 
    priority = [
        "avg_mdcr_pymt_amt",
        "avg_mdcr_stdzd_amt",
        "avg_mdcr_alowd_amt",
        "avg_sbmtd_chrg_amt",
        "price_amt",
    ]
    for c in priority:
        if c in df.columns:
            return c
   
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    return numeric_cols[0] if numeric_cols else "price_amt"


def export_for_dashboard():
   
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    cost_col = _pick_cost_column(df)

  
    s = pd.to_numeric(df[cost_col], errors="coerce").replace([float("inf"), -float("inf")], pd.NA).dropna()

    summary = {
       
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "cost_column": cost_col,
        "cost_mean": None,
        "cost_median": None,
        "cost_min": None,
        "cost_max": None,
        "cost_std": None,
        "Q1": None,
        "Q3": None,
        "IQR": None,
        "IQR_lower_bound": None,
        "IQR_upper_bound": None,
        "missing_cost": int(df[cost_col].isna().sum()) if cost_col in df.columns else None,

     
        "iqr_anomalies_count": 0,
        "zscore_anomalies_count": 0,

       
        "key_columns_present": {
            "hcpcs_cd": "hcpcs_cd" in df.columns,
            "hcpcs_desc": "hcpcs_desc" in df.columns,
            "rndrng_npi": "rndrng_npi" in df.columns,
            "rndrng_prvdr_type": "rndrng_prvdr_type" in df.columns,
            "rndrng_prvdr_state_abrvtn": "rndrng_prvdr_state_abrvtn" in df.columns,
            "place_of_srvc_label": "place_of_srvc_label" in df.columns,
        }
    }

    if len(s) > 0:
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        iqr = float(q3 - q1)
        lower = float(q1 - 1.5 * iqr)
        upper = float(q3 + 1.5 * iqr)

        summary.update({
            "cost_mean": float(s.mean()),
            "cost_median": float(s.median()),
            "cost_min": float(s.min()),
            "cost_max": float(s.max()),
            "cost_std": float(s.std(ddof=0)),
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "IQR_lower_bound": lower,
            "IQR_upper_bound": upper,
        })

   
    keep_cols = [
        "hcpcs_cd", "hcpcs_desc",
        "rndrng_npi", "rndrng_prvdr_last_org_name", "rndrng_prvdr_first_name",
        "rndrng_prvdr_type",
        "rndrng_prvdr_state_abrvtn", "rndrng_prvdr_city",
        "place_of_srvc_label",
        "tot_benes", "tot_srvcs",
        "avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt",
        "submitted_to_payment_ratio", "payment_to_allowed_ratio",
        "anomaly_method", "anomaly_metric", "anomaly_metric_label", "anomaly_reason",
        "group_size"
    ]

    iqr_df = _read_if_exists(ANOM_IQR_PATH)
    z_df = _read_if_exists(ANOM_Z_PATH)

    summary["iqr_anomalies_count"] = int(len(iqr_df)) if len(iqr_df) else 0
    summary["zscore_anomalies_count"] = int(len(z_df)) if len(z_df) else 0

    all_anoms = pd.concat([iqr_df, z_df], ignore_index=True) if (len(iqr_df) or len(z_df)) else pd.DataFrame()

    if len(all_anoms) > 0:
        cols = [c for c in keep_cols if c in all_anoms.columns]
        all_anoms = all_anoms[cols].copy()

        
        sort_col = summary["cost_column"] if summary["cost_column"] in all_anoms.columns else (
            "avg_mdcr_pymt_amt" if "avg_mdcr_pymt_amt" in all_anoms.columns else None
        )

        if sort_col:
            all_anoms[sort_col] = pd.to_numeric(all_anoms[sort_col], errors="coerce")
            all_anoms = all_anoms.sort_values(sort_col, ascending=False)

      
        all_anoms = all_anoms.head(5000)

        anomalies_payload = _sanitize_records(all_anoms)
    else:
        anomalies_payload = []

  
    top_groups = {}

    iqr_groups_df = _read_if_exists(TOP_IQR_GROUPS)
    z_groups_df = _read_if_exists(TOP_Z_GROUPS)

    top_groups["top_iqr_groups"] = _sanitize_records(iqr_groups_df.head(50)) if len(iqr_groups_df) else []
    top_groups["top_zscore_groups"] = _sanitize_records(z_groups_df.head(50)) if len(z_groups_df) else []

   
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(ANOM_JSON, "w", encoding="utf-8") as f:
        json.dump(anomalies_payload, f, indent=2, ensure_ascii=False)

    with open(TOP_GROUPS_JSON, "w", encoding="utf-8") as f:
        json.dump(top_groups, f, indent=2, ensure_ascii=False)

    print("Export done ✅")
    print("- outputs/summary.json")
    print("- outputs/anomalies.json")
    print("- outputs/top_groups.json")
