
import os
import re
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

RAW_PATH = os.path.join(BASE_DIR, "Data", "healthcare_raw.csv")
CLEAN_PATH = os.path.join(BASE_DIR, "Data", "healthcare_cleaned.csv")

REPORT_DIR = os.path.join(BASE_DIR, "outputs", "report")
os.makedirs(REPORT_DIR, exist_ok=True)
CLEAN_REPORT_PATH = os.path.join(REPORT_DIR, "01_cleaning_profile.txt")


def _normalize_colname(c: str) -> str:
    """Normalize column names to snake_case, lowercase, safe for matching."""
    c = c.strip()
    c = c.replace("\ufeff", "") 
    c = c.lower()
  
    c = re.sub(r"[^\w]+", "_", c)
    c = re.sub(r"_+", "_", c).strip("_")
    return c


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Convert messy numeric strings to float (handles $, commas, blanks)."""
    if series.dtype != object:
        return pd.to_numeric(series, errors="coerce")

    s = series.astype(str).str.strip()

 
    s = s.replace({"": np.nan, "nan": np.nan, "none": np.nan, "null": np.nan, "*": np.nan})

    s = s.str.replace(r"[\$,]", "", regex=True)

    s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)

    return pd.to_numeric(s, errors="coerce")


def clean_data():
    print("Reading raw CSV:", RAW_PATH)
    df = pd.read_csv(RAW_PATH, low_memory=False)

    original_cols = list(df.columns)
    df.columns = [_normalize_colname(c) for c in df.columns]

  
    rename_map = {}

    def pick(*candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

   
    c_npi = pick("rndrng_npi", "rendering_npi", "npi")
    if c_npi: rename_map[c_npi] = "rndrng_npi"

    c_ptype = pick("rndrng_prvdr_type", "provider_type", "provider_type_desc", "prvdr_type")
    if c_ptype: rename_map[c_ptype] = "rndrng_prvdr_type"

 
    c_hcpcs = pick("hcpcs_cd", "hcpcs_code", "hcpcs")
    if c_hcpcs: rename_map[c_hcpcs] = "hcpcs_cd"

    c_desc = pick("hcpcs_desc", "hcpcs_description", "hcpcs_desc_txt", "hcpcs_description_txt")
    if c_desc: rename_map[c_desc] = "hcpcs_desc"

    c_drug = pick("hcpcs_drug_ind", "drug_ind", "hcpcs_drug_indicator")
    if c_drug: rename_map[c_drug] = "hcpcs_drug_ind"

   
    c_pos = pick("place_of_srvc", "place_of_service", "pos", "place_of_svc")
    if c_pos: rename_map[c_pos] = "place_of_srvc"


    c_srvcs = pick("tot_srvcs", "total_services", "tot_srvs", "line_srvc_cnt", "line_service_cnt")
    if c_srvcs: rename_map[c_srvcs] = "tot_srvcs"

    c_benes = pick("tot_benes", "total_beneficiaries", "bene_unique_cnt", "bene_cnt")
    if c_benes: rename_map[c_benes] = "tot_benes"

 
    c_sub = pick(
        "avg_sbmtd_chrg",
        "average_submitted_charge_amount",
        "avg_sbmtd_chrg_amt",
        "average_submitted_charge_amt",
        "avg_submitted_charge_amt"
    )
    if c_sub: rename_map[c_sub] = "avg_sbmtd_chrg_amt"

    c_allowed = pick(
        "avg_mdcr_alowd_amt",
        "average_medicare_allowed_amount",
        "avg_mdcr_allowed_amt",
        "average_medicare_allowed_amt"
    )
    if c_allowed: rename_map[c_allowed] = "avg_mdcr_alowd_amt"

    c_pay = pick(
        "avg_mdcr_pymt_amt",
        "average_medicare_payment_amount",
        "avg_mdcr_payment_amt",
        "average_medicare_payment_amt"
    )
    if c_pay: rename_map[c_pay] = "avg_mdcr_pymt_amt"

    c_std = pick(
        "avg_mdcr_stdzd_amt",
        "average_medicare_standardized_amount",
        "avg_mdcr_standardized_amt",
        "average_medicare_standardized_amt"
    )
    if c_std: rename_map[c_std] = "avg_mdcr_stdzd_amt"


    df = df.rename(columns=rename_map)

  
    for col in ["hcpcs_cd", "hcpcs_desc", "rndrng_prvdr_type", "place_of_srvc", "hcpcs_drug_ind"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    
    if "hcpcs_cd" in df.columns:
        df["hcpcs_cd"] = df["hcpcs_cd"].astype(str).str.upper().str.strip()
        df.loc[df["hcpcs_cd"].isin(["NAN", "NONE"]), "hcpcs_cd"] = np.nan

 
    if "place_of_srvc" in df.columns:
        df["place_of_srvc"] = df["place_of_srvc"].astype(str).str.upper().str.strip()
        df.loc[df["place_of_srvc"].isin(["NAN", "NONE"]), "place_of_srvc"] = np.nan
        df["place_of_srvc_label"] = df["place_of_srvc"].map({
            "F": "Facility",
            "O": "Office"
        }).fillna("Unknown")

    numeric_cols = [
        "tot_srvcs", "tot_benes",
        "avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _coerce_numeric(df[col])

  
    has_payment = "avg_mdcr_pymt_amt" in df.columns
    has_submitted = "avg_sbmtd_chrg_amt" in df.columns

    if has_payment:
        df = df[df["avg_mdcr_pymt_amt"].notna()]
    elif has_submitted:
        df = df[df["avg_sbmtd_chrg_amt"].notna()]
    else:
      
        pass

    for col in ["tot_srvcs", "tot_benes", "avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt"]:
        if col in df.columns:
            df.loc[df[col] < 0, col] = np.nan

    if has_payment:
        df["log_payment"] = np.log1p(df["avg_mdcr_pymt_amt"])
    if has_submitted:
        df["log_submitted"] = np.log1p(df["avg_sbmtd_chrg_amt"])

    if has_submitted and has_payment:
        df["submitted_to_payment_ratio"] = df["avg_sbmtd_chrg_amt"] / df["avg_mdcr_pymt_amt"].replace({0: np.nan})

    if "avg_mdcr_alowd_amt" in df.columns and has_payment:
        df["payment_to_allowed_ratio"] = df["avg_mdcr_pymt_amt"] / df["avg_mdcr_alowd_amt"].replace({0: np.nan})

  
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)


    df.to_csv(CLEAN_PATH, index=False)

    
    with open(CLEAN_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("=== Cleaning Profile ===\n")
        f.write(f"raw_path: {RAW_PATH}\n")
        f.write(f"clean_path: {CLEAN_PATH}\n\n")
        f.write(f"original_columns_count: {len(original_cols)}\n")
        f.write(f"normalized_columns_count: {len(df.columns)}\n")
        f.write("normalized_columns:\n")
        for c in df.columns:
            f.write(f"- {c}\n")
        f.write("\n")
        f.write(f"rows_after_cleaning: {len(df)}\n")
        f.write(f"duplicates_removed: {before - after}\n\n")

   
        key_cols = ["hcpcs_cd", "hcpcs_desc", "rndrng_prvdr_type", "place_of_srvc",
                    "tot_srvcs", "tot_benes",
                    "avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt"]
        f.write("missing_values_key_columns:\n")
        for c in key_cols:
            if c in df.columns:
                f.write(f"- {c}: {int(df[c].isna().sum())}\n")
        f.write("\n")

       
        money_cols = [c for c in ["avg_sbmtd_chrg_amt", "avg_mdcr_alowd_amt", "avg_mdcr_pymt_amt", "avg_mdcr_stdzd_amt"] if c in df.columns]
        if money_cols:
            f.write("money_column_stats:\n")
            for c in money_cols:
                s = df[c].dropna()
                if len(s) > 0:
                    f.write(f"- {c}: mean={s.mean():.4f}, median={s.median():.4f}, min={s.min():.4f}, max={s.max():.4f}\n")

    print("Cleaning done ")
    print("Saved:", CLEAN_PATH)
    print("Report:", CLEAN_REPORT_PATH)
