from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
import logging

from core.config import DATABASE_URL
from core.models import Base, Job

logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def save_job(job_data: dict):
    async with AsyncSessionLocal() as session:
        stmt = insert(Job).values(**job_data)
        
        # Upsert: ON CONFLICT ON job_link DO UPDATE
        stmt = stmt.on_conflict_do_update(
            index_elements=['job_link'],
            set_={
                'title': stmt.excluded.title,
                'company': stmt.excluded.company,
                'location': stmt.excluded.location,
                'date_posted': stmt.excluded.date_posted,
                'description': stmt.excluded.description,
                'scraped_at': stmt.excluded.scraped_at
            }
        )
        
        try:
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Saved/Updated job: {job_data['title']} at {job_data['company']}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving job {job_data['job_link']}: {e}")
