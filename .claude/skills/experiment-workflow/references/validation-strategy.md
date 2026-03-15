# Validation Strategy

Guide for choosing the right cross-validation strategy based on the data characteristics.

## Gathering Information

Before deciding on a strategy, understand how the test set was constructed:

- **Standard competition**: Train/test split is known from the data description. Check group overlap, temporal ordering, and target distribution.
- **Code competition**: Test data is hidden or only partially visible. Rely on:
  - Competition description and data overview documents in backlog
  - Public notebooks and discussions on Kaggle (search for "CV strategy", "validation", "fold")
  - Ask the user — they may have insights from the forum or prior experiments
  - When uncertain, use `AskUserQuestion` to confirm the assumed split characteristics before implementing

## Decision Flow

```
1. Is it a time-series problem?
   └─ Yes → TimeSeriesSplit
   └─ No ↓

2. Are train/test split by distinct groups (e.g., categories, users, entities)?
   (i.e., groups in test never appear in train)
   └─ Yes → StratifiedGroupKFold (default over GroupKFold)
   └─ No ↓

3. Is it a multi-label classification problem?
   └─ Yes → MultilabelStratifiedKFold (from iterstrat)
   └─ No ↓

4. Is the target categorical or heavily imbalanced?
   └─ Yes → StratifiedKFold
   └─ No ↓

5. Default
   └─ KFold
```

## Strategy Details

### TimeSeriesSplit

Use when temporal ordering matters and future data should not leak into training.

```python
from sklearn.model_selection import TimeSeriesSplit

splitter = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in splitter.split(df):
    ...
```

- Sort data chronologically before splitting.
- Consider using a gap between train and validation to simulate real prediction lag.
- Variant: sliding window with fixed training size (`max_train_size` parameter).

### StratifiedGroupKFold (default for group splits)

Use when train and test are split by a group column (e.g., different categories, users, or entities appear exclusively in either train or test). Ensures no group leaks across folds.

**Always prefer `StratifiedGroupKFold` over `GroupKFold`**. `StratifiedGroupKFold` supports `shuffle` and `random_state`, making fold assignments reproducible. `GroupKFold` does not accept these parameters, so results depend on data order.

For regression targets, bin the target into quantile bins (e.g., `pd.qcut(df["target"], q=10, labels=False, duplicates="drop")`) and pass the binned values as `y` for stratification. This makes `StratifiedGroupKFold` usable in any setting.

```python
from sklearn.model_selection import StratifiedGroupKFold

splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

# Classification: use target directly
for train_idx, val_idx in splitter.split(df, df["target"], groups=df["group_col"]):
    ...

# Regression: bin target for stratification
import pandas as pd
y_binned = pd.qcut(df["target"], q=10, labels=False, duplicates="drop")
for train_idx, val_idx in splitter.split(df, y_binned, groups=df["group_col"]):
    ...
```

- Identify the group column by checking which column separates train/test without overlap.
- Fall back to `GroupKFold` only if stratification is truly impossible (e.g., single-sample groups with unique targets).

### MultilabelStratifiedKFold

Use for multi-label classification to preserve label co-occurrence distribution across folds.

```python
from iterstrat.ml_stratifiers import MultilabelStratifiedKFold

splitter = MultilabelStratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# y_multi: array-like of shape (n_samples, n_labels), binary indicator format
for train_idx, val_idx in splitter.split(X, y_multi):
    ...
```

- Requires `iterative-stratification` package (`uv add iterative-stratification`).
- Convert multi-label targets to binary indicator matrix before splitting.

### StratifiedKFold

Use when the target is categorical or has imbalanced class distribution.

```python
from sklearn.model_selection import StratifiedKFold

splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in splitter.split(df, df["target"]):
    ...
```

- For regression with skewed distributions, consider binning the target first, then stratifying on bins.

### KFold

Default choice when none of the above conditions apply.

```python
from sklearn.model_selection import KFold

splitter = KFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in splitter.split(df):
    ...
```

## Tips

- **Match CV to test split**: The CV strategy should mimic how the test set was created. If the competition splits by group, use GroupKFold; if by time, use TimeSeriesSplit.
- **Fold count**: 5 folds is a good default. Use fewer (3) for very large datasets, more (10) for small ones.
- **Reproducibility**: Always set `shuffle=True` and a fixed `random_state` (except TimeSeriesSplit, which must not shuffle).
- **Store fold assignments**: Save fold indices to ensure reproducibility across runs. Add a `fold` column to the DataFrame or save as a separate file.
