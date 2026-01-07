# main.py
from backend.cleaning import clean_data
from backend.analysis import analyze_and_detect
from backend.export_results import export_for_dashboard

def run_all():
    print("== Step 1: Cleaning ==")
    clean_data()

    print("\n== Step 2: Analysis + Anomalies ==")
    analyze_and_detect()

    print("\n== Step 3: Export for React Dashboard ==")
    export_for_dashboard()

    print("\n All steps completed. Check:")
    print("- Data/healthcare_cleaned.csv")
    print("- outputs/report/")
    print("- outputs/anomalies/")
    print("- outputs/ (anomalies.json, summary.json, top_groups.json)")

if __name__ == "__main__":
    run_all()
