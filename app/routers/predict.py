# app/routers/predict.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from app.ml_model import get_loaded_model, get_feature_order
from app.models import PredictRequest, PredictBatchRequest, PredictResponse

router = APIRouter()


def _row_from_features(feature_mapping: Dict[str, float], feature_order: Optional[List[str]]) -> List[float]:
	if feature_order:
		return [float(feature_mapping.get(name, 0.0)) for name in feature_order]
	# If no explicit feature order, use sorted keys for deterministic behavior
	return [float(value) for _, value in sorted(feature_mapping.items(), key=lambda kv: kv[0])]


@router.post("/predict_spending", response_model=PredictResponse)
async def predict_spending(payload: PredictRequest) -> Any:
	model = get_loaded_model()
	if model is None:
		raise HTTPException(status_code=500, detail="Model not loaded")

	feature_order = get_feature_order()
	row = _row_from_features(payload.features, feature_order)

	try:
		pred = model.predict([row])
		# Convert numpy types to native floats if needed
		pred_floats = [float(x) for x in (pred.tolist() if hasattr(pred, "tolist") else pred)]
		return PredictResponse(predictions=pred_floats, used_feature_order=feature_order)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


@router.post("/predict_spending_batch", response_model=PredictResponse)
async def predict_spending_batch(payload: PredictBatchRequest) -> Any:
	model = get_loaded_model()
	if model is None:
		raise HTTPException(status_code=500, detail="Model not loaded")

	feature_order = get_feature_order()
	matrix = [_row_from_features(item, feature_order) for item in payload.batch]

	try:
		pred = model.predict(matrix)
		pred_floats = [float(x) for x in (pred.tolist() if hasattr(pred, "tolist") else pred)]
		return PredictResponse(predictions=pred_floats, used_feature_order=feature_order)
	except Exception as exc:
		raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") 