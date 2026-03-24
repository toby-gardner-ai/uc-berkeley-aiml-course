import pandas as pd
import numpy as np

def initial_eda(df) -> pd.DataFrame:

    # Create base frame
    stats = pd.DataFrame(index=df.columns)

    stats["dtype"] = df.dtypes

    stats["sample_val"] = [df[col].dropna().unique()[:3].tolist() for col in df.columns]

    stats["vals"] = df.count()
    stats["unique"] = df.nunique()
    stats["missing"] = (df.isna().sum())
    stats["miss_pct"] = (df.isna().sum() / len(df) * 100).round(1)

    return stats

def summary_stats(df, dtype_sort=False) -> pd.DataFrame:

    # Create base frame
    stats = pd.DataFrame(index=df.columns)

    stats["dtype"] = df.dtypes

    stats["sample_val"] = [df[col].dropna().unique()[:3].tolist() for col in df.columns]

    stats["vals"] = df.count()
    stats["miss_pct"] = (df.isna().sum() / len(df) * 100).round(1)
    stats["unique"] = df.nunique()

    # Initiate Descriptive Stats
    for col in ["mean", "mode", "min", "max", "std", "skew", "kurtosis"]:
        stats[col] = np.nan

    # Compute stats for numeric columns
    num_cols = df.select_dtypes(include="number").columns

    for col in num_cols:
        s = df[col].dropna()
        if not s.empty:
            stats.at[col, "mean"] = s.mean()
            stats.at[col, "min"] = s.min()
            stats.at[col, "max"] = s.max()
            stats.at[col, "std"] = s.std()
            stats.at[col, "skew"] = s.skew().round(1)
            stats.at[col, "kurtosis"] = s.kurtosis().round(1)
            mode_vals = s.mode()
            stats.at[col, "mode"] = mode_vals.iloc[0] if not mode_vals.empty else np.nan

    # Rounding preferences for numeric stats (change this to suit dataset)
    round_cols = ["mean", "mode", "min", "max", "std"]
    stats[round_cols] = stats[round_cols].round(2)
    if dtype_sort is True:
        stats = stats.iloc[np.lexsort([stats.index.str.lower(), stats['dtype'].astype(str)])]
        return stats
    else:
        return stats


def missing_data_stats(df) -> pd.DataFrame:

    other_missing_values = ["?", "—", "N/A", "null", ""]

    stats = {}
    
    for col in df.columns:
        counts = df[col].isin(other_missing_values).sum()
        missing_nan = df[col].isna().sum()
        stats[col] = {
            "total_rows": len(df),
            'missing_nan': missing_nan,
            'missing_other': counts, 
            "true_missing": counts + missing_nan,
            "true_missing_pct":  ((counts + missing_nan) / len(df) * 100).round(1),
            "unique": df[col].nunique()
        }
    return pd.DataFrame(stats).T

def duplicates(df) -> pd.DataFrame:
    df = df.copy()

    # Identify duplicates
    dups = df[df.duplicated(keep=False)]
    dup_count = len(dups)

    if dup_count > 0:
        duplicate_count = df.duplicated().sum()
        original_rows = dup_count - duplicate_count
        print(f"Found {duplicate_count} duplicate entries of {original_rows} original rows")
        print(f"Returning df of {dup_count} rows: containing both original rows and their duplicate entries")

    else:
        print("No duplicate records found")

    return dups

def missing_patterns(df, column) -> pd.DataFrame:
    """Test whether missing values in a column are associated with values
    in other columns using chi-squared tests of independence.

    Uses Cramer's V (effect size) and p-values to identify MNAR patterns
    without the noise of raw counts.

    Parameters
    ----------
    df : DataFrame
    column : str - the column whose NaN rows you want to investigate

    Returns
    -------
    DataFrame with one row per tested column, sorted by Cramer's V
    (highest first = strongest association with missingness).
    """
    from scipy.stats import chi2_contingency

    is_missing = df[column].isna()
    n_missing = is_missing.sum()
    n_total = len(df)

    if n_missing == 0:
        print(f"No missing values found in '{column}'.")
        return pd.DataFrame()

    print(
        f"'{column}': {n_missing} missing "
        f"({n_missing / n_total * 100:.1f}%) of {n_total:,} rows\n"
    )

    rows = []
    for col in df.columns:
        if col == column:
            continue

        # Drop rows where the candidate column is also NaN
        subset = df[[column, col]].dropna(subset=[col])
        if subset.empty:
            continue

        # Contingency table: is_missing (True/False) vs column values
        ct = pd.crosstab(subset[column].isna(), subset[col])

        # Need at least 2x2 for chi-squared
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            continue

        chi2, p_value, dof, expected = chi2_contingency(ct)

        # Cramer's V: normalized effect size [0, 1]
        n = ct.sum().sum()
        k = min(ct.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 else 0

        rows.append(
            {
                "column": col,
                "cramers_v": round(cramers_v, 3),
                "p_value": round(p_value, 4),
                "unique": df[col].nunique(),
            }
        )

    if not rows:
        print("No testable columns found.")
        return pd.DataFrame()

    results = (
        pd.DataFrame(rows)
        .set_index("column")
        .sort_values("cramers_v", ascending=False)
    )

    # Label signal strength based on p-value
    def _signal(p):
        if p < 0.01:
            return "strong"
        if p < 0.05:
            return "moderate"
        return "none"

    results["signal"] = results["p_value"].apply(_signal)

    # Print summary of significant associations only
    sig = results[results["p_value"] < 0.05]
    if not sig.empty:
        print(f"Columns associated with missing '{column}' (p < 0.05):")
        for idx, row in sig.iterrows():
            print(
                f"  '{idx}': Cramer's V = {row['cramers_v']}, "
                f"p = {row['p_value']} ({row['signal']})"
            )
        print()
    else:
        print("No significant associations found -- missingness appears random.\n")

    return results


def remove_outliers_by_zscore(df, threshold=3, columns=None) -> pd.DataFrame:

    df = df.copy()

    # Select columns to check for outliers
    if columns is None:
        # Use all numeric columns
        num_cols = df.select_dtypes(include="number").columns.tolist()
    else:
        # Use specified columns and verify they're numeric
        num_cols = []
        for col in columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found in dataframe. Skipping.")
            elif df[col].dtype not in ["int64", "float64", "int32", "float32"]:
                print(f"Warning: Column '{col}' is not numeric. Skipping.")
            else:
                num_cols.append(col)

    if not num_cols:
        print("No valid numeric columns to check for outliers.")
        return df

    print(f"Checking for outliers in columns: {num_cols}")

    # Calculate z-scores for selected numeric columns
    z_scores = (df[num_cols] - df[num_cols].mean()) / df[num_cols].std()

    # Filter rows where all z-scores are within threshold
    original_len = len(df)
    df = df[(z_scores.abs() <= threshold).all(axis=1)]

    print(
        f"Removed {original_len - len(df)} outlier rows ({((original_len - len(df)) / original_len * 100):.1f}%)"
    )

    return df
