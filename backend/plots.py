# backend/plots.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

CLEAN_PATH = os.path.join("Data", "healthcare_cleaned.csv")
PLOTS_DIR = os.path.join("outputs", "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

def pick_cost_column(df: pd.DataFrame) -> str:
  
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(num_cols) == 1:
        return num_cols[0]
   
    keywords = ["price", "payment", "charge", "cost", "amount", "rate"]
    for k in keywords:
        for c in num_cols:
            if k in c.lower():
                return c
    return num_cols[0] if num_cols else ""

def make_plots():
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    cost_col = pick_cost_column(df)
    if cost_col == "":
        raise SystemExit("No numeric cost column found in cleaned data.")

   
    plt.figure()
    sns.histplot(df[cost_col].dropna(), bins=60)
    plt.title(f"Distribution of {cost_col}")
    plt.xlabel(cost_col)
    plt.savefig(os.path.join(PLOTS_DIR, "01_hist_cost.png"), bbox_inches="tight")
    plt.close()

  
    plt.figure()
    sns.boxplot(x=df[cost_col])
    plt.title(f"Boxplot of {cost_col} (Outliers)")
    plt.xlabel(cost_col)
    plt.savefig(os.path.join(PLOTS_DIR, "02_boxplot_cost.png"), bbox_inches="tight")
    plt.close()

    
    cap = df[cost_col].quantile(0.99)
    plt.figure()
    sns.boxplot(x=df[df[cost_col] <= cap][cost_col])
    plt.title(f"Boxplot of {cost_col} (<= 99th percentile)")
    plt.xlabel(cost_col)
    plt.savefig(os.path.join(PLOTS_DIR, "03_boxplot_cost_99pct.png"), bbox_inches="tight")
    plt.close()

    print(" Plots saved to outputs/plots:")
    print("- 01_hist_cost.png")
    print("- 02_boxplot_cost.png")
    print("- 03_boxplot_cost_99pct.png")

if __name__ == "__main__":
    make_plots()
