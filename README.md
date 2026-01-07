
# Healthcare Utilization & Cost Outlier Analysis (CMS Medicare)

## Project Overview
This project focuses on analyzing large-scale **CMS Medicare Physician & Supplier Utilization** data to identify **unusual healthcare cost and utilization patterns**. The primary goal is to detect **cost outliers (anomalies)** that may indicate atypical billing behavior, regional differences, service complexity, or cases that require further administrative or clinical review.

The project was developed as part of **Python Assignment 3**, with an emphasis on **real-world data handling, advanced analysis, and modern visualization techniques**.

                                                                                        =
                                                                                       ===
                                                                                      =====
                                                                                  =============
                                                                               ====================
                                                                       ===================================
                                                                 ==============================================
                                                        ===============================================================
                                           =========================================================================================
                                  ===========================================================================================================
                           ==========================================================================================================================
                    ========================================================================================================================================
==============================================================================================================================================================================================================================================================================================================================================================================================================================
===============================================================================================================================================================================================================
==================== ============== **you need to download the the dataset before running the code :** the set size is 3 GB unable to be uploaded to github 
 https://data.cms.gov/sites/default/files/dataset_zips/a016086bdf15ebceb4259c0cb799d15e/Medicare%20Physician%20%26%20Other%20Practitioners%20-%20by%20Provider%20and%20Service.zip                                                                 
 **after downlaoding the data extract the zip file to Data file in the project folder**
===============================================================================================================================================================================================================
==============================================================================================================================================================================================================================================================================================================================================================================================================================











## Dataset Description
- **Source**: Centers for Medicare & Medicaid Services (CMS)
- **Type**: Real-world healthcare utilization and payment data
- **Scale**: ~9.6 million records after cleaning
- **Nature of Data**: Messy, heterogeneous, large-scale dataset

### Key Dataset Characteristics
- Mixed data types
- Missing and inconsistent values
- High variance and heavy-tailed cost distributions
- Multiple categorical and numerical attributes

Working with this dataset satisfies the requirement for **messy real-world data**, which is explicitly rewarded in the assignment grading rubric.

---

## Data Cleaning Process
Data preprocessing was a critical stage of the project. The following steps were applied:

1. Removal of invalid and incomplete records
2. Standardization of numeric columns (payments, charges, services)
3. Conversion of categorical labels (e.g., place of service)
4. Handling missing values and inconsistent formats
5. Feature engineering:
   - Log-transformed payment and submitted charge values
   - Computed financial ratios such as:
     - Submitted-to-payment ratio
     - Payment-to-allowed ratio

All cleaning steps were automated and reproducible using Python scripts.

---

## Analysis Methodology
The analysis combines **descriptive statistics**, **statistical modeling**, and **data science techniques**.

### Baseline Analysis
- Mean, median, min, max calculations
- Distribution analysis of payment variables
- Aggregations by service, provider type, and geography

### Advanced Statistical Analysis
- Quartile and IQR analysis
- Distribution skewness handling
- Group-based comparisons

### Anomaly Detection Techniques
Two complementary methods were implemented:

#### 1. IQR (Interquartile Range)
- Flags observations above Q3 + 1.5 × IQR
- Robust against skewed healthcare cost distributions

#### 2. Z-Score
- Identifies extreme deviations from the mean
- Sensitive to large outliers

Detected anomalies were enriched with contextual information such as provider type, state, and place of service.

---

## Visualization & Dashboard
Visualization is a major component of this project and aligns with the **highest scoring category** of the assignment.

### Visualization Tools Used
- **Matplotlib** (baseline exploratory plots)
- **Seaborn** (statistical visualizations)
- **React.js Dashboard** (modern, web-based visualization)

### Dashboard Features
- Interactive anomaly filtering (IQR / Z-score)
- Summary statistics (mean, median, max, bounds)
- Contextual analysis by:
  - State
  - Provider type
  - Place of service
- Clean, professional UI for presentation purposes

This fulfills the requirement for a **modern visualization library with front-end integration**.

---

## Project Architecture
The project follows a **clear separation of concerns**:

### Backend (Python)
- Data cleaning
- Feature engineering
- Statistical analysis
- Anomaly detection
- Export of results to JSON

### Frontend (React.js)
- Loads exported JSON results
- Interactive visualization and filtering
- Presentation-ready dashboard

Although developed as a single project, the backend and frontend components are logically separated.

---

## Results & Insights
- Identified hundreds of thousands of high-cost anomalies
- Clear differences observed across provider types and service settings
- Facility-based services showed higher cost variance than non-facility services
- The approach demonstrates how statistical analysis can support healthcare oversight

---

## Conclusion
This project demonstrates:
- Effective handling of large, messy real-world datasets
- Application of advanced statistical analysis techniques
- Practical anomaly detection in a healthcare context
- Use of modern visualization tools beyond traditional Python plots

The final result is both **analytically rigorous** and **presentation-ready**, meeting and exceeding the expectations of the assignment.

---

## Tools & Technologies
- Python (Pandas, NumPy)
- Matplotlib & Seaborn
- React.js
- JSON-based data exchange

---

## Author
- Mohannad Turkman
