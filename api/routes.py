from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.models import Job, Person
from api.schemas import JobResponse, PaginatedJobs, PersonResponse, PaginatedPeople

router = APIRouter()

@router.get("/jobs", response_model=PaginatedJobs)
async def get_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    # Total count
    count_stmt = select(func.count()).select_from(Job)
    total_count = await db.scalar(count_stmt)

    # Fetch jobs
    stmt = select(Job).order_by(Job.scraped_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return PaginatedJobs(total=total_count, jobs=jobs)

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

@router.get("/people", response_model=PaginatedPeople)
async def get_people(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    count_stmt = select(func.count()).select_from(Person)
    total_count = await db.scalar(count_stmt)

    stmt = select(Person).order_by(Person.scraped_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    people = result.scalars().all()

    return PaginatedPeople(total=total_count, people=people)

@router.get("/people/{person_id}", response_model=PersonResponse)
async def get_person(person_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Person).where(Person.id == person_id)
    result = await db.execute(stmt)
    person = result.scalar_one_or_none()

    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    return person
