# app/scheduler.py
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import db

scheduler: Optional[AsyncIOScheduler] = None


async def check_overdue_loans() -> None:
	if db.client is None or db.database is None:
		return
	now = datetime.utcnow()
	# Find loans with due_date < now and status not repaid/overdue
	cursor = db.database.loans.find({
		"due_date": {"$lt": now},
		"status": {"$nin": ["repaid", "overdue"]},
	})
	async for loan in cursor:
		# Mark overdue
		await db.database.loans.update_one({"_id": loan["_id"]}, {"$set": {"status": "overdue"}})
		# Notify borrower
		await db.database.notifications.insert_one({
			"user_id": loan["borrower_id"],
			"loan_id": str(loan["_id"]),
			"type": "loan_overdue",
			"message": f"Loan of {loan['amount']} is overdue. Due date was {loan['due_date'].isoformat()}.",
			"created_at": datetime.utcnow(),
			"read": False,
		})


def start_scheduler() -> None:
	global scheduler
	scheduler = AsyncIOScheduler()
	# Run nightly at midnight UTC
	scheduler.add_job(check_overdue_loans, CronTrigger(hour=0, minute=0))
	scheduler.start()
	print("🕒 APScheduler started: nightly overdue loan checks enabled")


def shutdown_scheduler() -> None:
	global scheduler
	if scheduler:
		scheduler.shutdown(wait=False)
		print("🕒 APScheduler shutdown complete") 