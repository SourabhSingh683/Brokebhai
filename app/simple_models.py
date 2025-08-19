# app/simple_models.py
from typing import List, Sequence
import numpy as np


class LinearSumModel:
	"""Minimal linear regression-like model for inference only.
	Stores weights and intercept and implements .predict(X) -> List[float].
	"""

	def __init__(self, weights: Sequence[float], intercept: float = 0.0):
		self.weights = np.asarray(list(weights), dtype=float)
		self.intercept = float(intercept)

	def predict(self, X):
		X_arr = np.asarray(X, dtype=float)
		return (X_arr @ self.weights + self.intercept).tolist() 