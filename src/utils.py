"""
utils.py — Helper functions for the emergency healthcare access project.
"""

import os
import pandas as pd
from pathlib import Path


def ensure_dirs(*paths: str) -> None:
    """Create directories if they do not exist."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and replace spaces with underscores."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[\s\-/]+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


def log_summary(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """Print a short summary of a DataFrame."""
    print(f"\n{'='*50}")
    print(f"  Summary: {name}")
    print(f"{'='*50}")
    print(f"  Shape   : {df.shape}")
    print(f"  Columns : {list(df.columns)}")
    print(f"  Nulls   :\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    print(f"{'='*50}\n")


def save_csv(df: pd.DataFrame, path: str) -> None:
    """Save a DataFrame as CSV, creating parent directories if needed."""
    ensure_dirs(os.path.dirname(path))
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  [Saved] {path}")