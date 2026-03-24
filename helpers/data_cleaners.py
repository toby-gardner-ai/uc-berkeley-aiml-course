import pandas as pd
import numpy as np

def snake_cols(df) -> pd.DataFrame:
    df = df.copy()

    # Normalize column names
    df.columns = (
        df.columns
        # Remove special characters
        .str.replace(r"[^\w\s-]", "", regex=True)
        # Convert camelCase to snake_case
        .str.replace(r"([a-z0-9])([A-Z])", r"\1_\2", regex=True)
        # Convert PascalCase to snake_case
        .str.replace(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", regex=True)
        # General
        .str.replace(r"[\n\s]+", "_", regex=True)
        # Consistency
        .str.lower()
    )

    return df

def convert_dtypes(df, int_list=None, dt_list=None, cat_list=None) -> pd.DataFrame:
    df = df.copy()

    for col in int_list or []:
        df[col] = df[col].str.replace(',', '').astype(int)

    for col in dt_list or []:
        df[col] = pd.to_datetime(df[col], dayfirst=True)

    for col in cat_list or []:
        df[col] = df[col].astype('category')

    return df