# app/smart_saving_agent.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import google.generativeai as genai
from app.database import db

# ========== STEP 0: CONFIG ==========
# Replace with your Gemini API key
GEMINI_API_KEY = "AIzaSyAReMrpusIqsCvPuG6Pv0pKvXw4vjsyjno"
genai.configure(api_key=GEMINI_API_KEY)


# ========== STEP 1: DATA INPUT FROM MONGODB ==========
async def get_user_transactions(user_id: str, days: int = 30) -> pd.DataFrame:
    """Fetch user transactions from MongoDB and convert to DataFrame"""
    if db.client is None or db.database is None:
        raise ValueError("Database connection not available")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Fetch transactions from MongoDB
    cursor = db.database.transactions.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date},
        "transaction_type": "expense"  # Focus on expenses for savings analysis
    }).sort("date", 1)
    
    transactions = await cursor.to_list(None)
    
    if not transactions:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["date", "expense", "category", "description"])
    
    # Convert to DataFrame
    data = []
    for tx in transactions:
        data.append({
            "date": tx["date"],
            "expense": tx["amount"],
            "category": tx.get("category", "unknown"),
            "description": tx.get("description", "")
        })
    
    df = pd.DataFrame(data)
    
    # Group by date and sum expenses
    df["date"] = pd.to_datetime(df["date"])
    daily_expenses = df.groupby(df["date"].dt.date)["expense"].sum().reset_index()
    daily_expenses["date"] = pd.to_datetime(daily_expenses["date"])
    
    return daily_expenses


def generate_sample_expenses(days=30):
    """Generate sample daily expenses for testing when no real data exists"""
    np.random.seed(42)
    today = datetime.today()
    data = []
    for i in range(days):
        date = today - timedelta(days=days-i)
        expense = np.random.randint(200, 800)  # daily expense
        data.append({"date": date, "expense": expense})
    return pd.DataFrame(data)


# ========== STEP 2: EWMA Calculation ==========
def compute_ewma(expenses: pd.DataFrame, span: int = 7) -> pd.DataFrame:
    """Apply EWMA smoothing to expense data"""
    expenses = expenses.copy()
    expenses['ewma'] = expenses['expense'].ewm(span=span, adjust=False).mean()
    return expenses


# ========== STEP 3: Prophet-style Heuristic Forecast ==========
def forecast_expenses(expenses: pd.DataFrame, future_days: int = 7) -> pd.DataFrame:
    """Simple linear trend + seasonality (prophet-like heuristic)"""
    if len(expenses) < 2:
        # Not enough data for forecasting
        return pd.DataFrame(columns=["date", "forecast_expense"])
    
    expenses = expenses.copy()
    expenses['day'] = np.arange(len(expenses))

    # Fit linear trend
    coef = np.polyfit(expenses['day'], expenses['expense'], 1)
    trend = np.poly1d(coef)

    # Forecast future
    last_day = expenses['day'].iloc[-1]
    future_days_idx = np.arange(last_day+1, last_day+1+future_days)
    forecast = trend(future_days_idx)

    future_dates = [expenses['date'].iloc[-1] + timedelta(days=i+1) for i in range(future_days)]
    forecast_df = pd.DataFrame({"date": future_dates, "forecast_expense": forecast})
    return forecast_df


def get_fallback_suggestions(expenses: pd.DataFrame, forecast_df: pd.DataFrame, user_id: str) -> str:
    """Generate fallback suggestions when Gemini API is unavailable"""
    if len(expenses) == 0:
        return "No expense data available for analysis."
    
    avg_daily = expenses['expense'].mean()
    max_daily = expenses['expense'].max()
    min_daily = expenses['expense'].min()
    total_spent = expenses['expense'].sum()
    
    suggestions = f"""
**Smart Savings Analysis for {user_id}**

**📊 Spending Summary:**
- Average daily expense: ${avg_daily:.2f}
- Highest daily expense: ${max_daily:.2f}
- Lowest daily expense: ${min_daily:.2f}
- Total spent in period: ${total_spent:.2f}

**💡 Personalized Recommendations:**

1. **Budget Setting**: Based on your average daily spending of ${avg_daily:.2f}, consider setting a daily budget of ${avg_daily * 0.8:.2f} to save 20%.

2. **Spending Pattern**: Your spending varies between ${min_daily:.2f} and ${max_daily:.2f} daily. Look for patterns in your higher spending days.

3. **Savings Goal**: If you reduce daily spending by 15%, you could save ${avg_daily * 0.15 * 30:.2f} per month.

4. **Action Items:**
   - Track your highest spending days
   - Set up automatic savings transfers
   - Review recurring subscriptions
   - Use cash for discretionary spending

5. **Forecast Alert**: Based on current trends, you're projected to spend ${forecast_df['forecast_expense'].mean():.2f} daily in the next week.

*Note: This is an automated analysis. For personalized financial advice, consult a financial advisor.*
"""
    return suggestions


# ========== STEP 4: AI Suggestions via Gemini ==========
def get_gemini_suggestions(expenses: pd.DataFrame, forecast_df: pd.DataFrame, user_id: str) -> str:
    """Ask Gemini for personalized saving suggestions based on user data"""
    
    # Prepare data summary for AI
    if len(expenses) > 0:
        recent_expenses = expenses.tail(10).to_string(index=False)
        avg_daily = expenses['expense'].mean()
        max_daily = expenses['expense'].max()
        min_daily = expenses['expense'].min()
        total_spent = expenses['expense'].sum()
    else:
        recent_expenses = "No recent expense data available"
        avg_daily = max_daily = min_daily = total_spent = 0
    
    if len(forecast_df) > 0:
        forecast_summary = forecast_df.to_string(index=False)
        avg_forecast = forecast_df['forecast_expense'].mean()
    else:
        forecast_summary = "No forecast data available"
        avg_forecast = 0
    
    prompt = f"""
    You are a smart savings assistant analyzing financial data for user {user_id}.
    
    User's recent expense data (last 10 days, smoothed with EWMA): 
    {recent_expenses}
    
    Spending Statistics:
    - Average daily expense: ${avg_daily:.2f}
    - Maximum daily expense: ${max_daily:.2f}
    - Minimum daily expense: ${min_daily:.2f}
    - Total spent in period: ${total_spent:.2f}
    
    Forecast for next 7 days:
    {forecast_summary}
    - Average forecasted daily expense: ${avg_forecast:.2f}
    
    Based on this analysis, provide:
    1. **Spending Pattern Analysis**: What patterns do you observe in their spending?
    2. **Overspending Alerts**: Are there any concerning trends or spikes?
    3. **Personalized Savings Tips**: 3-5 specific, actionable tips to reduce expenses
    4. **Budget Recommendations**: Suggest a realistic daily/weekly budget
    5. **Category Insights**: If category data is available, suggest areas to cut back
    
    Keep the response concise, practical, and encouraging. Focus on actionable advice.
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Fallback to rule-based suggestions when API fails
        return get_fallback_suggestions(expenses, forecast_df, user_id)


# ========== STEP 5: Main Analysis Function ==========
async def analyze_user_savings(user_id: str, days: int = 30) -> Dict:
    """Complete savings analysis for a user"""
    try:
        # Get user data from MongoDB
        expenses = await get_user_transactions(user_id, days)
        
        # If no real data, use sample data for demonstration
        if len(expenses) == 0:
            expenses = generate_sample_expenses(days)
            expenses["date"] = pd.to_datetime(expenses["date"])
        
        # Apply EWMA smoothing
        expenses = compute_ewma(expenses)
        
        # Generate forecast
        forecast_df = forecast_expenses(expenses)
        
        # Get AI suggestions
        suggestions = get_gemini_suggestions(expenses, forecast_df, user_id)
        
        # Prepare response
        analysis = {
            "user_id": user_id,
            "analysis_period_days": days,
            "total_transactions": len(expenses),
            "total_spent": float(expenses['expense'].sum()) if len(expenses) > 0 else 0,
            "average_daily_expense": float(expenses['expense'].mean()) if len(expenses) > 0 else 0,
            "max_daily_expense": float(expenses['expense'].max()) if len(expenses) > 0 else 0,
            "min_daily_expense": float(expenses['expense'].min()) if len(expenses) > 0 else 0,
            "recent_expenses": expenses.tail(10).to_dict('records') if len(expenses) > 0 else [],
            "forecast": forecast_df.to_dict('records') if len(forecast_df) > 0 else [],
            "ai_suggestions": suggestions,
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        return {
            "user_id": user_id,
            "error": f"Analysis failed: {str(e)}",
            "analysis_date": datetime.utcnow().isoformat()
        } 