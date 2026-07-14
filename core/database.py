from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
import logging

from core.config import DATABASE_URL
from core.models import Base, Job, Person

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

async def save_person(person_data: dict):
    async with AsyncSessionLocal() as session:
        stmt = insert(Person).values(**person_data)
        
        # Upsert: ON CONFLICT ON profile_link DO UPDATE
        stmt = stmt.on_conflict_do_update(
            index_elements=['profile_link'],
            set_={
                'name': stmt.excluded.name,
                'headline': stmt.excluded.headline,
                'location': stmt.excluded.location,
                'snippet': stmt.excluded.snippet,
                'scraped_at': stmt.excluded.scraped_at
            }
        )
        
        try:
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Saved/Updated person: {person_data['name']}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving person {person_data['profile_link']}: {e}")
