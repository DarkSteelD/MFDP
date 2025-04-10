import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from .config import engine, AsyncSessionLocal, Base
from .models import User, Transaction, Prediction, MLModel
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

        models = [
            MLModel(
                name="Linear Regression Model",
                description="A basic linear regression model for numeric predictions",
                version="1.0.0",
                model_type="regression",
                parameters={"alpha": 0.01, "fit_intercept": True},
                metrics={"mae": 0.25, "mse": 0.1, "r2": 0.85}
            ),
            MLModel(
                name="Image Classification Model",
                description="Convolutional neural network for image classification",
                version="2.1.0",
                model_type="classification",
                parameters={"learning_rate": 0.001, "batch_size": 32, "epochs": 10},
                metrics={"accuracy": 0.92, "precision": 0.94, "recall": 0.89}
            )
        ]
        session.add_all(models)
        
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
                model_id=models[0].id,
                input_data={"feature1": 1.0, "feature2": 2.0},
                output_data={"prediction": 5.2},
                successful=True,
                created_at=datetime.now(timezone.utc),
                execution_time=45.3
            ),
            Prediction(
                user_id=user.id,
                model_id=models[1].id,
                input_data={"image_url": "https://example.com/sample.jpg"},
                output_data={"prediction": "cat", "confidence": 0.95},
                successful=True,
                created_at=datetime.now(timezone.utc),
                execution_time=156.7
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