import pandas as pd
import numpy as np

def summary_stats(df) -> pd.DataFrame:

    # Create base frame
    stats = pd.DataFrame(index=df.columns)

    stats["dtype"] = df.dtypes


    stats["sample_val"] = [df[col].dropna().sample(1).iloc[0]
                            if df[col].notna().any() else np.nan
                            for col in df.columns]

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

    return stats


def snake_cols(df) -> pd.DataFrame:
    df = df.copy()

    # Normalize column names
    df.columns = (df.columns
                  # Remove special characters
                  .str.replace(r'[^\w\s-]', '', regex=True)
                  # Convert camelCase to snake_case
                  .str.replace(r'([a-z0-9])([A-Z])', r'\1_\2', regex=True)
                  # Convert PascalCase to snake_case
                  .str.replace(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', regex=True)
                  # General
                  .str.replace(r'[\n\s]+', '_', regex=True)
                  # Consistency
                  .str.lower())

    return df