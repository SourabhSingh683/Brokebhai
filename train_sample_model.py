# train_sample_model.py
import json
import pickle
from typing import List

import numpy as np
from app.simple_models import LinearSumModel


def main() -> None:
	# Define feature schema
	features: List[str] = ["income", "rent", "groceries", "utilities"]

	# Synthetic data
	n_samples = 500
	rng = np.random.default_rng(42)
	income = rng.uniform(2000, 10000, size=n_samples)
	rent = rng.uniform(500, 3000, size=n_samples)
	groceries = rng.uniform(100, 1000, size=n_samples)
	utilities = rng.uniform(50, 500, size=n_samples)
	X = np.vstack([income, rent, groceries, utilities]).T

	# True linear relation + noise
	true_weights = np.array([0.2, 1.0, 1.0, 1.0])
	true_intercept = 0.0
	y = X @ true_weights + true_intercept + rng.normal(0, 100.0, size=n_samples)

	# Fit with least squares
	X_with_bias = np.hstack([X, np.ones((X.shape[0], 1))])
	coef, *_ = np.linalg.lstsq(X_with_bias, y, rcond=None)
	weights = coef[:-1]
	intercept = coef[-1]

	model = LinearSumModel(weights, intercept)

	# Save model.pkl
	with open("model.pkl", "wb") as f:
		pickle.dump(model, f)
	print("Saved trained model -> model.pkl")

	# Save model_features.json
	with open("model_features.json", "w") as f:
		json.dump({"features": features}, f)
	print("Saved feature order -> model_features.json")

	# Sanity check
	sample = np.array([[5000.0, 1200.0, 400.0, 200.0]])
	pred = model.predict(sample)
	print({"sample_input": sample.tolist()[0], "pred": float(pred[0])})


if __name__ == "__main__":
	main() 