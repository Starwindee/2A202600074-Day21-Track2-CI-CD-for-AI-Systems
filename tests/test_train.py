import os
import json
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
from src.train import train


FEATURE_NAMES = [
    "fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
    "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide", "density",
    "pH", "sulphates", "alcohol", "wine_type",
]


def _make_temp_data(base_dir: Path):
    """
    Tao dataset nho voi cung schema Wine Quality de su dung trong test.

    pytest cung cap `tmp_path` la mot thu muc tam thoi, tu dong xoa sau khi test ket thuc.
    Ham nay dung du lieu ngau nhien nen khong can ket noi GCS hay tai file CSV thuc.
    """
    rng = np.random.default_rng(0)
    n = 200

    X = rng.random((n, len(FEATURE_NAMES)))
    y = rng.integers(0, 3, size=n)
    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["target"] = y

    base_dir.mkdir(parents=True, exist_ok=True)
    tmp_root = (base_dir / "temp").resolve()
    tmp_root.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(tmp_root)
    os.environ["TEMP"] = str(tmp_root)
    run_store = (base_dir / "mlruns").resolve().as_posix()
    os.environ["MLFLOW_TRACKING_URI"] = f"file:///{run_store}"
    train_path = str(base_dir / "train.csv")
    eval_path = str(base_dir / "eval.csv")
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)

    return train_path, eval_path


def _new_temp_dir() -> Path:
    return Path(".tmp") / "tests" / f"run-{uuid.uuid4().hex}"


def test_train_returns_float():
    """Kiem tra ham train() tra ve mot so thuc nam trong [0.0, 1.0]."""
    train_path, eval_path = _make_temp_data(_new_temp_dir())

    acc = train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert isinstance(acc, float)
    assert 0.0 <= acc <= 1.0


def test_metrics_file_created():
    """Kiem tra file outputs/metrics.json duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(_new_temp_dir())
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("outputs/metrics.json")
    with open("outputs/metrics.json") as f:
        metrics = json.load(f)
    assert "accuracy" in metrics
    assert "f1_score" in metrics


def test_model_file_created():
    """Kiem tra file models/model.pkl duoc tao sau khi huan luyen."""
    train_path, eval_path = _make_temp_data(_new_temp_dir())
    train(
        {"n_estimators": 10, "max_depth": 3},
        data_path=train_path,
        eval_path=eval_path,
    )

    assert os.path.exists("models/model.pkl")
