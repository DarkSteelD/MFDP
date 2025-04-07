import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from .config import engine, AsyncSessionLocal, Base
from .models import User, Transaction, Prediction
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

async def create_demo_data():
    logger.info("Creating demo data...")
    async with AsyncSessionLocal() as session:
        admin = await session.get(User, 1)
        if admin:
            logger.info("Demo data already exists. Skipping...")
            return

        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash="hashed_admin_password",
            is_admin=True,
            balance=1000
        )
        session.add(admin)
        user = User(
            username="demo_user",
            email="user@example.com",
            password_hash="hashed_user_password",
            is_admin=False,
            balance=100
        )
        session.add(user)
        await session.flush()

        transactions = [
            Transaction(
                user_id=user.id,
                change=50,
                valid=True,
                time=datetime.now(timezone.utc)
            ),
            Transaction(
                user_id=user.id,
                change=-20,
                valid=True,
                time=datetime.now(timezone.utc)
            )
        ]
        session.add_all(transactions)

        predictions = [
            Prediction(
                user_id=user.id,
                input_data={"feature1": 1.0, "feature2": 2.0},
                output_data={"prediction": "class_A"},
                successful=True,
                created_at=datetime.now(timezone.utc)
            ),
            Prediction(
                user_id=user.id,
                input_data={"feature1": 3.0, "feature2": 4.0},
                output_data={"prediction": "class_B"},
                successful=True,
                created_at=datetime.now(timezone.utc)
            )
        ]
        session.add_all(predictions)

        await session.commit()
        logger.info("Demo data created successfully.")

async def main():
    try:
        logger.info("Initializing database...")
        await init_db()
        await create_demo_data()
        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 