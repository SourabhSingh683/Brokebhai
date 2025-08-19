# app/routers/loans.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from datetime import datetime
from app.database import db
from app.models import LoanModel, LoanCreate, LoanRepayRequest, NotificationModel
from app.scheduler import check_overdue_loans

router = APIRouter()


async def create_notification(user_id: str, loan_id: str, type_: str, message: str) -> None:
	if db.client is None or db.database is None:
		return
	await db.database.notifications.insert_one({
		"user_id": user_id,
		"loan_id": loan_id,
		"type": type_,
		"message": message,
		"created_at": datetime.utcnow(),
		"read": False,
	})


@router.post("/create_loan", response_model=LoanModel, status_code=201)
async def create_loan(payload: LoanCreate, background_tasks: BackgroundTasks):
	if db.client is None or db.database is None:
		raise HTTPException(status_code=500, detail="Database connection not available")
	try:
		loan_doc = payload.model_dump()
		loan_doc["status"] = "pending"
		loan_doc["created_at"] = datetime.utcnow()
		result = await db.database.loans.insert_one(loan_doc)
		created = await db.database.loans.find_one({"_id": result.inserted_id})

		# Notify borrower and lender
		background_tasks.add_task(
			create_notification,
			user_id=payload.borrower_id,
			loan_id=str(result.inserted_id),
			type_="loan_created",
			message=f"You received a loan of {payload.amount} due on {payload.due_date.isoformat()}"
		)
		background_tasks.add_task(
			create_notification,
			user_id=payload.lender_id,
			loan_id=str(result.inserted_id),
			type_="loan_created",
			message=f"You lent {payload.amount} to {payload.borrower_id} due on {payload.due_date.isoformat()}"
		)
		return LoanModel(**created)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error creating loan: {str(e)}")


@router.post("/repay_loan", response_model=LoanModel)
async def repay_loan(payload: LoanRepayRequest, background_tasks: BackgroundTasks):
	if db.client is None or db.database is None:
		raise HTTPException(status_code=500, detail="Database connection not available")
	try:
		from bson import ObjectId
		loan = await db.database.loans.find_one({"_id": ObjectId(payload.loan_id)})
		if not loan:
			raise HTTPException(status_code=404, detail="Loan not found")
		if loan.get("status") == "repaid":
			raise HTTPException(status_code=400, detail="Loan already repaid")

		await db.database.loans.update_one(
			{"_id": loan["_id"]},
			{"$set": {"status": "repaid", "repaid_at": datetime.utcnow()}}
		)
		updated = await db.database.loans.find_one({"_id": loan["_id"]})

		# Notify lender that borrower repaid
		background_tasks.add_task(
			create_notification,
			user_id=updated["lender_id"],
			loan_id=str(updated["_id"]),
			type_="loan_repaid",
			message=f"Loan from {updated['lender_id']} to {updated['borrower_id']} has been repaid"
		)
		return LoanModel(**updated)
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Error repaying loan: {str(e)}")


@router.get("/loans/user/{user_id}", response_model=List[LoanModel])
async def list_user_loans(user_id: str):
	if db.client is None or db.database is None:
		raise HTTPException(status_code=500, detail="Database connection not available")
	loans = await db.database.loans.find({
		"$or": [
			{"lender_id": user_id},
			{"borrower_id": user_id}
		]
	}).to_list(200)
	return [LoanModel(**doc) for doc in loans]


@router.get("/notifications/{user_id}", response_model=List[NotificationModel])
async def get_notifications(user_id: str):
	if db.client is None or db.database is None:
		raise HTTPException(status_code=500, detail="Database connection not available")
	notifs = await db.database.notifications.find({"user_id": user_id}).sort("created_at", -1).to_list(200)
	return [NotificationModel(**doc) for doc in notifs]


@router.post("/loans/check_overdue")
async def trigger_check_overdue():
	if db.client is None or db.database is None:
		raise HTTPException(status_code=500, detail="Database connection not available")
	await check_overdue_loans()
	return {"status": "ok"} 