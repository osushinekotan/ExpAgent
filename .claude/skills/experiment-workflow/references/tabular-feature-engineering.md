# Tabular Feature Engineering

Guidelines for structuring feature engineering in `train.py` with a clear separation of stateless and stateful transforms.

## Core Pattern

Define an `engineer_features()` function that takes the raw DataFrame, config, and fitted encoders, and returns a DataFrame with all original columns plus `f_`-prefixed feature columns.

```python
def engineer_features(df: pl.DataFrame, config: Config, encoders: list) -> pl.DataFrame:
    """Raw df → f_ prefix 付き特徴量を追加した df を返す。"""
    raw_cols = [c for c in df.columns if c not in META_COLS]

    # Stateless
    X = df.select(raw_cols).to_numpy().astype(np.float64)
    # ... apply transforms (e.g., normalization, filtering) ...
    stateless_features = pl.DataFrame({f"f_{col}": X[:, i] for i, col in enumerate(raw_cols)})

    # Stateful
    encoded_parts: list[pl.DataFrame] = []
    for enc in encoders:
        encoded = enc.transform(df.select(enc.cols).to_pandas())
        encoded_parts.append(pl.DataFrame({f"f_{col}": encoded[col].values for col in encoded.columns}))

    return pl.concat([df, stateless_features, *encoded_parts], how="horizontal")
```

## Rules

- **`f_` prefix**: All engineered features (both stateless and stateful) must use the `f_` prefix. This makes it trivial to collect feature columns: `f_cols = [c for c in df.columns if c.startswith("f_")]`.
- **Don't modify the original DataFrame**: `engineer_features` adds new columns; it never overwrites or drops existing columns. The returned DataFrame contains both raw and feature columns.
- **Polars as default**: Use `polars` for DataFrame operations. Convert to pandas only at encoder boundaries (e.g., `category_encoders` requires pandas for `fit`/`transform`).
- **Stateless vs stateful separation**: Stateless transforms (normalization, filtering, mathematical transforms) are applied directly inside `engineer_features`. Stateful transforms (encoders that learn from data) are passed in as a pre-fitted `encoders` list.

## Encoder Block Pattern

Stateful encoders are managed as a list — built once, saved as a single artifact, and loaded at inference time.

```python
# train.py — build and save
def build_encoders(df: pl.DataFrame, config: Config) -> list:
    encoders = []
    if config.use_some_encoding:
        enc = SomeEncoder(cols=["col_a"])
        enc.fit(df.select("col_a").to_pandas())
        encoders.append(enc)
    return encoders

encoders = build_encoders(train_df, config)
joblib.dump(encoders, artifact_dir / "encoders.pkl")

# inference.py — load and use
encoders = joblib.load(artifact_dir / "encoders.pkl")
df = engineer_features(test_df, config, encoders)
```

### Stateful Transform Guidelines

- **Use existing libraries first**: `sklearn` transformers (`StandardScaler`, `OneHotEncoder`, etc.) and `category_encoders` (`OrdinalEncoder`, `TargetEncoder`, `OneHotEncoder`, etc.) already implement fit/transform and are serializable with `joblib`.
- **Custom transformers are fine**: When existing libraries don't cover the use case, write a custom class with `fit()` and `transform()` methods. Keep it simple — no need to inherit from `sklearn.base.BaseEstimator` unless you need pipeline integration.

### Common Pitfalls

- **Train/test category mismatch**: Test data may contain categories not seen during training (or vice versa). Libraries like `category_encoders` handle this via `handle_unknown` / `handle_missing` parameters. Custom encoders must handle this explicitly.
- **Fitting on full data**: Never fit encoders/scalers on the full dataset before CV splits if the transformation uses target-aware statistics (e.g., `TargetEncoder`). Row-wise transforms like SNV or per-spectrum normalization are safe to apply before splitting.

## Usage in train.py / inference.py

Both files share the same `engineer_features` function. The only difference is how encoders are obtained:

```python
# train.py
encoders = build_encoders(train_df, config)
df = engineer_features(train_df, config, encoders)
f_cols = sorted(c for c in df.columns if c.startswith("f_"))
X = df.select(f_cols).to_numpy().astype(np.float64)

# inference.py
encoders = joblib.load(artifact_dir / "encoders.pkl")
df = engineer_features(test_df, config, encoders)
f_cols = sorted(c for c in df.columns if c.startswith("f_"))
X = df.select(f_cols).to_numpy().astype(np.float64)
```
