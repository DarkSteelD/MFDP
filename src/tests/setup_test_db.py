import asyncio
import asyncpg

async def setup_test_db():
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432",
        database="postgres"
    )
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1",
        "ml_course_test"
    )
    
    if exists:
        await conn.execute("DROP DATABASE ml_course_test")
    await conn.execute("CREATE DATABASE ml_course_test")
    await conn.close()
    
    print("Test database setup completed successfully.")

if __name__ == "__main__":
    asyncio.run(setup_test_db()) 