# app/ml_model.py
import os
import json
from typing import Any, List, Optional

try:
	from joblib import load as joblib_load
except Exception:  # joblib might not be installed yet
	joblib_load = None  # type: ignore


class DummyModel:
	"""Fallback model used when no model file is present. Produces a simple heuristic.
	For regression: sum of features; for classification-like models, returns 0.
	"""

	def predict(self, X):
		if not X:
			return []
		# Simple sum heuristic
		return [float(sum(row)) for row in X]

	def __repr__(self) -> str:
		return "<DummyModel: sum-of-features>"


_model: Any = None
_feature_order: Optional[List[str]] = None
_model_path: Optional[str] = None
_features_path: Optional[str] = None


def load_ml_model() -> None:
	"""Load the ML model and optional feature order from disk.
	Respects env vars ML_MODEL_PATH and ML_FEATURES_PATH.
	"""
	global _model, _feature_order, _model_path, _features_path

	_model_path = os.getenv("ML_MODEL_PATH", "model.pkl")
	_features_path = os.getenv("ML_FEATURES_PATH", os.path.splitext(_model_path)[0] + "_features.json")

	# Load model
	if _model_path and os.path.exists(_model_path) and joblib_load is not None:
		try:
			_model = joblib_load(_model_path)
			print(f"✅ Loaded ML model from {_model_path}")
		except Exception as exc:
			print(f"❌ Failed to load ML model at {_model_path}: {exc}")
			_model = DummyModel()
	else:
		if joblib_load is None:
			print("⚠️ joblib not available; using DummyModel. Install joblib to load pickled models.")
		else:
			print(f"⚠️ Model file not found at {_model_path}; using DummyModel fallback.")
		_model = DummyModel()

	# Load feature order if provided
	_feature_order = None
	if _features_path and os.path.exists(_features_path):
		try:
			with open(_features_path, "r") as f:
				data = json.load(f)
				if isinstance(data, dict) and "features" in data and isinstance(data["features"], list):
					_feature_order = [str(x) for x in data["features"]]
				elif isinstance(data, list):
					_feature_order = [str(x) for x in data]
				print(f"✅ Loaded feature order from {_features_path}: {_feature_order}")
		except Exception as exc:
			print(f"⚠️ Failed to load features list at {_features_path}: {exc}")


def get_loaded_model() -> Any:
	return _model


def get_feature_order() -> Optional[List[str]]:
	return _feature_order 