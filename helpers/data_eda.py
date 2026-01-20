import pandas as pd


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
