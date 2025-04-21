import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.database.models import Base, User, MLModel, Transaction
from src.api.auth import get_password_hash

async def init_db():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/ml_course")
    
    engine = create_async_engine(db_url, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        query = select(User).filter(User.username == "admin")
        result = await session.execute(query)
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("adminpassword"),
                is_admin=True,
                balance=1000
            )
            session.add(admin_user)
        
        query = select(User).filter(User.username == "user")
        result = await session.execute(query)
        test_user = result.scalar_one_or_none()
        
        if not test_user:
            test_user = User(
                username="user",
                email="user@example.com",
                password_hash=get_password_hash("userpassword"),
                is_admin=False,
                balance=50
            )
            session.add(test_user)
        
        models_data = [
            {
                "name": "Text Generation (LLaMA)",
                "description": "Generate text using LLaMA model",
                "version": "1.0",
                "creation_date": datetime.now(),
                "is_active": True,
                "model_type": "text_generation",
                "parameters": {"model_size": "7b"}
            },
            {
                "name": "Spam Detector",
                "description": "Detect spam in text messages",
                "version": "1.0",
                "creation_date": datetime.now(),
                "is_active": True,
                "model_type": "classification",
                "parameters": {"threshold": 0.5}
            },
            {
                "name": "Image Captioner (ViT)",
                "description": "Generate captions for images using ViT",
                "version": "1.0",
                "creation_date": datetime.now(),
                "is_active": True,
                "model_type": "image_captioning",
                "parameters": {"beam_size": 4}
            }
        ]
        
        for model_data in models_data:
            query = select(MLModel).filter(MLModel.name == model_data["name"])
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            
            if not model:
                model = MLModel(**model_data)
                session.add(model)
        
        await session.commit()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db()) 