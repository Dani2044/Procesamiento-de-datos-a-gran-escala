# Bank Marketing Classification with PySpark MLlib

**Author:** Daniel Felipe Castro Moreno  
**Workshop:** Data Classification with Performance Metrics  
**Course:** High Volume Data Processing  
**Period:** April 28 – May 25, 2026

---

## Overview

This notebook implements a supervised binary classification pipeline on the [Bank Marketing dataset](https://archive.ics.uci.edu/dataset/222/bank+marketing) from the UCI Machine Learning Repository. Using Apache Spark (PySpark MLlib) as the distributed processing engine, five classification models are trained, evaluated, and compared to predict whether a bank customer will subscribe to a term deposit (`y = yes/no`).

The central challenge is a severe class imbalance (8.5:1 majority-to-minority ratio), making AUC-ROC, F1-Score, Precision, and Recall the primary evaluation metrics rather than simple accuracy.

---

## Dataset

**Source:** UCI ML Repository — Bank Marketing Dataset  
**Records:** 45,211 rows × 17 columns  
**Target variable:** `y` — Has the client subscribed to a term deposit? (`yes`/`no`)

The data covers telephone marketing campaigns of a Portuguese bank from 2008 to 2013. Input features include customer demographics (age, job, marital status, education), financial profile (balance, housing loan, personal loan, credit default), and campaign interaction details (contact channel, month, call duration, number of contacts).

---

## Requirements

- Apache Spark with PySpark (session initialized via `findspark`)
- Python 3.x
- NumPy, Pandas
- Matplotlib, Seaborn
- scikit-learn (for ROC curve computation)
- Input file: `bank-full.csv` (semicolon-delimited, with header)

Install dependencies:
```bash
pip install scikit-learn findspark pyspark numpy pandas matplotlib seaborn
```

---

## Pipeline Structure

The notebook follows an 11-step methodology:

| Step | Description |
|------|-------------|
| 1 | Spark environment setup and session initialization |
| 2 | Dataset loading and initial inspection |
| 3 | Data type casting (String → Integer for numeric columns) |
| 4 | Class balance analysis and imbalance quantification |
| 5 | Descriptive statistical analysis (per-column and global) |
| 6 | Exploratory Data Analysis — histograms, boxplots, bar charts, correlation matrix |
| 7 | Data preparation — outlier filtering, `pdays` removal, random oversampling |
| 8 | Feature encoding (`StringIndexer` + `OneHotEncoder`) and vector assembly |
| 9 | Training of five binary classifiers |
| 10 | Model evaluation with confusion matrices and ROC curves |
| 11 | Conclusions and best model selection |

---

## Models Trained

- **Logistic Regression** — linear baseline with logistic function
- **Decision Tree** — hierarchical rule-based model (`maxDepth=10`, Gini impurity)
- **Random Forest** — ensemble of 100 trees with random feature subsets (`maxDepth=10`)
- **LinearSVC (SVM)** — maximum-margin hyperplane classifier (`maxIter=100`, `regParam=0.01`)
- **Gradient Boosting (GBT)** — sequential corrective ensemble (`maxIter=50`, `maxDepth=5`, `stepSize=0.1`)

---

## Results Summary

| Model | Accuracy | Precision | Recall | F1-Score | AUC-ROC |
|-------|----------|-----------|--------|----------|---------|
| Gradient Boosting | 0.908 | 0.909 | 0.908 | 0.908 | **0.962** |
| Random Forest | 0.871 | 0.873 | 0.871 | 0.870 | 0.941 |
| Logistic Regression | 0.833 | 0.834 | 0.833 | 0.833 | 0.911 |
| LinearSVC (SVM) | 0.834 | 0.834 | 0.834 | 0.834 | 0.911 |
| Decision Tree | 0.857 | 0.860 | 0.857 | 0.856 | 0.717 |

**Best model: Gradient Boosting (GBT)** — highest AUC-ROC (0.962) and F1-Score (0.908) across all models. Its sequential, corrective learning captures non-linear feature interactions that linear models and single trees cannot represent.

---

## Key Findings

- `duration` (call length) is the most discriminatory variable but constitutes data leakage — it is unknown before the call and should be excluded in real pre-contact prediction systems.
- `poutcome = success` is the strongest categorical predictor: customers with a previously successful campaign show 3–4× higher conversion rates.
- `pdays` was removed due to 81% of values being a sentinel code (−1) and high multicollinearity with `previous`.
- Fewer contact attempts (`campaign`) are associated with higher acceptance — repeated outreach shows diminishing returns.
- Class imbalance was addressed via random oversampling of the minority class (`yes`) to a balanced 50/50 split before training.

---

## File Structure

```
.
├── Taller_Classification_Castro.ipynb   # Main notebook
├── bank-full.csv                        # Input dataset
├── modeloPipeline/                      # Saved Spark ML pipeline (generated on run)
└── output.parquet                       # Encoded feature dataset (generated on run)
```
