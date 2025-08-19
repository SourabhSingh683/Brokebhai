# app/routers/savings.py
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
from app.smart_saving_agent import analyze_user_savings

router = APIRouter()


@router.get("/savings_analysis/{user_id}")
async def get_savings_analysis(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365)
) -> Dict:
    """Get comprehensive savings analysis for a user"""
    try:
        analysis = await analyze_user_savings(user_id, days)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/savings_summary/{user_id}")
async def get_savings_summary(
    user_id: str,
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365)
) -> Dict:
    """Get a simplified savings summary for quick insights"""
    try:
        full_analysis = await analyze_user_savings(user_id, days)
        
        # Extract key metrics for summary
        summary = {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_spent": full_analysis.get("total_spent", 0),
            "average_daily_expense": full_analysis.get("average_daily_expense", 0),
            "max_daily_expense": full_analysis.get("max_daily_expense", 0),
            "min_daily_expense": full_analysis.get("min_daily_expense", 0),
            "ai_suggestions": full_analysis.get("ai_suggestions", "No suggestions available"),
            "analysis_date": full_analysis.get("analysis_date")
        }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}") 