# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import connect_to_mongo, close_mongo_connection, db
from app.ml_model import load_ml_model
from app.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
	# Startup
	print("🚀 Starting up Financial Management API...")
	await connect_to_mongo()
	# Load ML model synchronously
	load_ml_model()
	# Start scheduler
	start_scheduler()
	yield
	# Shutdown
	print("🛑 Shutting down Financial Management API...")
	shutdown_scheduler()
	await close_mongo_connection()

app = FastAPI(
	title="Financial Management API",
	description="Backend for financial management app",
	version="1.0.0",
	lifespan=lifespan
)

# Include routers
from app.routers import users, transactions
from app.routers import predict as predict_router
from app.routers import loans as loans_router
from app.routers import savings as savings_router
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(predict_router.router, prefix="/api", tags=["predict"])
app.include_router(loans_router.router, prefix="/api", tags=["loans", "notifications"])
app.include_router(savings_router.router, prefix="/api", tags=["savings"])

@app.get("/")
async def root():
	return {"message": "Financial Management API is running"}

@app.get("/health")
async def health_check():
	return {"status": "healthy"}

@app.get("/test-db")
async def test_database():
	"""Test endpoint to check database connectivity"""
	try:
		if db.client is None:
			return {"status": "Database client not initialized"}
		
		# Try to ping the database
		result = await db.client.admin.command('ping')
		return {
			"status": "Database connected successfully", 
			"database_name": db.database.name if db.database is not None else "None",
			"ping_result": result
		}
	except Exception as e:
		return {"status": "Database error", "error": str(e)}

@app.get("/debug-env")
async def debug_env():
	import os
	return {
		"MONGODB_URL_present": "MONGODB_URL" in os.environ,
		"MONGODB_URL_value": os.getenv("MONGODB_URL", "NOT_SET")[:50] + "..." if os.getenv("MONGODB_URL") else "NOT_SET"
	}