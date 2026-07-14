from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.models import Job
from api.schemas import JobResponse, PaginatedJobs

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
