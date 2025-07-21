from typing import List, Dict
import pandas as pd

DEFAULT_COLUMNS = ["url", "title", "caption", "posted_at"]


def build_dataframe(data: List[Dict], columns: List[str]) -> pd.DataFrame:
    """Build pandas DataFrame with default and optional columns."""
    cols = DEFAULT_COLUMNS + [col for col in columns if col not in DEFAULT_COLUMNS]
    df = pd.DataFrame(data)
    for col in cols:
        if col not in df:
            df[col] = None
    return df[cols]
